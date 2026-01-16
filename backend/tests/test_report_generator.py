"""
报告生成器单元测试
"""
import os
import sys

import pytest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.report_generator import TEMPLATE_DIR, ReportGenerator, generate_html_report


class TestReportGenerator:
    """报告生成器测试"""

    @pytest.fixture
    def sample_data(self):
        """示例测试数据"""
        run_info = {
            "id": 1,
            "scenario_id": "test_scenario",
            "scenario_name": "测试场景",
            "test_type": "sensitivity",
            "status": "completed",
            "start_time": "2024-01-01 10:00:00",
            "end_time": "2024-01-01 10:05:00",
            "result_summary": "测试成功完成"
        }

        metrics = [
            {"elapsed_time": 0, "throughput_mbps": 150, "bler": 0.01, "power_dbm": -80},
            {"elapsed_time": 1, "throughput_mbps": 160, "bler": 0.02, "power_dbm": -82},
            {"elapsed_time": 2, "throughput_mbps": 140, "bler": 0.015, "power_dbm": -84},
        ]

        statistics = {
            "sample_count": 3,
            "avg_throughput": 150.0,
            "max_throughput": 160.0,
            "min_throughput": 140.0,
            "avg_bler": 0.015,
            "max_bler": 0.02,
            "min_power": -84,
            "max_power": -80
        }

        return run_info, metrics, statistics

    def test_template_exists(self):
        """测试模板文件存在"""
        template_path = os.path.join(TEMPLATE_DIR, "report.html")
        assert os.path.exists(template_path)

    def test_generate_html_report(self, sample_data):
        """测试生成 HTML 报告"""
        run_info, metrics, statistics = sample_data

        html = generate_html_report(run_info, metrics, statistics)

        assert html is not None
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
        assert "测试场景" in html
        assert "sensitivity" in html

    def test_report_generator_class(self, sample_data):
        """测试报告生成器类"""
        run_info, metrics, statistics = sample_data

        generator = ReportGenerator(run_info, metrics, statistics)

        html = generator.to_html()

        assert html is not None
        assert "测试场景" in html

    def test_html_contains_metrics(self, sample_data):
        """测试 HTML 包含指标数据"""
        run_info, metrics, statistics = sample_data

        html = generate_html_report(run_info, metrics, statistics)

        # 检查统计数据是否包含在报告中
        assert "150.00" in html  # 平均吞吐量
        assert "160.00" in html  # 最大吞吐量

    def test_html_with_empty_metrics(self, sample_data):
        """测试空指标数据的报告生成"""
        run_info, _, statistics = sample_data

        html = generate_html_report(run_info, [], statistics)

        assert html is not None
        assert "测试场景" in html

    def test_report_status_styling(self):
        """测试不同状态的样式"""
        run_info_completed = {
            "id": 1,
            "scenario_id": "test",
            "scenario_name": "Test",
            "test_type": "sensitivity",
            "status": "completed",
            "start_time": None,
            "end_time": None,
            "result_summary": None
        }

        run_info_failed = {
            "id": 2,
            "scenario_id": "test",
            "scenario_name": "Test",
            "test_type": "sensitivity",
            "status": "failed",
            "start_time": None,
            "end_time": None,
            "result_summary": "Error occurred"
        }

        html_completed = generate_html_report(run_info_completed, [], {})
        html_failed = generate_html_report(run_info_failed, [], {})

        assert "COMPLETED" in html_completed
        assert "FAILED" in html_failed


class TestReportGeneratorEdgeCases:
    """边界情况测试"""

    def test_none_values_in_statistics(self):
        """测试统计数据中的 None 值"""
        run_info = {
            "id": 1,
            "scenario_id": "test",
            "scenario_name": "Test",
            "test_type": "sensitivity",
            "status": "running",
            "start_time": None,
            "end_time": None,
            "result_summary": None
        }

        statistics = {
            "sample_count": 0,
            "avg_throughput": None,
            "max_throughput": None,
            "min_throughput": None,
            "avg_bler": None,
            "max_bler": None,
        }

        # 不应抛出异常
        html = generate_html_report(run_info, [], statistics)
        assert html is not None

    def test_large_metrics_list(self):
        """测试大量指标数据"""
        run_info = {
            "id": 1,
            "scenario_id": "test",
            "scenario_name": "Test",
            "test_type": "sensitivity",
            "status": "completed",
            "start_time": None,
            "end_time": None,
            "result_summary": None
        }

        # 100 条指标数据
        metrics = [
            {"elapsed_time": i, "throughput_mbps": 100 + i, "bler": 0.01, "power_dbm": -80}
            for i in range(100)
        ]

        statistics = {"sample_count": 100}

        html = generate_html_report(run_info, metrics, statistics)

        # 报告应该只显示前 50 条
        assert "共 100 条记录" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
