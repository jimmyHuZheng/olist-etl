from unittest import TestCase
import config.olist_config as conf
from util.read_file_util import FileUtil


class TestReadFileUtil(TestCase):

    def setUp(self) ->None:
        pass


    def test_process(self) ->None:
        # 实例化
        fu = FileUtil()

        file_list = fu.get_dir_files_list(conf.income_data_path)

        for file_path in file_list:
            # 获取表名
            table_name = fu.get_table_name_from_file(file_path)
            print(f"表名为：{table_name}")
            cols,rows = fu.read_file_data(file_path)
            print(f"：{cols},列：{rows}")


    def tearDown(self) -> None:
        pass