"""
API 端点单元测试
"""
import pytest
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """健康检查端点测试"""

    def test_health_check(self):
        """测试健康检查返回正常"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestInstrumentsEndpoint:
    """仪表状态端点测试"""

    def test_get_instruments_status(self):
        """测试获取仪表状态"""
        response = client.get("/api/v1/instruments/status")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestScenariosEndpoint:
    """场景端点测试"""

    def test_list_scenarios(self):
        """测试获取场景列表"""
        response = client.get("/api/v1/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # 应该有预设的场景文件
        if len(data) > 0:
            assert "filename" in data[0]
            assert "name" in data[0]


class TestHistoryEndpoint:
    """历史记录端点测试"""

    def test_list_history(self):
        """测试获取历史记录列表"""
        response = client.get("/api/v1/history")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_nonexistent_history(self):
        """测试获取不存在的历史记录"""
        response = client.get("/api/v1/history/999999")

        assert response.status_code == 404


class TestConfigEndpoint:
    """配置端点测试"""

    def test_list_config_files(self):
        """测试获取配置文件列表"""
        response = client.get("/api/v1/config/files")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # 应该至少有 config.yaml
        filenames = [f["filename"] for f in data]
        assert "config.yaml" in filenames

    def test_get_config_content(self):
        """测试获取配置文件内容"""
        response = client.get("/api/v1/config/config/config.yaml")

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "filename" in data

    def test_get_nonexistent_config(self):
        """测试获取不存在的配置文件"""
        response = client.get("/api/v1/config/config/nonexistent.yaml")

        assert response.status_code == 404

    def test_invalid_file_type(self):
        """测试无效的文件类型"""
        response = client.get("/api/v1/config/invalid/config.yaml")

        assert response.status_code == 400


class TestTestControlEndpoint:
    """测试控制端点测试"""

    def test_stop_without_running(self):
        """测试未运行时停止"""
        response = client.post("/api/v1/test/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["running"] is False


class TestReportEndpoint:
    """报告端点测试"""

    def test_get_nonexistent_report(self):
        """测试获取不存在的报告"""
        response = client.get("/api/v1/report/999999/html")

        assert response.status_code == 404


class TestManualsEndpoint:
    """手册端点测试"""

    def test_get_manuals_catalog(self):
        """测试获取手册目录"""
        response = client.get("/api/v1/manuals")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
