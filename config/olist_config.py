# 用来配置olist商城的sql
import time


############################ 配置olist日志的位置 #########################################
# 日志存储路径
log_root_path = './generate_logs'
log_name = f'pyetl-{time.strftime("%Y%m%d-%H",time.localtime(time.time()))}.log'
level = 10


############### MYSQLUtil 配置###########################
"""
olist-etl数据库
"""
OlistETl_host = 'your_localhost'
OlistETl_user = 'your_user'
OlistETl_password = 'your_password'
OlistETl_port = 3306
OlistETl_database = 'olist-etl'


#################### 指定文件读取所有文件列表路径 ############################
income_data_path =r"your_path\income"
archive_data_path = r"your_path\archive"
failed_data_path = r"your_path\failed"
failed_log = r"your_path\log"


########################### 钉钉密钥 #################################
DINGTALK_WEBHOOK=""
DINGTALK_SECRET=""


########################## 邮箱信息 ####################################
email_send = "发件人qq邮箱@qq.com"  # 发件人qq邮箱
email_auth_code = "16位SMTP授权码"              # 16位SMTP授权码
email_receicers = [
    "发件人qq邮箱@qq.com"           #发给自己一份留存
    "收件人qq邮箱@qq.com"
]
