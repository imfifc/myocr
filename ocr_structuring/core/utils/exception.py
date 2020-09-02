class StructuringException(Exception):
    pass


class NonTemplateException(StructuringException):
    pass


class TemplateException(StructuringException):
    pass


class ConfigException(TemplateException):
    def __init__(self, msg=""):
        print(msg)
