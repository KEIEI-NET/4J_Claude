#!/usr/bin/env python3
"""
API Integration Test Script

バックエンドAPIの統合テスト - 全エンドポイントの動作確認
"""

import sys
import requests
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# APIベースURL
API_BASE_URL = "http://localhost:8000"


class APIIntegrationTester:
    """API統合テスト実行クラス"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results: list[Dict[str, Any]] = []

    def test_health_check(self) -> bool:
        """ヘルスチェックエンドポイントテスト"""
        console.print("\n[bold cyan]1. Testing Health Check Endpoint[/bold cyan]")

        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            data = response.json()

            if response.status_code == 200:
                console.print("[green]✓ Health check passed[/green]")
                console.print(f"  Status: {data.get('status')}")
                console.print(f"  Neo4j Connected: {data.get('neo4j_connected')}")
                console.print(f"  Version: {data.get('version')}")

                self.results.append({
                    "endpoint": "GET /health",
                    "status": "✓ Pass",
                    "code": response.status_code
                })
                return True
            else:
                console.print(f"[red]✗ Health check failed: {response.status_code}[/red]")
                self.results.append({
                    "endpoint": "GET /health",
                    "status": "✗ Fail",
                    "code": response.status_code
                })
                return False

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            self.results.append({
                "endpoint": "GET /health",
                "status": "✗ Error",
                "code": "N/A"
            })
            return False

    def test_impact_analysis(self) -> bool:
        """影響範囲分析エンドポイントテスト"""
        console.print("\n[bold cyan]2. Testing Impact Analysis Endpoint[/bold cyan]")

        payload = {
            "target_type": "file",
            "target_path": "src/main/java/com/example/User.java",
            "depth": 3,
            "include_indirect": True
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/impact-analysis",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                console.print("[green]✓ Impact analysis succeeded[/green]")
                console.print(f"  Affected files: {data['impact_summary']['total_affected_files']}")
                console.print(f"  Risk level: {data['impact_summary']['risk_level']}")

                self.results.append({
                    "endpoint": "POST /api/impact-analysis",
                    "status": "✓ Pass",
                    "code": response.status_code
                })
                return True
            elif response.status_code == 404:
                console.print("[yellow]⚠ File not found (expected if no data)[/yellow]")
                self.results.append({
                    "endpoint": "POST /api/impact-analysis",
                    "status": "⚠ No Data",
                    "code": response.status_code
                })
                return True
            else:
                console.print(f"[red]✗ Failed: {response.status_code}[/red]")
                console.print(f"  Error: {response.json().get('detail', 'Unknown')}")
                self.results.append({
                    "endpoint": "POST /api/impact-analysis",
                    "status": "✗ Fail",
                    "code": response.status_code
                })
                return False

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            self.results.append({
                "endpoint": "POST /api/impact-analysis",
                "status": "✗ Error",
                "code": "N/A"
            })
            return False

    def test_get_dependencies(self) -> bool:
        """依存関係取得エンドポイントテスト"""
        console.print("\n[bold cyan]3. Testing Get Dependencies Endpoint[/bold cyan]")

        file_path = "src/main/java/com/example/User.java"

        try:
            response = requests.get(
                f"{self.base_url}/api/dependencies/{file_path}",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                console.print("[green]✓ Get dependencies succeeded[/green]")
                console.print(f"  Dependency count: {data['dependencies']['dependency_count']}")
                console.print(f"  Dependent count: {data['dependencies']['dependent_count']}")

                self.results.append({
                    "endpoint": "GET /api/dependencies/:path",
                    "status": "✓ Pass",
                    "code": response.status_code
                })
                return True
            elif response.status_code == 404:
                console.print("[yellow]⚠ File not found (expected if no data)[/yellow]")
                self.results.append({
                    "endpoint": "GET /api/dependencies/:path",
                    "status": "⚠ No Data",
                    "code": response.status_code
                })
                return True
            else:
                console.print(f"[red]✗ Failed: {response.status_code}[/red]")
                self.results.append({
                    "endpoint": "GET /api/dependencies/:path",
                    "status": "✗ Fail",
                    "code": response.status_code
                })
                return False

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            self.results.append({
                "endpoint": "GET /api/dependencies/:path",
                "status": "✗ Error",
                "code": "N/A"
            })
            return False

    def test_circular_dependencies(self) -> bool:
        """循環依存検出エンドポイントテスト"""
        console.print("\n[bold cyan]4. Testing Circular Dependencies Endpoint[/bold cyan]")

        try:
            response = requests.get(
                f"{self.base_url}/api/circular-dependencies",
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                console.print("[green]✓ Circular dependencies check succeeded[/green]")
                console.print(f"  Total cycles found: {data['total_cycles']}")
                console.print(f"  Recommendation: {data['recommendation']}")

                self.results.append({
                    "endpoint": "GET /api/circular-dependencies",
                    "status": "✓ Pass",
                    "code": response.status_code
                })
                return True
            else:
                console.print(f"[red]✗ Failed: {response.status_code}[/red]")
                self.results.append({
                    "endpoint": "GET /api/circular-dependencies",
                    "status": "✗ Fail",
                    "code": response.status_code
                })
                return False

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            self.results.append({
                "endpoint": "GET /api/circular-dependencies",
                "status": "✗ Error",
                "code": "N/A"
            })
            return False

    def test_cors(self) -> bool:
        """CORS設定テスト"""
        console.print("\n[bold cyan]5. Testing CORS Configuration[/bold cyan]")

        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }

        try:
            response = requests.options(
                f"{self.base_url}/api/impact-analysis",
                headers=headers,
                timeout=10
            )

            cors_allowed = response.headers.get("Access-Control-Allow-Origin")

            if cors_allowed:
                console.print("[green]✓ CORS configured correctly[/green]")
                console.print(f"  Allowed Origin: {cors_allowed}")
                console.print(f"  Allowed Methods: {response.headers.get('Access-Control-Allow-Methods', 'N/A')}")

                self.results.append({
                    "endpoint": "CORS Preflight",
                    "status": "✓ Pass",
                    "code": response.status_code
                })
                return True
            else:
                console.print("[yellow]⚠ CORS headers not found[/yellow]")
                self.results.append({
                    "endpoint": "CORS Preflight",
                    "status": "⚠ Warning",
                    "code": response.status_code
                })
                return True

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            self.results.append({
                "endpoint": "CORS Preflight",
                "status": "✗ Error",
                "code": "N/A"
            })
            return False

    def run_all_tests(self) -> bool:
        """全テストを実行"""
        console.print(Panel.fit(
            "[bold white]API Integration Test Suite[/bold white]\n"
            f"Testing: {self.base_url}",
            border_style="blue"
        ))

        tests = [
            self.test_health_check,
            self.test_impact_analysis,
            self.test_get_dependencies,
            self.test_circular_dependencies,
            self.test_cors
        ]

        passed = 0
        for test in tests:
            if test():
                passed += 1

        # 結果サマリー
        self.print_summary(passed, len(tests))

        return passed == len(tests)

    def print_summary(self, passed: int, total: int):
        """テスト結果サマリーを表示"""
        console.print("\n" + "=" * 60)

        # テーブル作成
        table = Table(title="Test Results Summary", show_header=True, header_style="bold magenta")
        table.add_column("Endpoint", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("HTTP Code", justify="center")

        for result in self.results:
            status_style = "green" if "Pass" in result["status"] else ("yellow" if "Warning" in result["status"] or "No Data" in result["status"] else "red")
            table.add_row(
                result["endpoint"],
                f"[{status_style}]{result['status']}[/{status_style}]",
                str(result["code"])
            )

        console.print(table)

        # 成功率
        success_rate = (passed / total) * 100 if total > 0 else 0
        console.print(f"\n[bold]Overall Result: {passed}/{total} tests passed ({success_rate:.1f}%)[/bold]")

        if passed == total:
            console.print("[bold green]✓ All tests passed![/bold green]")
        else:
            console.print(f"[bold yellow]⚠ {total - passed} tests failed or had warnings[/bold yellow]")


def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="API Integration Test Script")
    parser.add_argument(
        "--url",
        default=API_BASE_URL,
        help=f"API base URL (default: {API_BASE_URL})"
    )
    args = parser.parse_args()

    tester = APIIntegrationTester(args.url)

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
