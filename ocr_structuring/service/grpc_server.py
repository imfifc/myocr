import json
import threading
import traceback
from datetime import datetime
from ..protos.structuring_pb2 import StructuringResponse
from ..protos.structuring_pb2_grpc import StructuringServicer
from ..protos.structuring_pb2 import StructuringTimeInfo


class StructuringServer(StructuringServicer):
    request_processor = None
    lock = threading.Lock()

    def Process(self, request, context):
        try:
            if self.request_processor is None:
                with self.lock:
                    if self.request_processor is None:
                        from .request_processor import RequestProcessor
                        self.request_processor = RequestProcessor()
        except Exception as e:
            traceback.print_exc()
            return StructuringResponse(
                code=500000,
                message='%s: %s' % (e, traceback.format_exc())
            )
        response = StructuringResponse(code=500001, message='NOT_IMPLEMENTED')
        start_time = datetime.now()

        try:
            structuring_data = self.request_processor.process(
                request, "Process"
            )

            response = StructuringResponse(
                code=0,
                message='ok',
                data=json.dumps(structuring_data['data'], default=lambda obj: obj.__dict__),
                meta=json.dumps(structuring_data['metadata']),
            )
            return
        except BaseException as e:
            response = StructuringResponse(
                code=500000,
                message='%s: %s' % (e, traceback.format_exc())
            )
            traceback.print_exc()
            return
        finally:
            response.time_info.CopyFrom(StructuringTimeInfo(
                elapsed_time=int((datetime.now() - start_time).total_seconds() * 10 ** 9)
            ))
            return response

    def ProcessRotated(self, request, context):
        if self.request_processor is None:
            from .request_processor import RequestProcessor
            self.request_processor = RequestProcessor()
        response = StructuringResponse(code=500001, message='NOT_IMPLEMENTED')
        start_time = datetime.now()
        try:
            structuring_data = self.request_processor.process(
                request, "ProcessRotated"
            )

            response = StructuringResponse(
                code=0,
                message='ok',
                data=json.dumps(structuring_data['data'], default=lambda obj: obj.__dict__),
                meta=json.dumps(structuring_data['metadata']),
            )
            return
        except BaseException as e:
            response = StructuringResponse(
                code=500000,
                message='%s: %s' % (e, traceback.format_exc())
            )
            traceback.print_exc()
            return
        finally:
            response.time_info.CopyFrom(StructuringTimeInfo(
                elapsed_time=int((datetime.now() - start_time).total_seconds() * 10 ** 9)
            ))
            return response

    def ProcessMultiImage(self, request, context):
        if self.request_processor is None:
            from .request_processor import RequestProcessor
            self.request_processor = RequestProcessor()
        response = StructuringResponse(code=500001, message='NOT_IMPLEMENTED')
        start_time = datetime.now()
        try:
            structuring_data = self.request_processor.process(
                request, "ProcessMultiImage"
            )

            response = StructuringResponse(
                code=0,
                message='ok',
                data=json.dumps(structuring_data['data'], default=lambda obj: obj.__dict__),
                meta=json.dumps(structuring_data['metadata']),
            )
            return
        except BaseException as e:
            response = StructuringResponse(
                code=500000,
                message='%s: %s' % (e, traceback.format_exc())
            )
            traceback.print_exc()
            return
        finally:
            response.time_info.CopyFrom(StructuringTimeInfo(
                elapsed_time=int((datetime.now() - start_time).total_seconds() * 10 ** 9)
            ))
            return response
