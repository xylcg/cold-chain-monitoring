import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    
    # Go to login page
    page.goto('http://localhost:3000/#/login')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    page.screenshot(path='debug_login.png', full_page=True)
    print("Screenshot saved: debug_login.png")
    
    # Try to find login form elements
    content = page.content()
    print("Page title:", page.title())
    
    # Look for input fields
    inputs = page.locator('input').all()
    print(f"Found {len(inputs)} input elements")
    for i, inp in enumerate(inputs):
        placeholder = inp.get_attribute('placeholder') or ''
        print(f"  input[{i}]: placeholder='{placeholder}'")
    
    # Look for buttons
    buttons = page.locator('button').all()
    print(f"Found {len(buttons)} button elements")
    for i, btn in enumerate(buttons):
        text = btn.inner_text()[:50]
        print(f"  button[{i}]: text='{text}'")
    
    # Try to login
    try:
        # Fill username
        username_input = page.locator('input[placeholder*="用户名"]').first
        if username_input.count() == 0:
            username_input = page.locator('input').nth(0)
        username_input.fill('admin')
        
        # Fill password
        password_input = page.locator('input[type="password"]').first
        if password_input.count() == 0:
            password_input = page.locator('input').nth(1)
        password_input.fill('123456')
        
        # Click login button
        login_btn = page.locator('button:has-text("登录")').first
        if login_btn.count() == 0:
            login_btn = page.locator('button').first
        login_btn.click()
        
        page.wait_for_timeout(3000)
        page.wait_for_load_state('networkidle')
        
        print(f"After login URL: {page.url}")
        page.screenshot(path='debug_after_login.png', full_page=True)
        print("After-login screenshot saved")
        
    except Exception as e:
        print(f"Error during login: {e}")
        page.screenshot(path='debug_error.png', full_page=True)
    
    browser.close()
