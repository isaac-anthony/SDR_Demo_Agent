import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Type of stealth: {type(stealth)}")
        # Try calling it
        try:
            stealth(page)
            print("Successfully called stealth(page) sync")
        except Exception as e:
            print(f"Failed sync: {e}")
            
        try:
            await stealth(page)
            print("Successfully called await stealth(page)")
        except Exception as e:
            print(f"Failed async: {e}")
        await browser.close()

asyncio.run(main())
