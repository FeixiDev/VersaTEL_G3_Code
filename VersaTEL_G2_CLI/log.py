# coding:utf-8
import logging
import logging.handlers
import logging.config
import consts
import sundry




LOG_PATH = './'
# LOG_PATH = '/var/log/vtel/'
CLI_LOG_NAME = 'cli.log'
WEB_LOG_NAME = 'web.log'


class MyLoggerAdapter(logging.LoggerAdapter):
    """
    实现一个LoggerAdapter的子类，重写process()方法。
    其中对于kwargs参数的操作应该是先判断其本身是否包含extra关键字，如果包含则不使用默认值进行替换；
    如果kwargs参数中不包含extra关键字则取默认值。
    """

    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs["extra"] = self.extra
        return msg, kwargs


class Log(object):
    def __init__(self, user, tid,file_name=CLI_LOG_NAME):
        """
        日志格式：
        asctime：时间
        tid：transaction id，事务的唯一标识
        user：username，操作系统的用户
        t1：type1，日志数据的类型一
        t2：type2，日志数据的类型二
        d1：description1，日志数据的描述一
        d2：description2，日志数据的描述二
        data：具体的结果或者数据

        :param user:
        :param tid:
        :param file_name:
        """
        fmt = logging.Formatter(
            "%(asctime)s [%(tid)s] [%(user)s] [%(t1)s] [%(t2)s] [%(d1)s] [%(d2)s] [%(data)s]|",
            datefmt='[%Y/%m/%d %H:%M:%S]')
        self.handler_input = logging.handlers.RotatingFileHandler(filename=f'{LOG_PATH}{file_name}', mode='a',
                                                             maxBytes=10*1024*1024, backupCount=20)
        self.handler_input.setFormatter(fmt)
        self.user = user
        self.tid = tid

    def logger_input(self):
        vtel_logger = logging.getLogger('vtel_logger')
        vtel_logger.addHandler(self.handler_input)
        vtel_logger.setLevel(logging.DEBUG)
        extra_dict = {
            "user": "USERNAME",
            "tid": "",
            "t1": "TYPE1",
            "t2": "TYPE2",
            "d1": "",
            "d2": "",
            "data": ""}
        # 获取一个自定义LoggerAdapter类的实例
        logger = MyLoggerAdapter(vtel_logger, extra_dict)
        return logger

    # write to log file
    def write_to_log(self, t1, t2, d1, d2, data):
        vtel_logger = self.logger_input()

        # 获取到日志开关变量为'no'时，移除处理器，不再将数据记录到文件中
        if consts.glo_log_switch() == 'no':
            vtel_logger.logger.removeHandler(self.handler_input)
        vtel_logger.debug(
            '',
            extra={
                'user': self.user,
                'tid': self.tid,
                't1': t1,
                't2': t2,
                'd1': d1,
                'd2': d2,
                'data': data})

