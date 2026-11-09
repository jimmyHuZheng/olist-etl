import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

from pipeline.base import BasePipeline


class ProductPipeline(BasePipeline):
    target_layer = "dim" # 声明自己去 dim层


    def transform(self,df:pd.DataFrame) ->  pd.DataFrame:
        print("来到了dim清洗层")
        return df