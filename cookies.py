from playwright.sync_api import sync_playwright
import time

def get_headers_and_cookies():
    with sync_playwright() as p:
        # Specify the user data directory for the Chrome profile you want to use
        user_data_dir = '/home/your-username/.config/google-chrome/Profile 1'  # Replace with your actual profile path

        # Launch Chrome with the specified user data directory
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # Set to True if you don't need to see the browser
            channel="chrome"  # Use "chrome" if you have Google Chrome, or "chromium" for Chromium
        )

        # Check if the browser opened with any page
        if browser.pages:
            page = browser.pages[0]
        else:
            page = browser.new_page()

        print(f"Page URL: {page.url}")  # Debugging: print the initial URL

        # Navigate to the Loom videos page (you should already be logged in with the profile)
        print("Navigating to https://www.loom.com/looms/videos")
        page.goto('https://www.loom.com/looms/videos', wait_until='networkidle')

        print(f"Page URL after navigation: {page.url}")  # Debugging: print the URL after navigation

        # Check if the user is redirected to the login page
        if 'login' in page.url:
            print("Redirection to login page detected. Please ensure you are logged in with the correct profile.")
            browser.close()
            return {}, []

        headers = {}
        cookies = []

        # Function to handle requests and intercept the desired API URL
        def handle_request(route, request):
            nonlocal headers
            nonlocal cookies
            print(f"Intercepted URL: {request.url}")  # Debugging: print all intercepted URLs
            if "https://www.loom.com/graphql" in request.url:
                headers = request.headers  # Capture the headers
                cookies = page.context.cookies()  # Capture the cookies
                print(f"Intercepted API Request URL: {request.url}")
            route.continue_()  # Continue the request without modification

        # Enable request interception
        page.route("https://www.loom.com/graphql", handle_request)

        # Reload the page to ensure request interception happens
        print("Reloading the page to capture requests...")
        page.reload()
        page.wait_for_load_state('networkidle')
        time.sleep(10)  # Allow time for all requests to be captured

        # Close the browser context
        browser.close()

        return headers, cookies

# Run the function to get headers and cookies
headers, cookies = get_headers_and_cookies()

# Print captured headers and cookies
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
