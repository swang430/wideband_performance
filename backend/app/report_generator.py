"""
报告生成引擎 - 使用 Jinja2 模板生成 HTML/PDF 测试报告
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

# 模板目录
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# 报告输出目录
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def ensure_reports_dir():
    """确保报告输出目录存在"""
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


def generate_html_report(
    run_info: Dict[str, Any],
    metrics: List[Dict[str, Any]],
    statistics: Dict[str, Any],
    template_name: str = "report.html"
) -> str:
    """
    生成 HTML 格式的测试报告

    Args:
        run_info: 测试运行基本信息
        metrics: 指标采样数据列表
        statistics: 统计摘要
        template_name: 使用的模板文件名

    Returns:
        生成的 HTML 内容字符串
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(template_name)

    html_content = template.render(
        run_info=run_info,
        metrics=metrics,
        statistics=statistics,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    return html_content


def save_html_report(run_id: int, html_content: str) -> str:
    """
    保存 HTML 报告到文件

    Args:
        run_id: 测试运行 ID
        html_content: HTML 内容

    Returns:
        保存的文件路径
    """
    ensure_reports_dir()
    filename = f"report_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return filepath


def generate_pdf_report(
    run_info: Dict[str, Any],
    metrics: List[Dict[str, Any]],
    statistics: Dict[str, Any]
) -> Optional[bytes]:
    """
    生成 PDF 格式的测试报告

    Args:
        run_info: 测试运行基本信息
        metrics: 指标采样数据列表
        statistics: 统计摘要

    Returns:
        PDF 文件的字节内容，如果生成失败则返回 None
    """
    # 先生成 HTML
    html_content = generate_html_report(run_info, metrics, statistics)

    try:
        from weasyprint import CSS, HTML
        from weasyprint.text.fonts import FontConfiguration

        font_config = FontConfiguration()

        # 使用内置的中文字体支持
        css = CSS(string='''
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&display=swap');
        ''', font_config=font_config)

        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)

        return pdf_bytes

    except ImportError:
        print("[ReportGenerator] weasyprint 未安装，无法生成 PDF")
        return None
    except Exception as e:
        print(f"[ReportGenerator] PDF 生成失败: {e}")
        return None


def save_pdf_report(run_id: int, pdf_bytes: bytes) -> str:
    """
    保存 PDF 报告到文件

    Args:
        run_id: 测试运行 ID
        pdf_bytes: PDF 字节内容

    Returns:
        保存的文件路径
    """
    ensure_reports_dir()
    filename = f"report_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)

    return filepath


class ReportGenerator:
    """报告生成器类 - 提供便捷的报告生成接口"""

    def __init__(self, run_info: Dict[str, Any], metrics: List[Dict[str, Any]], statistics: Dict[str, Any]):
        self.run_info = run_info
        self.metrics = metrics
        self.statistics = statistics

    def to_html(self) -> str:
        """生成 HTML 报告内容"""
        return generate_html_report(self.run_info, self.metrics, self.statistics)

    def to_pdf(self) -> Optional[bytes]:
        """生成 PDF 报告字节"""
        return generate_pdf_report(self.run_info, self.metrics, self.statistics)

    def save_html(self) -> str:
        """保存 HTML 报告并返回路径"""
        html = self.to_html()
        return save_html_report(self.run_info['id'], html)

    def save_pdf(self) -> Optional[str]:
        """保存 PDF 报告并返回路径"""
        pdf = self.to_pdf()
        if pdf:
            return save_pdf_report(self.run_info['id'], pdf)
        return None
