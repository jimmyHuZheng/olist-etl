
import pymysql
import config.olist_config as config
from util import logging_util


'''
 创建一个mysqlutil类 用来管理数据操作连接和方法

 数据库操作工具类

 创建数据库连接
 切换数据库
 执行非查询sql
 执行查询sql
 开始事务
 提交事务
 回滚事务
 检查表是否存在
 检查表是否存在，不存在则创建
 查询指定表的数据
 执行一条插入sql
 关闭数据库连接

'''

logger =logging_util.init_logger()

class MySQLUtil(object):


    def __init__(self,
                 host=config.OlistETl_host,
                 port=config.OlistETl_port,
                 user=config.OlistETl_user,
                 password=config.OlistETl_password,
                 database =config.OlistETl_database
                 ):
        # 初始化工具类对象，在工具对象中添加连接属性
        self.conn = pymysql.connect(
            host = host,
            port = port,
            user = user,
            password= password,
            charset= 'utf8',
            database= database,
            autocommit= False #不自动提交 写在内存缓存中
        )

        #记录日志信息
        if self.conn:
            logger.info(f'主机为{host}:{port}的mysql数据服务已连接{database}……')


    def select_db(self, db_name):
        # 切换数据库
        self.conn.select_db(db_name)
        #日志记录信息
        logger.info(f'已经切换数据库，数据库名为{db_name}')



    def execute(self, sql):
        """执行非查询SQL"""
        # 1. 创建游标
        cursor = self.conn.cursor()
        # 执行sql语句
        cursor.execute(sql)
        #3.开启自动提交是否开启
        if not self.conn.get_autocommit():
            # 如果没有自动开始，手动进行提交
            self.conn.commit()

        cursor.close()
        #记录日志
        logger.info(f'非查询sql：{sql}已经执行完成……')

    def execute_without_autocommit(self,sql):
        # 获取游标
        cursor = self.conn.cursor()
        cursor.execute(sql)
        logger.debug(f"执行了一条sql:{sql}")
        cursor.close()


    def query(self, sql):

        #1.创建游标
        cursor = self.conn.cursor()
        #2 执行sql语句
        cursor.execute(sql)
        #返回结果
        results =  cursor.fetchall()
        # 关闭游标
        cursor.close()

        logger.info(results)
        return results

    def check_table_exists(self,db_name,table_name):
        """

        :param db_name: 数据库名称
        :param table_name: 表名
        :return:
        """
        # 切换数据库
        self.select_db(db_name)
        results = self.query('show tables')

        return (table_name,)in results


    def create_table(self, db_name ,table_name ,create_cols):
        """

        :param db_name:数据库名称
        :param table_name:表名
        :param create_cols:字段名以及类型
        :return:
        """

        if not self.check_table_exists(db_name,table_name):

            create_sql = f"create table {table_name}({create_cols})"

            self.conn.select_db(db_name)
            self.execute(create_sql)

            logger.info(f"在数据库：{db_name}中创建了表：{table_name}完成，建表语句事：{create_cols}")
        else:
            logger.info(f"数据库：{db_name}中，表{table_name}已经存在，创建表的操作跳过")
        pass


    def close_conn(self):
        '''
        关闭数据库连接
        :return:
        '''
        if self.conn:
            self.conn.close()
            self.conn = None
        pass


# 这个函数是写在MYSQLUtil外面 和MySQL没有关系
# def get_processed_files(db_util,
#                         db_name = config.OlistETl_database,
#                         table_name = config.metadata_file_monitor_table_name,
#                         create_cols = config.metadata_file_monitor_table_create_cols):
#     """
#     获取处理过的文件名
#     :param db_util:MYsqlutil 实例对象
#     :param db_name: 数据库名称 实际上是metadata
#     :param table_name:元数据表名，实际上就是file_monitor
#     :param create_cols:建表语句中的列名和类型
#     :return:处理过的文件路径组成的列表
#     """
#     db_util.select_db(db_name)
#
#     if not db_util.cheack_table_exists(db_name, table_name):
#         db_util.create_table(db_name, table_name, create_cols)
#     else:
#         logger.debug(f'{table_name}存在，跳过建表语句')
#
#     # 查询元数据表中存的处理过的文件名
#     results = db_util.query(f'select file_name from {table_name}')
#     # results是一个元组
#
#     file_names = []
#     for result in results:
#         file_names.append(result[0])
#
#     return file_names
#     pass



if __name__ == '__main__':
    mysql_util = MySQLUtil()
    print(mysql_util.query('select * from test;'))
    mysql_util.select_db('retail')
    mysql_util.query('select database();')

    if not mysql_util.check_table_exists('metadata', 'test2'):
        mysql_util.check_table_exists_and_create('metadata', 'test2', 'name varchar(255), age int(3)')

    mysql_util.close_conn()



