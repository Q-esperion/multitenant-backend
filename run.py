import uvicorn
from uvicorn.config import LOGGING_CONFIG
from app.core.config import settings, setup_logging
from app.core.log import get_logger

# 获取logger
logger = get_logger("run")

def main():
    # 初始化日志配置
    setup_logging()
    logger.info("Starting application...")

    # 修改默认日志配置
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
    LOGGING_CONFIG["formatters"]["access"][
        "fmt"
    ] = '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    LOGGING_CONFIG["formatters"]["access"]["datefmt"] = "%Y-%m-%d %H:%M:%S"

    # 从settings获取主机和端口配置
    host = settings.APP_HOST
    port = settings.APP_PORT

    logger.info(f"Server starting on {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
        log_config=LOGGING_CONFIG
    )

if __name__ == "__main__":
    main() 