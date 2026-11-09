"""

Pipeline 基类：
    1. transform: 抽象方法，子类必须实现具体的清洗规则
    2. load: 通用模板方法，子类直接继承复用，无需重复编写

"""

from abc import ABC,abstractmethod
from util.mysql_util import MySQLUtil
from datetime import datetime
import config.olist_config as conf
import pandas as pd
import numpy as np

class BasePipeline(ABC):

    # 修改dim
    target_layer = 'dwd' #默认目标层是dwd

    @abstractmethod
    def transform(self,df:pd.DataFrame) -> pd.DataFrame:
        """每个表特有的清洗逻辑，子类必须实现"""
        pass

    def _map_dtype_to_mysql(self, dtype_str: str) -> str:
        """内部类型映射助手方法"""
        dtype_str = dtype_str.lower()
        if 'int' in dtype_str:
            return "INT"
        elif 'float' in dtype_str:
            return "DECIMAL(10,2)"
        elif 'datetime' in dtype_str:
            return "DATETIME"
        else:
            return "TEXT"

    def load(self,
             df: pd.DataFrame,  # 清洗完成的 DataFrame
             target_table: str,  # 要插入的表
             mu: MySQLUtil = None,
             db_name: str = conf.OlistETl_database,  # 要插入的数据库
             batch_size: int = 2000,
             primary_key: str = None,
             # 主键指定
             ):

        # 写入 MySQL
        """
        落库逻辑：
        1. 检查目标表是否存在，不存在则由 pandas 依据类型自动创建表结构并写入
        2. 支持大批量分批写入
        """
        """
                调用自定义的 MySQLUtil 进行建表和数据入库
                :param df: 清洗完成的 DataFrame
                :param mu: 传入你实例化的 MySQLUtil 对象
                :param db_name: 目标数据库名
                :param batch_size: 分批写入数量
                """
        if mu is None:
            mu = MySQLUtil()

        if df.empty:
            print("数据为空，跳过入库")
            return

        # 0. 动态确定主键：若未显式指定，默认取 DataFrame 的第一个字段作为主键
        pk_col = primary_key if primary_key else df.columns[0]

        # 1. 切换数据库
        mu.select_db(db_name)

        # 2. 判断表是否存在，若不存在则自动动态建表
        if not mu.check_table_exists(db_name, target_table):
            col_definitions = []
            for col in df.columns:
                sql_type = self._map_dtype_to_mysql(str(df[col].dtype))
                # 动态主键判端：只要是主键字段，设置主键约束
                if col == pk_col:
                    # 主键如果是文本类型，MySQL 必须指定具体长度（如 VARCHAR(64)），不能用 TEXT
                    if "TEXT" in sql_type or "VARCHAR" in sql_type:
                        col_definitions.append(f"`{col}` VARCHAR(64) PRIMARY KEY")
                    else:
                        col_definitions.append(f"`{col}` {sql_type} PRIMARY KEY")
                else:
                    col_definitions.append(f"`{col}` {sql_type}")

            create_cols_sql = ", ".join(col_definitions)
            mu.create_table(db_name, target_table, create_cols_sql)
            print(f"目标表 `{target_table}` 不存在，已自动创建（主键字段: `{pk_col}`）")

        # 3. 构造要插入的字段声明
        col_names = ", ".join([f"`{col}`" for col in df.columns])

        # 4. 定义单个值的 SQL 格式化函数（安全处理 NULL、NaN、NaT 和字符串引号）
        def format_value(val):
            if val is None or pd.isna(val):
                return "NULL"
            if isinstance(val, (int, np.integer)):
                return str(val)
            if isinstance(val, (float, np.floating)):
                return f"{val:.2f}"
            if isinstance(val, (datetime, pd.Timestamp)):
                return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
            # 字符串转义
            clean_str = str(val).replace("\\", "\\\\").replace("'", "''")
            return f"'{clean_str}'"

        # 5. 分批转换并执行插入
        records = df.to_dict(orient='records')
        total_rows = len(records)
        print(f"开始向 `{db_name}`.`{target_table}` 写入清洗后数据，共 {total_rows} 条...")

        for i in range(0, total_rows, batch_size):
            chunk = records[i: i + batch_size]
            val_rows = []
            for row in chunk:
                row_vals = [format_value(row[col]) for col in df.columns]
                val_rows.append(f"({', '.join(row_vals)})")

            # 插入语句，如果想支持重复主键自动更新或跳过，可换成 INSERT IGNORE 或 ON DUPLICATE KEY UPDATE
            #batch_sql = f"INSERT INTO `{db_name}`.`{target_table}` ({col_names}) VALUES {', '.join(val_rows)};"
            # 自动拼接更新子句：排除主键自身，其余字段赋值为 VALUES(col)
            update_clause = ", ".join([f"`{col}` = VALUES(`{col}`)" for col in df.columns if col != pk_col])

            batch_sql = (
                f"INSERT INTO `{db_name}`.`{target_table}` ({col_names}) "
                f"VALUES {', '.join(val_rows)} "
                f"ON DUPLICATE KEY UPDATE {update_clause};"
            )
            mu.execute_without_autocommit(batch_sql)

        # 6. 单表批次完成后手动提交事务
        print(f"数据成功写入 `{target_table}` 缓存区，共 {total_rows} 条记录！")