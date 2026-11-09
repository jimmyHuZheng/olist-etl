import config.olist_config as conf
import pandas as pd
import time
import traceback
import sys

from util.dingtalk_util import DingTalkUtil
from util.mysql_util import MySQLUtil
from util.read_file_util import FileUtil
from util.email_util import EmailUtil
from util.logging_util import init_logger
from pipeline.pipeline_factory import PipelineFactory

# olist入口函数
def run_etl():
    # 1.

    income_path = conf.income_data_path  # income/ 存放下载的原始文件
    archive_path = conf.archive_data_path  # archive/ 成功后存放
    failed_path = conf.failed_data_path  # failed/ 失败时存放
    logging_path = conf.failed_log  # logging/ 存放运行日志

    # 实例化
    logger = init_logger()
    fu = FileUtil()
    mu = MySQLUtil()

    file_list = fu.get_dir_files_list(income_path)

    db_name = conf.OlistETl_database

    """清洗特殊字符，避免在 f-string 大括号中使用反斜杠报错"""
    def clean_val(val):
        s = str(val) if val is not None else ""
        s = s.replace("\\", "\\\\").replace("'", "''")
        return f"'{s}'"

    # 开始循环文件夹里面的所有文件
    for file_path in file_list:
        # 获取表名
        stem = fu.get_table_name_from_file(file_path)
        # 从右往左按照 '_' 切割 1 次，取第 0 个元素
        table_name = stem.rsplit('_', 1)[0]

        ods_table ="ods_"+table_name
        # dwd_table ="dwd_"+table_name
        # dim_table ="dim_"+table_name

        print(f"表名为：{table_name}")
        cols, rows = fu.read_file_data(file_path)
        print(f"：{cols},列：{rows}")

        #如果没有内容 就不执行循环
        if not rows:
            logger.info(f"{table_name}没有内容，跳过")
            continue

        # 如果不存在 需要创建对应的表
        if not mu.check_table_exists(db_name,ods_table):

            # 1. 业务字段全部给 TEXT
            col_definitions = [f"`{col}` TEXT" for col in cols]

            # 2. 末尾追加三个元数据字段
            col_definitions.append("`create_time` DATETIME DEFAULT CURRENT_TIMESTAMP")
            col_definitions.append("`update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            col_definitions.append("`source_filename` VARCHAR(255)")

            create_cols_str = ", ".join(col_definitions)

            # 3. 调用你的 mysql_util 建表
            mu.create_table(db_name, ods_table, create_cols_str)
            logger.info(f"表 {ods_table} 自动创建完成！")

        try:
            #显性开启事务
            mu.execute_without_autocommit("start transaction")

            #--------------------插入到mysql里 根据表名 插入到指定的表里:数仓 ODS 层（原始数据层） 的建表，规范做法是将业务字段全部统一设为 TEXT（或较长长度的 VARCHAR）---------------------------
            # 2.1 组装字段名
            col_names = ', '.join([f"`{col}`" for col in cols]) + ", `source_filename`"

            #2.2 分批过招并执行批量插入（每批2000条）

            batch_size = 2000
            total_rows = len(rows)
            logger.info(f"开始向{ods_table}插入数据，共{total_rows}条…………")


            #2.3 一次2000条执行
            for i in range(0, total_rows, batch_size):
                chunk = rows[i: i + batch_size]
                val_rows = []
                for row in chunk:
                    # 处理单引号喝反斜杠转义，避免拼 SQL 时报错
                    escaped_vals = [clean_val(v) for v in row]
                    escaped_vals.append(clean_val(stem))
                    val_rows.append(f"({', '.join(escaped_vals)})")

                batch_sql = f"INSERT INTO `{db_name}`.`{ods_table}` ({col_names}) VALUES {', '.join(val_rows)};"
                mu.execute_without_autocommit(batch_sql)
            logger.info(f"表 {ods_table} 数据内存插入完成，成功写入 {total_rows} 条记录！")


        # 3.根据表名 进行清洗 策略模式 然后进行插入到mysql中dwd表中 这个dwd表是唯一主键的

            #3.1 匹配对应策略
            matched_pipeline = PipelineFactory.get_pipeline(table_name)
            logger.info(f"已选取到了指定的清洗方法")

            if not matched_pipeline:
                logger.warning(f"未找到表 {table_name} 对应的清洗策略 Pipeline，跳过 DWD 清洗")
            else:

                logger.info(f"开始执行 {table_name} 的 DWD 清洗策略...")

                #3.2 将内存中的 cols 和 rows 转为 DataFrame 进行加工
                raw_df = pd.DataFrame(rows, columns=cols)

                #3.3 执行策略清洗（对应你的 BasePipeline.transform）
                clean_df = matched_pipeline.transform(raw_df)

                # 3.4 检查/创建 DWD 表，并写入数据（对应你的 BasePipeline.load）
                #target_table = dwd_table  # 默认入 DWD，如为维度表可在策略内动态调整为 dim_table

                target_table =f"{matched_pipeline.target_layer}_{table_name}"
                matched_pipeline.load(clean_df, target_table,mu, db_name, 2000) #这里进行清洗
                logger.info(f"表 {target_table} 数据清洗并入库完成，有效数据 {len(clean_df)} 条！")

            #-----------------------第4步：两者都无报错，全盘提交！----------------------------------
            mu.execute("COMMIT;")
            logger.info(f"【成功】文件 {stem} 处理完毕，ODS 与 DWD 事务已统一提交！")

            #----------------------第5步：income文件成功流转至 archive目录--------------------------
            dest = fu.move_file(file_path,archive_path)
            logger.info(f"文件已归档: {file_path} -> {dest}")

        except Exception as e:
            mu.execute("ROLLBACK;")
            logger.error(f"【失败回滚】处理文件 {stem} 发生异常，已执行事务回滚（ODS和DWD均未生效）: {str(e)}")

            #---------------------第5.2 失败流转：移动到failed目录
            dest = fu.move_file(file_path,failed_path)
            logger.info(f"错误文件已隔离：{file_path}->{dest}")


    # 整体文件循环结束后关闭数据
    mu.close_conn()
    logger.info('=================已关闭连接！=================')


if __name__ == '__main__':
    # 1. 实例化邮件通知工具
    mailer = EmailUtil(
        sender_email = conf.email_send,
        auth_code = conf.email_auth_code,
        receiver_emails = conf.email_receicers
    )
    task_name = "Olist-ETL 每日定时任务"

    start_time = time.time()
    try:
        # 2. 执行 ETL 核心逻辑
        run_etl()

        # 3. 成功报平安
        cost_time = time.time() - start_time
        mailer.send_success_email(
            task_name= task_name,
            duration= cost_time,
            detail=" 各文件已正常读取并成功写入 MySQL (ODS & DWD)。"
        )
        sys.exit(0)

    except Exception:
        # 4. 失败立即告警，发送完整报错堆栈
        err_detail = traceback.format_exc()
        mailer.send_failure_email(task_name=task_name, error_msg=err_detail)
        sys.exit(1)