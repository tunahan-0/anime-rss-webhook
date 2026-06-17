import os
import sqlite3
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from webhook import embed_gonder
from dotenv import load_dotenv

load_dotenv()

webhook_url = os.getenv("WEBHOOK_URL")
rol_id = os.getenv("ROL_ID")
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "animecix_rss.db")

def veritabani_hazirla():
    vt = sqlite3.connect(db_path)
    cursor = vt.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("CREATE TABLE IF NOT EXISTS bolumler (id INTEGER PRIMARY KEY AUTOINCREMENT, bolum TEXT UNIQUE)")
    vt.commit()
    vt.close()

def scrape():
    with sync_playwright() as p:
        tarayici = p.chromium.launch(headless=True) #headless = silent
        sayfa = tarayici.new_page()
        sayfa.goto("https://animecix.tv/")
        sayfa.wait_for_selector("episode-portrait-item")
        html = sayfa.content()
        tarayici.close()

    soup = BeautifulSoup(html, 'html.parser')
    kartlar = soup.select("episode-portrait-item")
    domain = "https://animecix.tv"

    vt = sqlite3.connect(db_path)
    cursor = vt.cursor()

    for kart in kartlar:
        ad = kart.find("a", class_="title").text.strip()
        bolum = kart.find("div", class_="subtitle").text.strip()
        resim = kart.find("img", class_="media-image-el")['src']
        href = kart.find("a", class_="title")['href']
        link = f"{domain}{href}"

        bolum_ad = f"{ad}({bolum})"
        bolum_ad_yeni = bolum_ad.lower().replace(" ", "_").replace(".","").replace(",","").replace("?","").replace("!","").replace(":","").replace(";","")

        try:
            cursor.execute("INSERT INTO bolumler (bolum) VALUES (?)", (bolum_ad_yeni,))
            vt.commit()
            #hata almadiysa(bolum sutunu unique oldugu icin aynı degerde baska veri eklenemiyor) yeni bolumdur yani embed gonderilecek demektir
            print(f"Yeni bolum: {bolum_ad_yeni}")
            embed_gonder(ad, bolum, link, resim,  webhook_url, rol_id)
        except sqlite3.IntegrityError:
            print(f"Zaten mevcut: {bolum_ad_yeni}")
    vt.close()

if __name__ == "__main__":
    try:
        veritabani_hazirla()
        scrape()
    except Exception as e:
        print(f"Hata:{e}")