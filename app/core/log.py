import os
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from .config import settings, LOG_FILE, DEBUG_FORMAT, DEFAULT_FORMAT, DATE_FORMAT

# 创建日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志文件路径
LOG_FILE = LOG_DIR / "app.log"

class CustomFormatter(logging.Formatter):
    """自定义日志格式化器，根据日志级别使用不同的格式"""
    
    def format(self, record):
        # 如果是DEBUG级别，使用更详细的格式
        if record.levelno == logging.DEBUG:
            self._style._fmt = DEBUG_FORMAT
        else:
            self._style._fmt = DEFAULT_FORMAT
        return super().format(record)

def get_logger(name: str) -> logging.Logger:
    """
    获取logger实例
    :param name: logger名称，通常使用模块名
    :return: logger实例
    """
    logger = logging.getLogger(name)
    
    # 如果logger已经有处理器，说明已经配置过，直接返回
    if logger.handlers:
        return logger
        
    # 设置日志级别
    logger.setLevel(settings.LOG_LEVEL)
    
    # 创建自定义格式化器
    formatter = CustomFormatter(datefmt=DATE_FORMAT)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 创建文件处理器（按周滚动）
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when='W0',  # 每周一凌晨
        interval=1,  # 间隔为1周
        backupCount=4,  # 保留4周的日志
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 创建默认logger
logger = get_logger("app") 