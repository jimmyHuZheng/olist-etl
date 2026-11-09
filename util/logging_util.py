##
import os
import logging
from config.olist_config import  log_name,log_root_path,level

#先封装一个类
class Logging():
    def __init__(self,level=20):
        self.logger = logging.getLogger()
        self.logger.setLevel(level)


def init_logger():
    logger = Logging(level).logger

    #避免重复输出日志
    if logger.handlers:
        return logger

    # 1. 自动检查并创建不存在的日志目录
    if not os.path.exists(log_root_path):
        os.makedirs(log_root_path, exist_ok=True)
    # 2. 安全拼接完整日志路径
    full_log_path = os.path.join(log_root_path, log_name)

    # 构造一个handle对象
    stream_handler =  logging.StreamHandler()
    file_handler = logging.FileHandler(
        filename= full_log_path, #这里要变成每天每小时生成一个
        mode='a',
        encoding = 'utf8'
    )

    fmt = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(filename)s[%(lineno)d]：%(message)s'
    )

    stream_handler.setFormatter(fmt)
    file_handler.setFormatter(fmt)

    #组合
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger