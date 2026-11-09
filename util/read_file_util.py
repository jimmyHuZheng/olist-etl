import os
import json
import shutil

import pandas as pd

from pathlib import Path
from typing import List, Tuple
from datetime import datetime


from util.logging_util import init_logger

logger = init_logger()

class FileUtil:
    """
    纯文件操作工具类：
    一个只有
    负责文件列表获取，多格式文件解析（csv/ xls / xlsx /json）
    """
    # @staticmethod 静态方法
    @staticmethod
    def get_dir_files_list(dir_path: str,
                           allowed_exts: tuple = ('.csv', '.xls', '.xlsx', '.json')
                           ) ->List[str]:

        # 获取指定目录下所有匹配后缀的文件绝对路径列表
        if not os.path.exists(dir_path):
            logger.warning(f"目录不存在：{dir_path}")

        file_list = []
        # root 是当前所在文件夹路径，files是当前文件夹里所有文件名
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                ext = Path(file).suffix.lower()   #提取当前文件的后缀名，并统一转换为小写
                if ext in allowed_exts:
                    file_list.append(os.path.join(root,file))

        # print(file_list)
        return file_list

    @staticmethod
    def get_table_name_from_file(file_path: str) -> str:
        """
        从文件路径种解析出对应的数据表名(默认去除后缀名)，同时进行
        :param file_path:
        :return:
        """
        stem = Path(file_path).stem  # 先去除扩展名，得到 orders_261030


        return stem

    # --------------------------底层文件读取函数 -------------------------------------

    @staticmethod
    def read_csv(file_path: str, sep: str=',') -> Tuple[List[str], List[List[str]]]:
        # 读取 csv文件 返回 （列名列表，数据二维列表），保留字符串格式
        try:
            df = pd.read_csv(file_path, sep=sep, dtype=str, keep_default_na=False, encoding='gb18030')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, sep=sep, dtype=str, keep_default_na=False, encoding='gb18030')
        return list(df.columns),df.values.tolist()

    @staticmethod
    def read_excel(file_path: str)-> Tuple[List[str],List[List[str]]]:
        # 读取 excel（.xls 或 .xlsx）返回（列名列表，数据二维列表）
        df = pd.read_excel(file_path,dtype=str,keep_default_na=False)
        return list(df.columns),df.values.tolist()

    @staticmethod
    def read_json(file_path: str) -> Tuple[List[str],List[List[str]]]:
        # 读取 json/ jsonLines，返回（列名列表，数据二维列表）
        with open(file_path,'r', encoding='gb18030') as f:
            first_char = f.read(1)
            f.seek(0)
            if first_char == '[':
                data = json.load(f)
            else:
                data = [json.loads(line) for line in f if line.strip()]

        if not data:
            return [],[]

        cols = list(data[0].keys())
        rows = [[str(item.get(c,'')) if item.get(c) is not None else '' for c in cols] for item in data]
        return cols,rows


    # -----------------------统一路由入口 -------------------------------

    @classmethod
    def read_file_data(cls, file_path: str) -> Tuple[List[str], List[List[str]]]:

        """
        统一分发入口：依据后缀选择对应的解析器
        未来如果有新增格式，直接在此扩充即可
        :param cls:
        :param file_path:
        :return:
         """
        ext = Path(file_path).suffix.lower()

        if ext == '.csv':
            return cls.read_csv(file_path)
        elif ext in ('.xls',',xlsx'):
            return cls.read_excel(file_path)
        elif ext == 'json':
            return cls.read_json(file_path)
        else:
            logger.warning(f"暂时不支持的文件格式：{ext}")

# if __name__ == '__main__':
#     util = FileUtil()
#     util.get_dir_files_list(r"C:\Users\杰武\Desktop\etl-python\olist-etl\income")


    def move_file(self,src_file_path:str,target_dir:str):
        """
        将文件从原路径移动到目标目录，如果目标已存在同名文件，自动追加时间戳防覆盖
        :param src_file_path:
        :param target_dir:
        :return:
        """
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        filename = os.path.basename(src_file_path)
        dest_path = os.path.join(target_dir,filename)

        # 如果目标目录已有同名文件，重命名为：原名_20261104_153022.csv
        if os.path.exists(dest_path):
            stem,ext = os.path.splitroot(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = os.path.join(target_dir,f"{stem}_{timestamp}{ext}")

        shutil.move(src_file_path,dest_path)
        return dest_path