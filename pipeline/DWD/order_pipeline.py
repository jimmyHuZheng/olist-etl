import pandas as pd
import numpy as np
from pipeline.base import BasePipeline
from datetime import datetime

class OrdersPipeline(BasePipeline):
    def transform(self,df:pd.DataFrame)  -> pd.DataFrame:

        """
          清洗步骤
          1. 去重
          2.字符串规范化
          3.时间类型统一与缺失填充
          4.配送时效衍生指标
          5.增加etl审计时间
          :param df:
          :return:
        """
        if df.empty:
            return df

        df = df.copy()

        # 1. 过滤核心主键缺失，并针对 order_id 进行去重
        df = df.dropna(subset=['order_id', 'customer_id'])
        df = df.drop_duplicates(subset=['order_id'], keep='last')

        # 2. 文本字段去空格并小写化
        str_cols = ['order_id', 'customer_id', 'order_status']
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.lower()

        # 3. 时间字段格式转换（无法解析的转为 NaT）
        time_cols = [
            'order_purchase_timestamp',
            'order_approved_at',
            'order_delivered_carrier_date',
            'order_delivered_customer_date',
            'order_estimated_delivery_date'
        ]
        for col in time_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # 4. 派生电商分析关键指标
        # 4.1 实际履约配送时长（天）
        delivery_delta = df['order_delivered_customer_date'] - df['order_purchase_timestamp']
        df['actual_delivery_days'] = delivery_delta.dt.total_seconds() / 86400

        # 4.2 预估配送时长（天）
        estimated_delta = df['order_estimated_delivery_date'] - df['order_purchase_timestamp']
        df['estimated_delivery_days'] = estimated_delta.dt.total_seconds() / 86400

        # 4.3 是否延迟送达（1：延迟，0：准时，None：未送达）
        df['is_delayed'] = np.where(
            df['order_delivered_customer_date'].notnull() & df['order_estimated_delivery_date'].notnull(),
            (df['order_delivered_customer_date'] > df['order_estimated_delivery_date']).astype(int),
            None
        )

        # 5. 数仓审计字段
        df['dw_create_time'] = datetime.now()
        return df


