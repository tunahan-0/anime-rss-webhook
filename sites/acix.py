import os
import asyncio
import libsql_client
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from webhook import embed_gonder
from dotenv import load_dotenv

load_dotenv()
# webhook adres
acix_webhook_url = os.getenv("ACIX_WEBHOOK_URL")
# ortak bilgiler
rol_id = os.getenv("ROL_ID")
vt_url = os.getenv("TURSO_DATABASE_URL")
vt_token = os.getenv("TURSO_TOKEN")

async def acix_veritabani_hazirla():
    async with libsql_client.create_client(url=vt_url, auth_token=vt_token) as acix_vt:
        acix_sql = "CREATE TABLE IF NOT EXISTS acix_bolumler (id INTEGER PRIMARY KEY AUTOINCREMENT, bolum TEXT UNIQUE)"
        await acix_vt.execute(acix_sql)
        print("[ACIX] Veritabanı hazır")
    
async def animecix(browser):
    acix_proxy_server = os.getenv("PROXY_SERVER")
    acix_proxy_user = os.getenv("PROXY_USER")
    acix_proxy_pass = os.getenv("PROXY_PASS")

    acix_proxy_config = None
    if acix_proxy_server:
        acix_proxy_config={
            "server": acix_proxy_server,
            "username": acix_proxy_user,
            "password": acix_proxy_pass
        }
    
    acix_context = await browser.new_context(proxy=acix_proxy_config)
    acix_sayfa = await acix_context.new_page()

    acix_html = None

    try:    
        await acix_sayfa.goto("https://animecix.tv/", wait_until='domcontentloaded', timeout=60000)
        print("[ACIX] Sayfa içeriği:", (await acix_sayfa.content())[:500]) # debug amaclı sayfanın iceriginin bir kısmı 
        try:
            await acix_sayfa.wait_for_selector("episode-portrait-item")
            acix_html = await acix_sayfa.content()
        except Exception as e:
            print(f"[ACIX] HATA: Element bulunamadı veya zaman aşımına uğradı ({e})")
            return
    finally:
        await acix_context.close()

    if acix_html:
        acix_soup = BeautifulSoup(acix_html, 'html.parser')
        acix_kartlar = acix_soup.select("episode-portrait-item")
        acix_domain = "https://animecix.tv"

        if acix_kartlar and acix_domain:
            async with libsql_client.create_client(url=vt_url, auth_token=vt_token) as vt:
                for acix_kart in acix_kartlar:
                    acix_ad_t = acix_kart.find("a", class_="title")
                    acix_bolum_t = acix_kart.find("div", class_="subtitle")
                    acix_resim_t = acix_kart.find("img", class_="media-image-el")
                    
                    if not (acix_ad_t and acix_bolum_t and acix_resim_t): continue
                    acix_ad = acix_ad_t.text.strip()
                    acix_bolum = acix_bolum_t.text.strip()
                    acix_resim = acix_resim_t.get('src') or acix_resim_t.get('data-src', '')
                    if acix_resim and not acix_resim.startswith("http"):
                        acix_resim = f"{acix_domain}{acix_resim}"
                    acix_link_path = acix_ad_t.get('href', '')
                    acix_link = f"{acix_domain}{acix_link_path}" if not acix_link_path.startswith("http") else acix_link_path

                    acix_bolum_ad = f"{acix_ad}({acix_bolum})"
                    acix_bolum_ad_yeni = (
                        acix_bolum_ad.lower()
                        .replace(" ", "_")
                        .replace(".","")
                        .replace(",","")
                        .replace("?","")
                        .replace("!","")
                        .replace(":","")
                        .replace(";","")
                    )
                    try:
                        await vt.execute("INSERT INTO acix_bolumler (bolum) VALUES (?)", (acix_bolum_ad_yeni,))
                        #hata almadiysa yeni bolum yani webhook gonderilecek demektir. 
                        print(f"[ACIX] Yeni bolum: {acix_bolum_ad_yeni}")
                        embed_gonder(acix_ad, acix_bolum, acix_link, acix_resim, acix_webhook_url, rol_id)
                    except Exception as acix_e:
                        print(f"[ACIX] Zaten mevcut veya VT hatasi ({acix_bolum_ad_yeni}): {acix_e}")
        else:
            print("[ACIX] HATA: HTML çekildi fakat 'episode-portrait-item' kartları bulunamadı.")
    else:
        print("[ACIX] HATA: Sayfa HTML içeriği alınamadığı için işlem iptal edildi.")
