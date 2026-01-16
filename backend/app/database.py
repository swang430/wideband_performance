"""
数据库管理模块 - SQLite 持久化测试结果
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_results.db")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典形式的结果
    return conn


@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """初始化数据库表结构"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 测试运行记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT NOT NULL,
                scenario_name TEXT NOT NULL,
                test_type TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                result_summary TEXT,
                config_snapshot TEXT
            )
        """)

        # 指标采样表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                elapsed_time REAL NOT NULL,
                throughput_mbps REAL,
                bler REAL,
                power_dbm REAL,
                extra_data TEXT,
                FOREIGN KEY (run_id) REFERENCES test_runs(id)
            )
        """)

        # 创建索引以加速查询
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_run_id ON metrics_samples(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_runs_start_time ON test_runs(start_time)")


class TestRunRepository:
    """测试运行记录仓库"""

    @staticmethod
    def create(scenario_id: str, scenario_name: str, test_type: str,
               config_snapshot: Optional[str] = None) -> int:
        """创建新的测试运行记录，返回 run_id"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_runs (scenario_id, scenario_name, test_type, config_snapshot)
                VALUES (?, ?, ?, ?)
            """, (scenario_id, scenario_name, test_type, config_snapshot))
            return cursor.lastrowid

    @staticmethod
    def update_status(run_id: int, status: str, result_summary: Optional[str] = None):
        """更新测试状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            if status in ('completed', 'failed', 'stopped'):
                cursor.execute("""
                    UPDATE test_runs
                    SET status = ?, end_time = CURRENT_TIMESTAMP, result_summary = ?
                    WHERE id = ?
                """, (status, result_summary, run_id))
            else:
                cursor.execute("""
                    UPDATE test_runs SET status = ? WHERE id = ?
                """, (status, run_id))

    @staticmethod
    def get_by_id(run_id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 获取测试记录"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_recent(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取最近的测试记录列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM test_runs
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def delete(run_id: int):
        """删除测试记录及其关联的指标数据"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM metrics_samples WHERE run_id = ?", (run_id,))
            cursor.execute("DELETE FROM test_runs WHERE id = ?", (run_id,))


class MetricsSampleRepository:
    """指标采样数据仓库"""

    @staticmethod
    def insert(run_id: int, timestamp: float, elapsed_time: float,
               throughput_mbps: Optional[float] = None,
               bler: Optional[float] = None,
               power_dbm: Optional[float] = None,
               extra_data: Optional[str] = None):
        """插入单条指标采样"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics_samples
                (run_id, timestamp, elapsed_time, throughput_mbps, bler, power_dbm, extra_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (run_id, timestamp, elapsed_time, throughput_mbps, bler, power_dbm, extra_data))

    @staticmethod
    def insert_batch(run_id: int, samples: List[Dict[str, Any]]):
        """批量插入指标采样"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO metrics_samples
                (run_id, timestamp, elapsed_time, throughput_mbps, bler, power_dbm, extra_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                (run_id, s.get('timestamp'), s.get('elapsed_time'),
                 s.get('throughput_mbps'), s.get('bler'), s.get('power_dbm'),
                 s.get('extra_data'))
                for s in samples
            ])

    @staticmethod
    def get_by_run_id(run_id: int) -> List[Dict[str, Any]]:
        """获取指定测试运行的所有指标采样"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM metrics_samples
                WHERE run_id = ?
                ORDER BY elapsed_time ASC
            """, (run_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_statistics(run_id: int) -> Dict[str, Any]:
        """获取指定测试运行的指标统计"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as sample_count,
                    AVG(throughput_mbps) as avg_throughput,
                    MAX(throughput_mbps) as max_throughput,
                    MIN(throughput_mbps) as min_throughput,
                    AVG(bler) as avg_bler,
                    MAX(bler) as max_bler,
                    MIN(power_dbm) as min_power,
                    MAX(power_dbm) as max_power
                FROM metrics_samples WHERE run_id = ?
            """, (run_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}


# 应用启动时初始化数据库
init_database()
