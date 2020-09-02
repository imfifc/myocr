import time
import grpc
import multiprocessing
from concurrent import futures
from adder.secure import TimeValidator
from datetime import datetime
from ocr_structuring.settings import MyConfig
from ocr_structuring.utils.logging import logger
from adder.service import HealthServer, MetricsServer
from ocr_structuring.service.grpc_server import StructuringServer
from adder.protos import add_HealthServicer_to_server, add_MetricsServicer_to_server
from ocr_structuring.protos.structuring_pb2_grpc import add_StructuringServicer_to_server


def setup_grpc_server(port):
    cfg = MyConfig()
    grpc_server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=1),
        options=[
            ('grpc.max_receive_message_length', cfg.grpc_max_message_length.value),
            ('grpc.max_send_message_length', cfg.grpc_max_message_length.value)
        ],
        maximum_concurrent_rpcs=cfg.grpc_max_concurrent.value,
    )
    add_StructuringServicer_to_server(servicer=StructuringServer(), server=grpc_server)
    add_MetricsServicer_to_server(servicer=MetricsServer(cfg), server=grpc_server)
    add_HealthServicer_to_server(servicer=HealthServer(), server=grpc_server)
    grpc_server.add_insecure_port('[::]:%s' % port)
    grpc_server.start()
    logger.info('grpc server starts serving at %s' % port)
    return grpc_server


if __name__ == '__main__':
    config = MyConfig()
    multiprocessing.freeze_support()
    server = setup_grpc_server(config.grpc_port.value)
    validator = TimeValidator(datetime(year=2019, month=9, day=24), datetime(year=2029, month=9, day=25))
    try:
        while validator.validate():
            time.sleep(60)  # 1 分钟
        server.stop(0)
        while True:
            time.sleep(60 * 60 * 24)  # 1 天
    except KeyboardInterrupt:
        server.stop(0)
        logger.info('grpc server stop serving')
