from unittest import TestCase

import pandas as pd

import config.olist_config as conf
from pipeline.DWD.order_pipeline import OrdersPipeline
from util.read_file_util import FileUtil
from util.mysql_util import  MySQLUtil


class TestReadFileUtil(TestCase):

    def setUp(self) ->None:
        pass


    def test_process(self) ->None:
        # 实例化
        pipeline = OrdersPipeline()
        mu = MySQLUtil()
        # 先读取文件
        file_list = FileUtil.get_dir_files_list(conf.income_data_path)
        for file in file_list:
            print(file)
            # 执行读取
            cols,row = FileUtil.read_file_data(file)
            print(f"cols:{cols},row:{row}")
            raw_df = pd.DataFrame(row, columns=cols)

            # 执行pipeline
            clean_df = pipeline.transform(raw_df)
            print(clean_df)

            # 需要插入mysql里
            # pipeline.load(clean_df)



        #pipeline.load(clean_df, engine=engine, if_exists="append", db_name="dwd_olist")



    def tearDown(self) -> None:
        pass