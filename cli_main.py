import logging
import os
import sys

# 将项目根目录添加到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config_loader import ConfigLoader
from core.logger import setup_logger
from core.sequencer import TestSequencer


def main():
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="终端宽带标准信道验证系统")
    parser.add_argument("-c", "--config", default=os.path.join(os.path.dirname(__file__), 'config.yaml'), help="配置文件路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="启用详细日志")
    parser.add_argument("--simulate", action="store_true", help="使用模拟模式运行 (无硬件连接)")

    args = parser.parse_args()

    # 1. 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(level=log_level)
    logger.info("正在初始化终端宽带标准信道验证系统...")
    if args.simulate:
        logger.warning("运行在模拟模式下 - 不会尝试连接真实硬件")

    # 2. 加载配置
    try:
        loader = ConfigLoader(args.config)
        config = loader.load()
    except Exception as e:
        logger.critical(f"中止: {e}")
        return

    # 3. 初始化并运行序列器
    sequencer = TestSequencer(config, simulation_mode=args.simulate)
    try:
        sequencer.run()
    except KeyboardInterrupt:
        logger.info("用户中断。")
        sequencer.cleanup()
    except Exception as e:
        logger.exception(f"执行过程中出现意外错误: {e}")
        sequencer.cleanup()

if __name__ == "__main__":
    main()
