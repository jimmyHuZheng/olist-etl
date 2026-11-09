import os
import smtplib
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

# 清除环境变量代理，保证直连
for env_key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(env_key, None)


class EmailUtil:
    def __init__(self, sender_email: str, auth_code: str, receiver_emails: list):
        self.smtp_server = "smtp.qq.com"
        self.sender = sender_email.strip()
        self.auth_code = auth_code.strip()
        self.receivers = receiver_emails if isinstance(receiver_emails, list) else [receiver_emails]

    def _send_email(self, subject: str, html_content: str):
        message = MIMEText(html_content, 'html', 'utf-8')

        # 核心修复点：标准 RFC 格式构造 From
        sender_nickname = "ETL数据监控中心"
        message['From'] = formataddr((Header(sender_nickname, 'utf-8').encode(), self.sender))
        message['To'] = ",".join(self.receivers)
        message['Subject'] = Header(subject, 'utf-8')

        # 优先使用 587 端口 + STARTTLS
        server = None
        try:
            server = smtplib.SMTP(self.smtp_server, 587, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender, self.auth_code)
            server.sendmail(self.sender, self.receivers, message.as_string())
            print("[Email] 邮件发送成功！(通过 587 端口)")
            return
        except Exception as e587:
            print(f"[Email] 587 端口发送失败 ({e587})，正在尝试 465 SSL 端口重试...")
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

        # 备选使用 465 端口 SSL
        server_ssl = None
        try:
            server_ssl = smtplib.SMTP_SSL(self.smtp_server, 465, timeout=15)
            server_ssl.login(self.sender, self.auth_code)
            server_ssl.sendmail(self.sender, self.receivers, message.as_string())
            print("[Email] 邮件发送成功！(通过 465 端口)")
            return
        except Exception as e465:
            print(f"[Email] 邮件最终发送失败: {e465}")
            raise e465
        finally:
            if server_ssl:
                try:
                    server_ssl.quit()
                except Exception:
                    pass

    def send_success_email(self, task_name: str, duration: float, detail: str = ""):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"【ETL成功】{task_name} 执行完毕 - {now[:10]}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
            <h2 style="color: #28a745; margin-top: 0;">✅ {task_name} 执行成功</h2>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p><strong>完成时间：</strong> {now}</p>
            <p><strong>执行耗时：</strong> {duration:.2f} 秒</p>
            <p><strong>任务状态：</strong> <span style="color: #28a745; font-weight: bold;">成功</span></p>
            <p><strong>详细说明：</strong> {detail if detail else "数据已顺利入库至 ODS 并完成 DWD 清洗转换。"}</p>
        </div>
        """
        self._send_email(subject, html_content)

    def send_failure_email(self, task_name: str, error_msg: str):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"【紧急告警】{task_name} 执行异常！"

        formatted_error = error_msg.replace('\n', '<br>').replace(' ', '&nbsp;')

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; border: 1px solid #f5c6cb; border-radius: 8px; padding: 20px; background-color: #fffafb;">
            <h2 style="color: #dc3545; margin-top: 0;">❌ {task_name} 任务中断告警</h2>
            <hr style="border: 0; border-top: 1px solid #f5c6cb;">
            <p><strong>发生时间：</strong> {now}</p>
            <p><strong>任务状态：</strong> <span style="color: #dc3545; font-weight: bold;">失败 / 异常退出</span></p>
            <p><strong>异常日志详情：</strong></p>
            <div style="background-color: #f8f9fa; border: 1px solid #ddd; padding: 10px; border-radius: 4px; font-family: Consolas, monospace; font-size: 13px; color: #333; overflow-x: auto;">
                {formatted_error}
            </div>
            <p style="color: #666; font-size: 12px; margin-top: 15px;">提示：请及时登录服务器排查日志与数据库连接状态。</p>
        </div>
        """
        self._send_email(subject, html_content)