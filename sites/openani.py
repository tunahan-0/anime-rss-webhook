import os
import libsql_client
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from webhook import embed_gonder

load_dotenv()
# webhook adres
open_webhook_url = os.getenv("OPEN_WEBHOOK_URL")
# ortak bilgiler
rol_id = os.getenv("ROL_ID")
vt_url = os.getenv("TURSO_DATABASE_URL")
vt_token = os.getenv("TURSO_TOKEN")

opendomain = "https://openani.me"
openhedeflink = "https://openani.me/episodes/populars/1"
# (kart-link-gorsel)
open_kaligo_class = "anime-card"
open_adbolumclass = "anime-name"

open_SUFFIX_RE = re.compile(
    r"\s+(?:(?P<season>\d+)\.\s*Sezon\s+)?(?P<episode>\d+(?:\.\d+)?)\.\s*Bölüm\s*$",
    re.IGNORECASE,)

open_HREF_RE = re.compile(r"/anime/(?P<slug>[^/]+)/(?P<season>\d+)/(?P<episode>\d+(?:\.\d+)?)")

async def open_veritabani_hazirla():
    async with libsql_client.create_client(url=vt_url, auth_token=vt_token) as open_vt:
        sql = "CREATE TABLE IF NOT EXISTS open_bolumler (id INTEGER PRIMARY KEY AUTOINCREMENT, bolum TEXT UNIQUE)"
        await open_vt.execute(sql)
        print("[OpenAnime] Veritabanı hazır")

async def openanime(browser):
    open_proxy_server = os.getenv("PROXY_SERVER")
    open_proxy_user = os.getenv("PROXY_USER")
    open_proxy_pass = os.getenv("PROXY_PASS")

    open_proxy_config = None
    if open_proxy_server:
        open_proxy_config={
            "server": open_proxy_server,
            "username": open_proxy_user,
            "password": open_proxy_pass
            }

    open_context = await browser.new_context(proxy=open_proxy_config)
    open_sayfa = await open_context.new_page()
    await open_sayfa.route(
        "**/*",
        lambda r: r.abort() if r.request.resource_type in ("image", "font", "media") else r.continue_(),
    )
    try:
        await open_sayfa.goto(f"{openhedeflink}", wait_until='domcontentloaded', timeout=60000)
        await open_sayfa.wait_for_timeout(2000)

        try:
            # ekrana cıkan kutuyu kapatmak icin bos yere tıkla
            await open_sayfa.mouse.click(50, 50)
        except Exception as e:
            print(f"[OpenAnime] Boş alana tıklama sırasında hata: {e}")

        await open_sayfa.wait_for_timeout(1000)
            
        try:
            open_animekart = open_sayfa.locator(f"a.{open_kaligo_class}").first
            await open_animekart.wait_for(state="visible", timeout=50000)
        except Exception as e:
            print(f"[OpenAnime] HATA: Playwright elementi bulamadı veya zaman aşımına uğradı -> {e}")
            return
        open_html = await open_sayfa.content()
    finally:    
        await open_context.close()
    try:
        open_soup = BeautifulSoup(open_html, 'html.parser')
        open_kartlar = open_soup.select(f"a.{open_kaligo_class}")
    except Exception as e:
        print(f"[OpenAnime] HATA: HTML içeriği boş veya tanımlanmamış ({e})")

    async with libsql_client.create_client(url=vt_url, auth_token=vt_token) as open_vt:    
        for open_kart in open_kartlar:
            open_h5_etiketi = open_kart.select_one(f"h5.{open_adbolumclass}")
            if open_h5_etiketi is None:
                continue
                
            open_anatext = open_h5_etiketi.text.strip()
            open_ayiklanmistext = open_parse_episode(open_anatext, open_kart["href"])
            open_anime_ad = open_ayiklanmistext["Ad"]

            if open_ayiklanmistext["Sezon"] is not None:
                open_bolum_bilgisi = f"{open_ayiklanmistext['Sezon']}. Sezon {open_ayiklanmistext['Bölüm']}. Bölüm"
            else:
                open_bolum_bilgisi = f"{open_ayiklanmistext['Bölüm']}. Bölüm"
                
            open_href = open_kart['href']
            open_link = (f"{opendomain}{open_href}")
            open_style = open_kart.get("style", "")
            open_m = re.search(r"--canvas-url:\s*url\((.+?)\)", open_style)
            open_resim_url = None
                
            if open_m:
                open_canvas_url = open_m.group(1)
                open_src = parse_qs(urlparse(open_canvas_url).query).get("src")
                if open_src:
                    open_resim_url = open_src[0].replace("/w300/", "/w780/")
            open_db_bolum_ad = f"{open_anime_ad}({open_bolum_bilgisi})"
            open_db_bolum_ad_temiz = (open_db_bolum_ad.lower()
                                      .replace(" ", "_")
                                      .replace(".","")
                                      .replace(",","")
                                      .replace("?","")
                                      .replace("!","")
                                      .replace(":","")
                                      .replace(";",""))

            try:
                await open_vt.execute("INSERT INTO bolumler (bolum) VALUES (?)", (open_db_bolum_ad_temiz,))
                #hata almadiysa yeni bolum yani webhook gonderilecek demektir. 
                print(f"[OpenAnime] Yeni bolum: {open_db_bolum_ad_temiz}")
                embed_gonder(open_anime_ad, open_bolum_bilgisi, open_link, open_resim_url, open_webhook_url, rol_id)
            except Exception as e:
                print(f"[OpenAnime] Zaten mevcut veya hata: {open_db_bolum_ad_temiz}")
            
        # anime adı = open_anime_ad
        # sezon-bolum bilgisi = open_bolum_bilgisi
        # bolum linki = open_link
        # gorsel url = open_resim_url
        # database'e girecek kayıt = db_bolum_ad_temiz

def open_parse_episode(text, href):
    text = text.strip()

    open_m = open_SUFFIX_RE.search(text)
    open_adi = text[:open_m.start()].strip() if open_m else text

    open_season = open_episode = None
    open_h = open_HREF_RE.search(href)
    if open_h:
        open_season, open_episode = open_h["season"], open_h["episode"]
    elif open_m:
        open_season, open_episode = open_m["season"], open_m["episode"]

    return {
        "Ad": open_adi,
        "Sezon": int(open_season) if open_season and open_season.isdigit() else open_season,
        "Bölüm": int(open_episode) if open_episode and open_episode.isdigit() else open_episode,
    }