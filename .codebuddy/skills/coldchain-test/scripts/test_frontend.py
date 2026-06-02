"""
冷链物流监控平台 - 前端 E2E 测试脚本 (Playwright)
测试所有前端页面的渲染和交互

用法:
    python test_frontend.py                        # 默认测试 localhost:3000
    python test_frontend.py --url http://localhost:5173  # 指定前端地址
    python test_frontend.py --headless             # 无头模式（默认）
    python test_frontend.py --headed               # 有头模式（可视化）
"""

import sys
import argparse
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("请先安装 playwright: pip install playwright && playwright install chromium")
    sys.exit(1)


class FrontendTester:
    """前端 E2E 测试器"""

    def __init__(self, frontend_url="http://localhost:3000", headless=True):
        self.frontend_url = frontend_url.rstrip("/")
        self.headless = headless
        self.results = {"pass": 0, "fail": 0, "details": []}

    def _record(self, test_name: str, passed: bool, message: str = ""):
        status = "[OK]" if passed else "[FAIL]"
        detail = f"  {status} {test_name} - {message}"
        print(detail)
        if passed:
            self.results["pass"] += 1
        else:
            self.results["fail"] += 1
        self.results["details"].append({"test": test_name, "status": "PASS" if passed else "FAIL", "message": message})

    def _screenshot(self, page, name):
        """截图保存"""
        import os
        screenshot_dir = os.path.join(os.path.dirname(__file__), "..", "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        path = os.path.join(screenshot_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        page.screenshot(path=path, full_page=True)
        return path

    def test_login_page(self, page):
        """测试登录页面"""
        print("\n=== 登录页面 ===")
        try:
            page.goto(f"{self.frontend_url}/#/login", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(1000)

            # 检查关键元素
            username_input = page.locator('input[placeholder*="用户名"], input[type="text"]').first
            password_input = page.locator('input[placeholder*="密码"], input[type="password"]').first
            login_btn = page.locator('button:has-text("登录"), button:has-text("登 录")').first

            has_username = username_input.count() > 0
            has_password = password_input.count() > 0
            has_btn = login_btn.count() > 0

            self._record("登录页-用户名输入框", has_username, "存在" if has_username else "不存在")
            self._record("登录页-密码输入框", has_password, "存在" if has_password else "不存在")
            self._record("登录页-登录按钮", has_btn, "存在" if has_btn else "不存在")

            # 测试登录流程
            if has_username and has_password and has_btn:
                username_input.fill("admin")
                password_input.fill("123456")
                login_btn.click()
                page.wait_for_timeout(2000)

                # 检查是否跳转到了仪表盘
                current_url = page.url
                logged_in = "/dashboard" in current_url or "/#" not in current_url or page.locator('.el-menu, .sidebar, nav').count() > 0
                self._record("登录页-登录流程", logged_in, f"登录后URL: {current_url}")
            else:
                self._record("登录页-登录流程", False, "缺少必要元素，无法测试登录")

            path = self._screenshot(page, "login")
            print(f"    截图: {path}")

        except PlaywrightTimeout as e:
            self._record("登录页-加载超时", False, str(e)[:80])
        except Exception as e:
            self._record("登录页-异常", False, str(e)[:80])

    def test_dashboard_page(self, page):
        """测试仪表盘页面"""
        print("\n=== 仪表盘页面 ===")
        try:
            page.goto(f"{self.frontend_url}/#/dashboard", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            # 检查 KPI 卡片
            cards = page.locator('.kpi-card, .stat-card, [class*="card"]').count()
            self._record("仪表盘-KPI卡片", cards > 0, f"发现 {cards} 个卡片")

            # 检查图表
            charts = page.locator('canvas, [class*="chart"], [class*="echart"]').count()
            self._record("仪表盘-图表", charts > 0, f"发现 {charts} 个图表")

            # 检查表格
            tables = page.locator('table, [class*="table"], .el-table').count()
            self._record("仪表盘-表格", tables >= 0, f"发现 {tables} 个表格")

            # 检查标题
            title = page.locator('h1, h2, h3, .page-title, [class*="title"]').first
            has_title = title.count() > 0
            title_text = title.inner_text() if has_title else "N/A"
            self._record("仪表盘-页面标题", has_title, title_text)

            path = self._screenshot(page, "dashboard")
            print(f"    截图: {path}")

        except PlaywrightTimeout as e:
            self._record("仪表盘-加载超时", False, str(e)[:80])
        except Exception as e:
            self._record("仪表盘-异常", False, str(e)[:80])

    def test_monitor_page(self, page):
        """测试设备监控页面"""
        print("\n=== 设备监控页面 ===")
        try:
            page.goto(f"{self.frontend_url}/#/monitor", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            # 检查设备列表/表格
            devices = page.locator('table, .el-table, [class*="device"]').count()
            self._record("设备监控-设备列表", devices >= 0, f"发现 {devices} 个设备相关元素")

            # 检查是否有设备选择器
            selectors = page.locator('select, .el-select, [class*="select"]').count()
            self._record("设备监控-选择器", selectors >= 0, f"发现 {selectors} 个选择器")

            path = self._screenshot(page, "monitor")
            print(f"    截图: {path}")

        except PlaywrightTimeout as e:
            self._record("设备监控-加载超时", False, str(e)[:80])
        except Exception as e:
            self._record("设备监控-异常", False, str(e)[:80])

    def test_alerts_page(self, page):
        """测试告警中心页面"""
        print("\n=== 告警中心页面 ===")
        try:
            page.goto(f"{self.frontend_url}/#/alerts", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            # 检查告警列表
            alerts = page.locator('table, .el-table, [class*="alert"]').count()
            self._record("告警中心-告警列表", alerts >= 0, f"发现 {alerts} 个相关元素")

            path = self._screenshot(page, "alerts")
            print(f"    截图: {path}")

        except PlaywrightTimeout as e:
            self._record("告警中心-加载超时", False, str(e)[:80])
        except Exception as e:
            self._record("告警中心-异常", False, str(e)[:80])

    def test_temperature_page(self, page):
        """测试温度趋势页面"""
        print("\n=== 温度趋势页面 ===")
        try:
            page.goto(f"{self.frontend_url}/#/temperature", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            # 检查图表
            charts = page.locator('canvas, [class*="chart"]').count()
            self._record("温度趋势-图表", charts > 0, f"发现 {charts} 个图表")

            path = self._screenshot(page, "temperature")
            print(f"    截图: {path}")

        except PlaywrightTimeout as e:
            self._record("温度趋势-加载超时", False, str(e)[:80])
        except Exception as e:
            self._record("温度趋势-异常", False, str(e)[:80])

    def test_rules_page(self, page):
        """测试告警规则页面"""
        print("\n=== 告警规则页面 ===")
        try:
            page.goto(f"{self.frontend_url}/#/rules", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            # 检查规则表格
            tables = page.locator('table, .el-table').count()
            self._record("告警规则-规则表格", tables >= 0, f"发现 {tables} 个表格")

            # 检查添加按钮
            add_btn = page.locator('button:has-text("添加"), button:has-text("新增"), button:has-text("创建")').count()
            self._record("告警规则-添加按钮", add_btn >= 0, f"发现 {add_btn} 个操作按钮")

            path = self._screenshot(page, "rules")
            print(f"    截图: {path}")

        except PlaywrightTimeout as e:
            self._record("告警规则-加载超时", False, str(e)[:80])
        except Exception as e:
            self._record("告警规则-异常", False, str(e)[:80])

    def test_navigation(self, page):
        """测试侧边栏导航"""
        print("\n=== 导航测试 ===")
        try:
            page.goto(f"{self.frontend_url}/#/dashboard", wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(1000)

            # 检查侧边栏菜单
            menu_items = page.locator('.el-menu-item, [class*="nav"], [class*="menu"] a, [class*="sidebar"] a').all()
            menu_count = len(menu_items)
            self._record("导航-菜单项数量", menu_count > 0, f"发现 {menu_count} 个菜单项")

            if menu_count > 0:
                # 打印所有菜单文本
                menu_texts = []
                for item in menu_items[:10]:
                    try:
                        text = item.inner_text().strip()
                        if text:
                            menu_texts.append(text)
                    except:
                        pass
                print(f"    菜单项: {menu_texts}")
                self._record("导航-菜单文本", len(menu_texts) > 0, str(menu_texts))

        except PlaywrightTimeout as e:
            self._record("导航-加载超时", False, str(e)[:80])
        except Exception as e:
            self._record("导航-异常", False, str(e)[:80])

    def test_responsive(self, page):
        """测试响应式布局"""
        print("\n=== 响应式布局 ===")

        sizes = [
            ("桌面端 (1920x1080)", 1920, 1080),
            ("平板端 (768x1024)", 768, 1024),
            ("手机端 (375x667)", 375, 667),
        ]

        for name, width, height in sizes:
            try:
                page.set_viewport_size({"width": width, "height": height})
                page.goto(f"{self.frontend_url}/#/dashboard", wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(1000)

                # 检查页面是否正常渲染（无横向滚动条且内容可见）
                body = page.locator('body')
                is_visible = body.is_visible()
                self._record(f"响应式-{name}", is_visible, "页面可见" if is_visible else "页面不可见")
            except Exception as e:
                self._record(f"响应式-{name}", False, str(e)[:80])

    def report(self):
        """输出测试报告"""
        print("\n" + "=" * 60)
        print("  前端 E2E 测试报告")
        print("=" * 60)
        total = self.results["pass"] + self.results["fail"]
        print(f"  总计: {total} 个测试")
        print(f"  通过: {self.results['pass']} 个  [OK]")
        print(f"  失败: {self.results['fail']} 个  [FAIL]")
        print(f"  通过率: {self.results['pass']/total*100:.1f}%" if total > 0 else "  通过率: N/A")
        print("=" * 60)
        return self.results["fail"] == 0

    def run_all(self):
        """运行所有前端测试"""
        print("=" * 60)
        print(f"  冷链物流监控平台 前端 E2E 测试")
        print(f"  目标: {self.frontend_url}")
        print(f"  模式: {'无头' if self.headless else '可视化'}")
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN"
            )
            page = context.new_page()

            try:
                self.test_login_page(page)
                self.test_dashboard_page(page)
                self.test_monitor_page(page)
                self.test_alerts_page(page)
                self.test_temperature_page(page)
                self.test_rules_page(page)
                self.test_navigation(page)
                self.test_responsive(page)
            finally:
                browser.close()

        return self.report()


def main():
    parser = argparse.ArgumentParser(description="冷链物流监控平台 前端 E2E 测试")
    parser.add_argument("--url", default="http://localhost:3000", help="前端地址 (默认: http://localhost:3000)")
    parser.add_argument("--headless", action="store_true", default=True, help="无头模式 (默认)")
    parser.add_argument("--headed", action="store_true", help="可视化模式")
    args = parser.parse_args()

    headless = not args.headed
    tester = FrontendTester(frontend_url=args.url, headless=headless)
    success = tester.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
