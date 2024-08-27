import asyncio
from playwright.async_api import async_playwright
import os

async def get_headers_and_cookies():
    async with async_playwright() as p:
        # Specify the user data directory and profile directory
        user_data_dir = '/home/cognilium/.config/google-chrome'
        profile_directory = 'Default'

        # Check if the user data directory exists
        if not os.path.exists(user_data_dir):
            print(f"User data directory does not exist: {user_data_dir}")
            return {}, []

        try:
            # Launch Chrome with the specified user data directory and profile
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                channel="chrome",
                user_data_dir=user_data_dir,
                profile_directory=profile_directory
            )

            if browser.pages:
                page = browser.pages[0]
            else:
                page = await browser.new_page()

            print(f"Page URL: {page.url}")

            print("Navigating to https://www.loom.com/looms/videos")
            await page.goto('https://www.loom.com/looms/videos', wait_until='networkidle')

            print(f"Page URL after navigation: {page.url}")

            if 'login' in page.url:
                print("Redirection to login page detected. Please ensure you are logged in with the correct profile.")
                return {}, []

            headers = {}
            cookies = []

            async def handle_request(route, request):
                nonlocal headers
                nonlocal cookies
                if "https://www.loom.com/graphql" in request.url:
                    headers = request.headers
                    cookies = await page.context.cookies()
                    print(f"Intercepted API Request URL: {request.url}")
                await route.continue_()

            await page.route("https://www.loom.com/graphql", handle_request)

            print("Reloading the page to capture requests...")
            await page.reload()
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(10000)  # Wait for all requests to be captured

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            await browser.close()

        return headers, cookies

# Directly await the coroutine in Jupyter or a similar environment
headers, cookies = await get_headers_and_cookies()

print("Captured Headers:")
if headers:
    for key, value in headers.items():
        print(f"{key}: {value}")
else:
    print("No headers captured.")

print("\nCaptured Cookies:")
if cookies:
    for cookie in cookies:
        print(f"<Cookie {cookie['name']}={cookie['value']} for {cookie['domain']}/>")
else:
    print("No cookies captured.")
