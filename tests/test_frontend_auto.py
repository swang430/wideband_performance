#!/usr/bin/env python3
"""
前端自动化测试脚本
使用简单的 HTTP 请求验证前端和后端 API
"""

import requests
import json
import time
from typing import Dict, Any

class FrontendTester:
    """前端和 API 自动化测试"""
    
    def __init__(self, backend_url: str = "http://127.0.0.1:8000", frontend_url: str = "http://localhost:5173"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.session = requests.Session()
        
    def test_frontend_accessible(self) -> bool:
        """测试前端是否可访问"""
        try:
            response = self.session.get(self.frontend_url, timeout=5)
            print(f"✅ 前端可访问: {self.frontend_url}")
            print(f"   状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 前端不可访问: {e}")
            return False
    
    def test_backend_root(self) -> bool:
        """测试后端根路径"""
        try:
            response = self.session.get(f"{self.backend_url}/", timeout=5)
            data = response.json()
            print(f"✅ 后端根路径: {data}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 后端根路径失败: {e}")
            return False
    
    def test_get_instruments(self) -> Dict[str, Any]:
        """测试获取仪表状态 API"""
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/instruments", timeout=5)
            instruments = response.json()
            print(f"✅ 仪表状态 API:")
            for inst in instruments:
                status_icon = "🟢" if inst['status'] == 'connected' else "🔴"
                print(f"   {status_icon} {inst['name']}: {inst['type']} ({inst['status']})")
            return {"success": True, "count": len(instruments), "data": instruments}
        except Exception as e:
            print(f"❌ 获取仪表状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    def test_get_scenarios(self) -> Dict[str, Any]:
        """测试获取场景列表 API"""
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/scenarios", timeout=5)
            scenarios = response.json()
            print(f"✅ 场景列表 API:")
            for scenario in scenarios[:5]:  # 只显示前5个
                print(f"   📄 {scenario['name']} ({scenario['filename']})")
            print(f"   总计: {len(scenarios)} 个场景")
            return {"success": True, "count": len(scenarios), "data": scenarios}
        except Exception as e:
            print(f"❌ 获取场景列表失败: {e}")
            return {"success": False, "error": str(e)}
    
    def test_get_test_status(self) -> Dict[str, Any]:
        """测试获取测试状态 API"""
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/test/status", timeout=5)
            status = response.json()
            print(f"✅ 测试状态 API:")
            print(f"   运行中: {status.get('running', False)}")
            if status.get('running'):
                print(f"   当前场景: {status.get('current_scenario', 'N/A')}")
                print(f"   已运行时间: {status.get('elapsed_time', 0):.1f}s")
            return {"success": True, "data": status}
        except Exception as e:
            print(f"❌ 获取测试状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    def test_dut_status(self) -> Dict[str, Any]:
        """测试 DUT 状态 API"""
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/dut/status", timeout=5)
            dut_status = response.json()
            print(f"✅ DUT 状态 API:")
            print(f"   连接状态: {'🟢 已连接' if dut_status.get('connected') else '🔴 未连接'}")
            return {"success": True, "data": dut_status}
        except Exception as e:
            print(f"❌ 获取 DUT 状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    def test_channel_models(self) -> Dict[str, Any]:
        """测试信道模型 API"""
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/channel-models/scenarios", timeout=5)
            data = response.json()
            print(f"✅ 信道模型 API:")
            print(f"   场景数: {data['statistics']['total_scenarios']}")
            print(f"   模型数: {data['statistics']['unique_models']}")
            print(f"   总使用次数: {data['statistics']['total_usage']}")
            return {"success": True, "data": data}
        except Exception as e:
            print(f"❌ 获取信道模型失败: {e}")
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 60)
        print("  前端自动化测试套件")
        print("=" * 60)
        print()
        
        results = {
            "frontend_accessible": self.test_frontend_accessible(),
            "backend_root": self.test_backend_root(),
        }
        
        print()
        print("-" * 60)
        print("  API 端点测试")
        print("-" * 60)
        print()
        
        api_results = {
            "instruments": self.test_get_instruments(),
            "scenarios": self.test_get_scenarios(),
            "test_status": self.test_get_test_status(),
            "dut_status": self.test_dut_status(),
            "channel_models": self.test_channel_models(),
        }
        
        results.update(api_results)
        
        # 统计
        print()
        print("=" * 60)
        print("  测试总结")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for v in results.values() if (isinstance(v, bool) and v) or (isinstance(v, dict) and v.get('success')))
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {total_tests - passed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        return results


if __name__ == "__main__":
    tester = FrontendTester()
    results = tester.run_all_tests()
    
    # 保存结果
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print()
    print(f"✅ 测试结果已保存到: test_results.json")
