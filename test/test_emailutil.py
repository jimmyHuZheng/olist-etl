import time

import config.olist_config as conf

from unittest import TestCase
from util.email_util import EmailUtil

class TestReadFileUtil(TestCase):

    def setUp(self) ->None:
         pass



    def test_process(self) ->None:
        # 实例化
        eu = EmailUtil(
            sender_email=conf.email_send,
            auth_code=conf.email_auth_code,
            receiver_emails=conf.email_receicers
        )
        start_time = time.time()
        eu.send_success_email(
            task_name="每日定时任务",
            duration = time.time() - start_time,
            detail=" 各文件已正常读取并成功写入 MySQL (ODS & DWD)。"
        )
    def tearDown(self) -> None:
        pass