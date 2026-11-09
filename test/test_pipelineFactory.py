from unittest import TestCase
from pipeline.pipeline_factory import PipelineFactory



class TestReadFileUtil(TestCase):

    def setUp(self) ->None:
        pass


    def test_process(self) ->None:
        pipeline = PipelineFactory.get_pipeline("orders")

        if not pipeline:
            print("表 orders 暂未配置清洗 Pipeline，跳过 DWD 清洗.")


        print(pipeline)




    def tearDown(self) -> None:
        pass