#coding:utf-8
import logging
import logging.handlers
import logging.config
import sys,os
import getpass
import socket

"""
记录输入
1.命令
2.配置文件
3.从设备收集到的数据
"""

"""
2.使用配置文件和fileConfig()函数实现日志配置
"""

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
    def __init__(self):
        # log_dir = 'logs'
        # os.makedirs(log_dir, exist_ok=True)
        # self._log_dir = log_dir
        # self._log_name = log_name
        logging.config.fileConfig('logging_GUI.conf')
        # self.InputLogger = self.logger_input()
        # self.OutputLogger = self.logger_output()
        # self.LocalLogger = self.logger_local()
        self.GUILogger = self.logger_gui()


    # def set_logger(self):
    #     # 创建一个logger,可以考虑如何将它封装
    #     logger = logging.getLogger(self._log_name)
    #     logger.setLevel(logging.DEBUG)
    #     #创建一个handler，用于写入日志文件, 存 3 个日志，每个 10M 大小
    #     fh = logging.handlers.RotatingFileHandler(os.path.join(self._log_dir, self._log_name + '.log'),
    #                                               maxBytes=10*1024*1024, backupCount=3)
    #     fh.setLevel(logging.DEBUG)
    #     # 再创建一个handler，用于输出到控制台
    #     ch = logging.StreamHandler()
    #     ch.setLevel(logging.DEBUG)
    #     # 定义handler的输出格式
    #     formatter = logging.Formatter('%(asctime)s - %(module)s.%(funcName)s.%(lineno)d - '
    #                                   '%(levelname)s - %(message)s')
    #     fh.setFormatter(formatter)
    #     ch.setFormatter(formatter)
    #     # 给logger添加handler
    #     logger.addHandler(fh)
    #     logger.addHandler(ch)
    #     return logger

    def logger_input(self):
        # 创建一个日志器logger
        # fmt_input = logging.Formatter("%(asctime)s - %(name)s - %(CLI)s - %(username)s - %(message)s")
        # handle_input = logging.StreamHandler(sys.stdout)
        # handle_input.setFormatter(fmt_input)

        Logger_Input = logging.getLogger('cli_input')
        # Logger_Input.addHandler(handle_input)

        #%(asctime)s - [%(username)s] - [%(type)s] - [%(describe1)s] - [%(describe2)s] - [%(cmd)s]
        extra_dict = {"username": "USERNAME","type":"TYPE","describe1":"DESCRIBE","describe2":"DESCRIBE","cmd":"CMD"}

        # 获取一个自定义LoggerAdapter类的实例
        logger = MyLoggerAdapter(Logger_Input, extra_dict)
        return logger



    def logger_output(self):
        Logger_Output = logging.getLogger('cli_output')
        #%(asctime)s - %(name)s - %(levelname)s - %s(output) -  %(message)s
        extra_dict = {"result":"RESULT"}
        # 获取一个自定义LoggerAdapter类的实例
        logger = MyLoggerAdapter(Logger_Output, extra_dict)
        return logger

    def logger_local(self):
        logger_local = logging.getLogger('localmessage')
        extra_dict = {"path":"PATH","RES":"RES"}
        logger = MyLoggerAdapter(logger_local,extra_dict)
        return logger


    def logger_gui(self):
        logger_gui = logging.getLogger('gui')
        extra_dict = {"username": "USERNAME","type":"TYPE","describe1":"DESCRIBE","describe2":"DESCRIBE","data":"DATA"}
        logger = MyLoggerAdapter(logger_gui,extra_dict)
        return logger


class Collector(object):
    linstor_conf_path = '/etc/linstor/linstor-client.conf'

    def get_username(self):
        return getpass.getuser()

    def get_hostname(self):
        return socket.gethostname()

    def get_path(self):
        return os.getcwd()

    def get_linstor_controller(self,path):
        path = self.linstor_conf_path
        with open(path, 'r') as f:
            data = f.read()
            return data

#
# """
# 上下文实现方式
# """
#
#
#
# if __name__ == '__main__':
#     # 初始化一个要传递给LoggerAdapter构造方法的logger实例
#     fmt = logging.Formatter("%(asctime)s - %(name)s - %(ip)s - %(username)s - %(message)s")
#     h_console = logging.StreamHandler(sys.stdout)
#     h_console.setFormatter(fmt)
#     init_logger = logging.getLogger("myPro")
#     init_logger.setLevel(logging.DEBUG)
#     init_logger.addHandler(h_console)
#
#     # 初始化一个要传递给LoggerAdapter构造方法的上下文字典对象
#     extra_dict = {"ip": "IP", "username": "USERNAME"}
#
#     # 获取一个自定义LoggerAdapter类的实例
#     logger = MyLoggerAdapter(init_logger, extra_dict)
#
#     # 应用中的日志记录方法调用
#     logger.info("User Login!")
#     logger.info("User Login!", extra={"ip": "113.208.78.29", "username": "Petter"})
#     logger.info("User Login!")
#     logger.info("User Login!")
#
#
#
# #
# """
# 使用配置文件
# """
# from logging import config
#
# # 读取日志配置文件内容
# logging.config.fileConfig('logging.conf')
#
# # 创建一个日志器logger
# logger = logging.getLogger('simpleExample')
#
# # 日志输出
# logger.debug('debug message')
# logger.info('info message')
# logger.warning('warn message')
# logger.error('error message')
# logger.critical('critical message')
