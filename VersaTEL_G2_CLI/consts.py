#coding:utf-8
"""
Global constants for vtel
"""
VERSION = "v0.8.0"


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


def init():
    global _GLOBAL_DICT
    _GLOBAL_DICT = {}
    _GLOBAL_DICT['LOG_ID'] = 0
    _GLOBAL_DICT['RPL'] = 'no'
    _GLOBAL_DICT['LOG_SWITCH'] = 'yes'

def set_value(key, value):
    """ 定义一个全局变量 """
    _GLOBAL_DICT[key] = value


def get_value(key, dft_val = None):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        return _GLOBAL_DICT[key]
    except KeyError:
        return dft_val


def set_glo_log(value):
    set_value('LOG', value)


def set_glo_db(value):
    set_value('LOG_DB', value)


def set_glo_rpl(value):
    set_value('RPL', value)


def set_glo_tsc_id(value):
    set_value('TSC_ID', value)


def set_glo_log_id(value):
    set_value('LOG_ID', value)


def set_glo_log_switch(value):
    set_value('LOG_SWITCH', value)


def set_glo_gui_tid(value):
    set_value('GUI_TID',value)



def glo_gui_tid():
    return get_value('GUI_TID')


def glo_log():
    return get_value('LOG')


def glo_db():
    return get_value('LOG_DB')


def glo_str():
    return get_value('STR')


def glo_rpl():
    return get_value('RPL')


def glo_tsc_id():
    return get_value('TSC_ID')


def glo_log_id():
    return get_value('LOG_ID')


def glo_log_switch():
    return get_value('LOG_SWITCH')


