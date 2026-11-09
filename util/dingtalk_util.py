import time
import hmac
import hashlib
import base64
import urllib.parse
import requests


class DingTalkUtil:
    def __init__(self, webhook: str, secret: str = None):
        """
        :param webhook: 钉钉机器人的完整 webhook 地址
        :param secret: 加签安全设置的密钥 (如果勾选了加签则必填)
        """
        self.webhook = webhook
        self.secret = secret

    def _get_signed_url(self) -> str:
        """ 如果配置了加签密钥，计算签名并拼接到 URL"""
        if not self.secret:
            return self.webhook

        timestamp  = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        sep = "&" if "?" in self.webhook else "?"
        return f"{self.webhook}{sep}timestamp={timestamp}&sign={sign}"

    def send_markdown(self,title:str, text:str):
        """发送 Markdown 格式的消息"""
        url =  self._get_signed_url()
        headers = {"Content-Type": "application/json"}
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            }
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            result = resp.json()
            if result.get("errcode") != 0:
                print(f"[DingTalk] 发送失败: {result.get('errmsg')}")
        except Exception as e:
            print(f"[DingTalk] 请求异常: {e}")


    def send_success_message(self, task_name:str,duration:float,detail:str = ""):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        markdown_text = f"""###  【ETL 运行成功通知】
        ---
        * **任务名称**：{task_name}
        * **结束时间**：{now}
        * **执行耗时**：{duration:.2f} 秒
        * **执行说明**：{detail if detail else "所有文件已成功入库并清洗完成"}
        """
        self.send_markdown(title=f"✅ {task_name} 执行成功", text=markdown_text)

    def send_failure_msg(self, task_name: str, error_msg: str):
        """失败立即告警通知"""
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        markdown_text = f"""###  【ETL 运行失败告警】
         ---
         * **任务名称**：{task_name}
         * **报错时间**：{now}
         * **错误详情**：
         ```text
         {error_msg[-800:]}
         """
        self.send_markdown(title=f"❌ {task_name} 执行失败", text=markdown_text)