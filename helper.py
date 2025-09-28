import asyncio
import aiofiles
import json
from playwright.async_api import async_playwright
import time
import random
import re

class AsyncHelper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def setup(self):
        """Async setup for browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        
        user_agents = [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.context = await self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=random.choice(user_agents),
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        self.page = await self.context.new_page()
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            })
        """)

    async def save_results(self):
        try:
            async with aiofiles.open("results_log.txt", "a") as f:
                await f.write(f"URL: {self.page.url}\n")
                await f.write(f"Title: {await self.page.title()}\n")
                content = await self.extract_visible_content()
                await f.write(f"Content Preview: {content[:500]}\n")
                await f.write("="*50 + "\n")
            return "Results saved to results_log.txt"
        except Exception as e:
            return f"Error saving results: {e}"

    async def human_like_delay(self, min_sec=1, max_sec=4):
        base_delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(base_delay)

    async def human_like_mouse_movement(self):
        try:
            for _ in range(3):
                x = random.randint(100, 1200)
                y = random.randint(100, 600)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(0.2)
        except:
            pass

    async def search_google_safely(self, query: str):
        try:
            print(f"🔍 Searching for: {query}")
            await self.page.goto("https://www.wikipedia.org", wait_until="networkidle")
            await self.human_like_delay(1, 2)
            await self.page.goto("https://www.google.com", wait_until="networkidle")
            await self.human_like_delay(1, 3)
            
            search_box = "textarea[name='q'], input[name='q']"
            await self.page.wait_for_selector(search_box, timeout=10000)
            await self.page.click(search_box)
            await self.human_like_delay(0.5, 1)
            
            for i, char in enumerate(query):
                await self.page.type(search_box, char, delay=random.randint(80, 200))
                if random.random() > 0.9:
                    await self.human_like_delay(0.1, 0.4)
                if i % 5 == 0:
                    await self.human_like_mouse_movement()
                    
            await self.human_like_delay(1, 2)
            await self.page.press(search_box, "Enter")
            await self.human_like_delay(1, 4)
            
            content = await self.page.content()
            content_lower = content.lower()
            if any(blocked in content_lower for blocked in ["unusual traffic", "detected unusual traffic", "captcha"]):
                print("🚫 Blocked by Google. Trying alternative approach...")
                return await self.use_alternative_search_engine(query)
            
            return await self.get_page_info()
        except Exception as e:
            return {"error": str(e)}

    async def use_alternative_search_engine(self, query: str):
        alternatives = [
            ("https://search.yahoo.com", "input[name='p']"),
            ("https://duckduckgo.com", "input[name='q']"),
            ("https://www.bing.com", "input[name='q']"),
        ]
        for url, selector in alternatives:
            try:
                await self.page.goto(url, wait_until="networkidle")
                await self.page.fill(selector, query)
                await self.page.press(selector, "Enter")
                await self.human_like_delay(2, 4)
                return await self.get_page_info()
            except:
                continue
        return {"error": "All search engines blocked"}

    async def smart_click(self, target: str):
        strategies = [
            f"a:has-text('{target}')",
            f"h3:has-text('{target}')",
            f"div:has-text('{target}')",
            f"span:has-text('{target}')",
            f"button:has-text('{target}')",
        ]
        
        for selector in strategies:
            try:
                if await self.page.locator(selector).count() > 0:
                    await self.human_like_mouse_movement()
                    await self.page.click(selector)
                    await self.human_like_delay(1, 2)
                    return await self.get_page_info()
            except:
                continue
        return "Click failed - element not found"

    async def extract_visible_content(self):
        try:
            data = await self.page.evaluate("""
                () => {
                    const tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'];
                    const result = [];

                    tags.forEach(tagName => {
                        const nodes = document.querySelectorAll(tagName);
                        nodes.forEach(node => {
                            const text = node.innerText?.trim() || '';
                            const id = node.id || null;
                            const className = node.className || null;
                            let href = null;
                            if (tagName === 'a') {
                                href = node.getAttribute('href');
                            }
                            result.push({
                                tag: tagName,
                                text: text,
                                id: id,
                                class: className,
                                href: href
                            });
                        });
                    });

                    return result;
                }
            """)
            return data
        except Exception as e:
            return f"Extraction error: {e}"

    async def get_page_info(self):
        try:
            content = await self.extract_visible_content()
            return {
                "url": self.page.url,
                "title": await self.page.title(),
                "content_preview": content[:500] if content else ""
            }
        except:
            return {"error": "Could not get page info"}

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def clear_cookies_and_cache(self):
        """Clear cookies and cache between sessions"""
        try:
            await self.context.clear_cookies()
            await self.page.evaluate("() => localStorage.clear()")
            await self.page.evaluate("() => sessionStorage.clear()")
        except:
            pass

    async def rotate_user_agent(self):
        """Rotate user agent for new sessions"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        ]
        new_agent = random.choice(user_agents)
        await self.context.set_extra_http_headers({'User-Agent': new_agent})