"""
数据库模块单元测试
"""
import pytest
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import (
    TestRunRepository,
    MetricsSampleRepository,
    init_database,
    get_connection
)


class TestDatabase:
    """数据库基础功能测试"""

    def test_database_init(self):
        """测试数据库初始化"""
        init_database()
        conn = get_connection()
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert 'test_runs' in tables
        assert 'metrics_samples' in tables
        conn.close()


class TestTestRunRepository:
    """测试运行记录仓库测试"""

    def test_create_and_get(self):
        """测试创建和获取测试记录"""
        run_id = TestRunRepository.create(
            scenario_id="test_scenario_1",
            scenario_name="测试场景1",
            test_type="sensitivity"
        )

        assert run_id is not None
        assert run_id > 0

        # 获取记录
        run = TestRunRepository.get_by_id(run_id)
        assert run is not None
        assert run['scenario_id'] == "test_scenario_1"
        assert run['scenario_name'] == "测试场景1"
        assert run['test_type'] == "sensitivity"
        assert run['status'] == "running"

        # 清理
        TestRunRepository.delete(run_id)

    def test_update_status(self):
        """测试更新状态"""
        run_id = TestRunRepository.create(
            scenario_id="test_scenario_2",
            scenario_name="测试场景2",
            test_type="blocking"
        )

        TestRunRepository.update_status(run_id, "completed", "测试成功")

        run = TestRunRepository.get_by_id(run_id)
        assert run['status'] == "completed"
        assert run['result_summary'] == "测试成功"
        assert run['end_time'] is not None

        # 清理
        TestRunRepository.delete(run_id)

    def test_list_recent(self):
        """测试获取最近记录列表"""
        # 创建多条记录
        ids = []
        for i in range(5):
            run_id = TestRunRepository.create(
                scenario_id=f"test_list_{i}",
                scenario_name=f"列表测试{i}",
                test_type="sensitivity"
            )
            ids.append(run_id)

        # 获取列表
        runs = TestRunRepository.list_recent(limit=3)
        assert len(runs) >= 3

        # 清理
        for run_id in ids:
            TestRunRepository.delete(run_id)

    def test_delete(self):
        """测试删除记录"""
        run_id = TestRunRepository.create(
            scenario_id="test_delete",
            scenario_name="删除测试",
            test_type="dynamic_scenario"
        )

        TestRunRepository.delete(run_id)

        run = TestRunRepository.get_by_id(run_id)
        assert run is None


class TestMetricsSampleRepository:
    """指标采样仓库测试"""

    def setup_method(self):
        """每个测试方法前创建测试运行记录"""
        self.run_id = TestRunRepository.create(
            scenario_id="metrics_test",
            scenario_name="指标测试",
            test_type="sensitivity"
        )

    def teardown_method(self):
        """每个测试方法后清理"""
        TestRunRepository.delete(self.run_id)

    def test_insert_single(self):
        """测试插入单条指标"""
        MetricsSampleRepository.insert(
            run_id=self.run_id,
            timestamp=1000.0,
            elapsed_time=1.0,
            throughput_mbps=150.5,
            bler=0.02,
            power_dbm=-85.0
        )

        samples = MetricsSampleRepository.get_by_run_id(self.run_id)
        assert len(samples) == 1
        assert samples[0]['throughput_mbps'] == 150.5
        assert samples[0]['bler'] == 0.02

    def test_insert_batch(self):
        """测试批量插入指标"""
        samples_data = [
            {"timestamp": 1000 + i, "elapsed_time": float(i),
             "throughput_mbps": 100 + i * 10, "bler": 0.01 + i * 0.001}
            for i in range(10)
        ]

        MetricsSampleRepository.insert_batch(self.run_id, samples_data)

        samples = MetricsSampleRepository.get_by_run_id(self.run_id)
        assert len(samples) == 10

    def test_get_statistics(self):
        """测试统计计算"""
        samples_data = [
            {"timestamp": 1000, "elapsed_time": 0, "throughput_mbps": 100, "bler": 0.01},
            {"timestamp": 1001, "elapsed_time": 1, "throughput_mbps": 200, "bler": 0.02},
            {"timestamp": 1002, "elapsed_time": 2, "throughput_mbps": 150, "bler": 0.015},
        ]

        MetricsSampleRepository.insert_batch(self.run_id, samples_data)

        stats = MetricsSampleRepository.get_statistics(self.run_id)

        assert stats['sample_count'] == 3
        assert stats['avg_throughput'] == 150.0
        assert stats['max_throughput'] == 200.0
        assert stats['min_throughput'] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
