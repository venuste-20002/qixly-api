import logging
import sys

log_format = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

sqlalchemy_logger = logging.getLogger("sqlalchemy")
sqlalchemy_logger.setLevel(logging.ERROR)

sqlalchemy_file_handler = logging.FileHandler("logs/dbLogs.log")
sqlalchemy_file_handler.setFormatter(log_format)

sqlalchemy_logger.handlers = [sqlalchemy_file_handler]

logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)


app_file_handler = logging.FileHandler("logs/app.log")
app_stream_handler = logging.StreamHandler(sys.stdout)

app_file_handler.setFormatter(log_format)
app_stream_handler.setFormatter(log_format)

logger.handlers = [app_file_handler, app_stream_handler]

sqlalchemy_logger.propagate = False
logger.propagate = False
