# coding:utf-8
import logging
import logging.handlers
import logging.config
from functools import wraps
import traceback
import sys
import os
import getpass
import socket




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
    fmt = logging.Formatter("%(asctime)s [%(username)s] [%(type)s] [%(transaction_id)s] [%(describe1)s] [%(describe2)s] [%(data)s]",datefmt = '[%Y/%m/%d%H:%M:%S]')
    handler_input = logging.handlers.RotatingFileHandler(filename='VersaTEL_G2_CLI.log',mode='a',maxBytes=10*1024*1024,backupCount=5)
    handler_input.setFormatter(fmt)
    def __init__(self,username,transaction_id):
        # log_dir = 'logs'
        # os.makedirs(log_dir, exist_ok=True)
        # self._log_dir = log_dir
        # self._log_name = log_name
        # logging.config.fileConfig('logging_CLI.conf')
        self.username = username
        self.transaction_id = transaction_id
        # self.InputLogger = self.logger_input()
        # self.OutputLogger = self.logger_output()
        # self.LocalLogger = self.logger_local()
        # self.GUILogger = self.logger_gui() # GUI only, temporarily stored


    def logger_input(self):
        Logger_cli = logging.getLogger('cli_input')
        Logger_cli.addHandler(self.handler_input)
        Logger_cli.setLevel(logging.DEBUG)
        # %(asctime)s - [%(username)s] - [%(type)s] - [%(describe1)s] - [%(describe2)s] - [%(data)s]
        extra_dict = {
            "username": "USERNAME",
            "type": "TYPE",
            "transaction_id":"",
            "describe1": "",
            "describe2": "",
            "data": ""}
        # 获取一个自定义LoggerAdapter类的实例
        logger = MyLoggerAdapter(Logger_cli, extra_dict)
        return logger

    def logger_output(self):
        Logger_Output = logging.getLogger('cli_output')
        # %(asctime)s - [%(username)s] - [%(type)s] - [%(describe1)s] - [%(describe2)s] - [%(data)s]
        extra_dict = {
            "username": "USERNAME",
            "type": "TYPE",
            "transaction_id": "",
            "describe1": "",
            "describe2": "",
            "data": ""}
        # 获取一个自定义LoggerAdapter类的实例
        logger = MyLoggerAdapter(Logger_Output, extra_dict)
        return logger

    def logger_local(self):
        logger_local = logging.getLogger('localmessage')
        extra_dict = {"path": "PATH", "RES": "RES"}
        logger = MyLoggerAdapter(logger_local, extra_dict)
        return logger

    # GUI only, temporarily stored here
    def logger_gui(self):
        logger_gui = logging.getLogger('gui')
        extra_dict = {
            "username": "USERNAME",
            "type": "TYPE",
            "transaction_id": "",
            "describe1": "",
            "describe2": "",
            "data": "DATA"}
        logger = MyLoggerAdapter(logger_gui, extra_dict)
        return logger


    # write to log file
    def write_to_log(self,type,describe1,describe2,data):
        InputLogger = self.logger_input()
        # InputLogger.logger.removeHandler(self.handler_input)
        InputLogger.debug(
            '',
            extra={
                'username': self.username,
                'type': type,
                'transaction_id': self.transaction_id,
                'describe1': describe1,
                'describe2': describe2,
                'data': data})



# 放置到sundry模块中去了
# class Collector(object):
#     linstor_conf_path = '/etc/linstor/linstor-client.conf'
#
#     def get_username(self):
#         return getpass.getuser()
#
#     def get_hostname(self):
#         return socket.gethostname()
#
#     # Get the path of the program
#     def get_path(self):
#         return os.getcwd()
#
#     # Get LISNTOR controller configuration file information
#     def get_linstor_controller(self, path):
#         path = self.linstor_conf_path
#         with open(path, 'r') as f:
#             data = f.read()
#             return data