#coding:utf-8
"""
Global constants for vtel
"""
VERSION = 'v1.2.0-RC'


class ExitCode(object):
    OK = 0
    UNKNOWN_ERROR = 1
    ARGPARSE_ERROR = 2
    OBJECT_NOT_FOUND = 3
    OPTION_NOT_SUPPORTED = 4
    ILLEGAL_STATE = 5
    CONNECTION_ERROR = 20
    CONNECTION_TIMEOUT = 21
    UNEXPECTED_REPLY = 22
    API_ERROR = 10
    NO_SATELLITE_CONNECTION = 11


class ReplayExit(Exception):
    "replay时，输出日志中的异常信息后，此次replay事务也随之停止"
    pass


class CmdError(Exception):
    "执行命令出错"
    pass
