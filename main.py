import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
# siteler
from sites.acix import *
from sites.openani import *

load_dotenv()

async def main():
    await acix_veritabani_hazirla()
    await open_veritabani_hazirla()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            await asyncio.gather(
                animecix(browser),
                openanime(browser)
            )
        finally:
            await browser.close()
if __name__ == "__main__":
    asyncio.run(main())