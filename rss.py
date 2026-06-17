import os
import asyncio
import libsql_client
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from webhook import embed_gonder
from dotenv import load_dotenv

load_dotenv()

vt_url = os.getenv("TURSO_DATABASE_URL")
vt_token = os.getenv("TURSO_TOKEN")
webhook_url = os.getenv("WEBHOOK_URL")
rol_id = os.getenv("ROL_ID")

async def veritabani_hazirla():
    async with libsql_client.create_client(url=vt_url, auth_token=vt_token) as client:
        sql = "CREATE TABLE IF NOT EXISTS bolumler (id INTEGER PRIMARY KEY AUTOINCREMENT, bolum TEXT UNIQUE)"
        await client.execute(sql)
        print("Veritabanı hazır")
    
async def scrape():
    async with async_playwright() as p:
        tarayici = await p.chromium.launch(headless=True) #headless = silent
        sayfa = await tarayici.new_page()
        await sayfa.goto("https://animecix.tv/")
        content = await sayfa.content()
        print(f"Sayfa boyutu: {len(content)} karakter")
        await sayfa.wait_for_selector("episode-portrait-item")
        html = await sayfa.content()
        await tarayici.close()

    soup = BeautifulSoup(html, 'html.parser')
    kartlar = soup.select("episode-portrait-item")
    domain = "https://animecix.tv"

    async with libsql_client.create_client(url=vt_url, auth_token=vt_token) as vt:
        for kart in kartlar:
            ad_t = kart.find("a", class_="title")
            bolum_t = kart.find("div", class_="subtitle")
            resim_t = kart.find("img", class_="media-image-el")
            
            if not (ad_t and bolum_t and resim_t): continue
            ad = ad_t.text.strip()
            bolum = bolum_t.text.strip()
            resim = resim_t['src']
            link = f"{domain}{ad_t['href']}"

            bolum_ad = f"{ad}({bolum})"
            bolum_ad_yeni = bolum_ad.lower().replace(" ", "_").replace(".","").replace(",","").replace("?","").replace("!","").replace(":","").replace(";","")

            try:
                await vt.execute("INSERT INTO bolumler (bolum) VALUES (?)", (bolum_ad_yeni,))
                #hata almadiysa yeni bolum yani webhook gonderilecek demektir. 
                print(f"Yeni bolum: {bolum_ad_yeni}")
                embed_gonder(ad, bolum, link, resim, webhook_url, rol_id)
            except Exception as e:
                print(f"Zaten mevcut veya hata: {bolum_ad_yeni}")

async def main():
    await veritabani_hazirla()
    await scrape()

if __name__ == "__main__":
    asyncio.run(main())