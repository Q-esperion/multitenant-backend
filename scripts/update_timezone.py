"""
执行数据库时区更新脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.migrations.update_timezone import update_timezone_columns
from app.core.log import get_logger

logger = get_logger(__name__)

async def main():
    try:
        logger.info("开始更新数据库时区...")
        await update_timezone_columns()
        logger.info("数据库时区更新完成")
    except Exception as e:
        logger.error(f"更新数据库时区失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 