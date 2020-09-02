import logging
from adder import Config, StringField, IntField


class MyConfig(Config):
    log_level = IntField('LOG_LEVEL', f'{logging.DEBUG}')
    tfidf_classes_config = StringField('TFIDF_CLASSES_CONFIG', 'all')

    grpc_port = StringField('GRPC_PORT', '50051')
    grpc_max_message_length = IntField('GRPC_MAX_MESSAGE_LENGTH', '104857600')  # 100M
    grpc_max_concurrent = IntField('GRPC_MAX_CONCURRENT', None)
    ner_ip_addr = StringField('NER_IP','172.18.192.17')
    ner_port_in = IntField('NER_PORT_IN',32767)
    ner_port_out = IntField('NER_PORT_OUT',31801)
