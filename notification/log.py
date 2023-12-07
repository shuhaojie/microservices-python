import logging
import os
from logging import handlers

# 服务被访问的日志记录
api_log = logging.getLogger('api_log')

# log_dir = os.path.dirname(os.path.abspath(__file__))


log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log_init():
    api_log.setLevel(level=logging.INFO)
    formatter = logging.Formatter(
        '进程ID:%(process)d - '
        '线程ID:%(thread)d- '
        '日志时间:%(asctime)s - '
        '代码路径:%(pathname)s:%(lineno)d - '
        '日志等级:%(levelname)s - '
        '日志信息:%(message)s'
    )
    api_log.handlers.clear()
    # 设置api log存储
    base_path = os.path.join(log_dir, "log")
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
    api_handler = handlers.TimedRotatingFileHandler(os.path.join(base_path, "api.log"), encoding='utf-8',
                                                    when='W6')
    api_handler.setLevel(level=logging.INFO)
    api_handler.setFormatter(formatter)
    api_log.addHandler(api_handler)
