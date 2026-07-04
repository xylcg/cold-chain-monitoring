import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto('http://localhost:3000/#/login')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    page.screenshot(path='c:/Users/18356/Desktop/11111/debug_login_now.png', full_page=True)
    
    # 获取所有按钮文本
    buttons = page.locator('button').all()
    print("所有按钮:")
    for i, btn in enumerate(buttons):
        try:
            text = btn.inner_text()
            disabled = btn.is_disabled()
            print(f"  button[{i}]: text='{text}' disabled={disabled}")
        except:
            print(f"  button[{i}]: error reading")
    
    # 填入账号密码 - 通过 placeholder 找
    page.locator('input[placeholder*="账号"]').first.fill('admin')
    page.locator('input[placeholder*="密码"]').first.fill('123456')
    print("已填入账号密码")
    
    # 找到提交按钮（type=submit 的按钮）
    submit_btn = page.locator('button[type="submit"]').first
    submit_btn.click()
    print("已点击登录")
    
    page.wait_for_timeout(4000)
    page.screenshot(path='c:/Users/18356/Desktop/11111/debug_after_login_now.png', full_page=True)
    
    current_url = page.url
    print(f"当前 URL: {current_url}")
    
    browser.close()
    print("完成")
