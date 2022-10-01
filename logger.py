import logging
import time

logging_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
logging_datefmt = '%Y-%m-%d %H:%M:%S'
log_formatter = logging.Formatter(logging_format, logging_datefmt)

logging.basicConfig(
        level=logging.WARNING,
        format=logging_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("access_manager.log", mode='a')
        ],
        datefmt=logging_datefmt
    )

logging.Formatter.converter = time.gmtime

usage_logger = logging.getLogger('access_manager.usage')
usage_logger.setLevel(logging.INFO)

am_logger = logging.getLogger('access_manager')
am_logger.setLevel(logging.INFO)