# 工厂模式 作用是 策略注册中心

# 以后增加了新 pipeline 直接在这里导：
from pipeline.DWD.order_pipeline import OrdersPipeline
from pipeline.DIM.product_pipeline import ProductPipeline

class PipelineFactory:
    """
    Pipeline 注册与获取工厂
    解耦主入口，后续新增清洗规则只需要在此字典中配置

    """
    _PIPELINE_MAP={
        "orders":OrdersPipeline,
        "product":ProductPipeline,
        #这里添加就可以了
    }

    @classmethod
    def get_pipeline(cls,table_name:str):
        """
        根据表名动态获取对应的Pipeline实例
        如果该表尚未开发专用清洗规则，返回None
        :param table_name:
        :return:
        """
        pipeline_cls =cls._PIPELINE_MAP.get(table_name)
        if pipeline_cls:
            return pipeline_cls()
        return None

    @classmethod
    def get_supported_table(cls):
        """获取当前已支撑清洗的所有表名列表"""
        return list(cls._PIPELINE_MAP.keys())