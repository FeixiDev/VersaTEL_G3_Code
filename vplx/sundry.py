# coding:utf-8
import time
import os
import traceback
import re
import prettytable
import sys
import subprocess
from functools import wraps
import colorama as ca
import json
import readline
import math

import consts
# from public import log
import log
from replay import Replay,LogDB


def deco_record_exception(func):
    """
    Decorator
    Get exception, throw the exception after recording
    :param func:Command binding function
    """
    def wrapper(self,*args):
        try:
            return func(self,*args)
        except Exception as e:
            logger = log.Log()
            logger.write_to_log('DATA','DEBUG','exception','', str(traceback.format_exc()))
            raise e
    return wrapper


def deco_comfirm_del(type):
    """
    Decorator providing confirmation of deletion function.
    :param func: Function to delete linstor resource
    """
    def decorate(func):
        def wrapper(self,*args):
            cli_args = args[0]
            if cli_args.yes:
                func(self,*args)
            else:
                print(f"Are you sure you want to delete this {type}? If yes, enter 'y/yes'")
                answer = get_answer()
                # answer = 'y'
                if answer in ['y', 'yes']:
                    func(self,*args)
                else:
                    prt_log('Delete canceled',0)
        return wrapper
    return decorate


def get_answer():
    logger = log.Log()
    replay_mode = Replay.switch

    if replay_mode:
        logdb = LogDB()
        time,answer = logdb.get_anwser()
        if not time:
            time = ''
        list_rd = [time, '<input> user', answer]
        Replay.replay_data.append(list_rd)
    else:
        answer = input()
        logger.write_to_log('DATA', 'INPUT', 'confirm_input', 'confirm deletion', answer)

    return answer





# Get the path of the program
def get_path():
    return os.getcwd()


def re_findall(re_string, tgt_string):
    logger = log.Log()
    re_ = re.compile(re_string)
    oprt_id = log.create_oprt_id()
    logger.write_to_log('OPRT', 'REGULAR', 'findall', oprt_id, {'re': re_, 'string': tgt_string})
    re_result = re_.findall(tgt_string)
    logger.write_to_log('DATA', 'REGULAR', 'findall', oprt_id, re_result)
    return re_result


def re_search(re_string, tgt_stirng,output_type='group'):
    logger = log.Log()
    re_ = re.compile(re_string)
    oprt_id = log.create_oprt_id()
    logger.write_to_log('OPRT','REGULAR','search',oprt_id, {'re':re_,'string':tgt_stirng})
    re_result = re_.search(tgt_stirng)
    if re_result:
        if output_type == 'group':
            re_result = re_result.group()
        else:
            re_result = re_result.groups()
    logger.write_to_log('DATA', 'REGULAR', 'search', oprt_id, re_result)
    return re_result



def make_table(list_header,list_data):
    table = prettytable.PrettyTable()
    table.field_names = list_header
    if list_data:
        for i in list_data:
            table.add_row(i)
    return table



def deco_cmd(type):
    """
    装饰器
    用于装饰系统命令的执行
    :param type: 系统命令的类型(sys,linstor,crm)
    :return:返回命令执行结果
    """

    def decorate(func):
        @wraps(func)
        def wrapper(cmd):
            RPL = Replay.switch
            oprt_id = log.create_oprt_id()
            func_name = traceback.extract_stack()[-2][2]  # 装饰器获取被调用函数的函数名
            if not RPL:
                logger = log.Log()
                logger.write_to_log('DATA', 'STR', func_name, '', oprt_id)
                logger.write_to_log('OPRT', 'CMD', type, oprt_id, cmd)
                result_cmd = func(cmd)
                logger.write_to_log('DATA', 'CMD', type, oprt_id, result_cmd)
                return result_cmd
            else:
                logdb = LogDB()
                id_result = logdb.get_id(func_name)
                cmd_result = logdb.get_oprt_result()

                if type != 'sys' and cmd_result['result']:
                    result = eval(cmd_result['result'])
                    result_replay = result['rst']
                else:
                    result = cmd_result['result']
                    result_replay = cmd_result['result']


                if cmd == 'crm configure show | cat' or \
                   cmd == 'linstor --no-color --no-utf8 n l' or \
                   cmd == 'linstor --no-color --no-utf8 r lv' or \
                   cmd == 'linstor --no-color --no-utf8 sp l':
                    if Replay.mode == 'LITE':
                        Replay.specific_data.update({Replay.num: result_replay})
                        result_replay = f'...({Replay.num})'
                        Replay.num += 1


                list_rd1 = [id_result['time'],'<cmd>cmd',cmd]
                if not result_replay:
                    list_rd2 = [cmd_result['time'], '<cmd>result', result]
                else:
                    list_rd2 = [cmd_result['time'], '<cmd>result', result_replay.replace('\t', '')]

                Replay.replay_data.append(list_rd1)
                Replay.replay_data.append(list_rd2)

            return result
        return wrapper
    return decorate


def deco_json(str):
    """
    Decorator providing confirmation of deletion function.
    :param func: Function to delete linstor resource
    """
    def decorate(func):
        @wraps(func)
        def wrapper(self, *args):
            RPL = Replay.switch
            if not RPL:
                logger = log.Log()
                oprt_id = log.create_oprt_id()
                logger.write_to_log('DATA', 'STR', func.__name__, '', oprt_id)
                logger.write_to_log('OPRT', 'JSON', func.__name__, oprt_id, args)
                result = func(self,*args)
                logger.write_to_log('DATA', 'JSON', func.__name__, oprt_id,result)
            else:
                logdb = LogDB()
                id_result = logdb.get_id(func.__name__)
                json_result = logdb.get_oprt_result()
                if json_result['result']:
                    result = eval(json_result['result'])
                else:
                    result = ''
                result_replay = json.dumps(result, indent=2)

                if str == 'read json' or str == 'commit data':
                    str_opertion = str
                    if Replay.mode == 'LITE':
                        Replay.specific_data.update({Replay.num:result_replay})
                        result_replay = f'...({Replay.num})'
                        Replay.num += 1
                elif str == 'check key' or str == 'check value':
                    str_opertion = f'check "{args[1]}" in "{args[0]}"'
                elif str == 'check if it is used':
                    str_opertion = f'check "{args[2]}" in "{args[0]}" of "{args[1]}"'
                elif str == 'update data' or str == 'update all data' or str == 'delete data':
                    str_opertion = str
                    func(self,*args)
                else:
                    str_opertion = str

                list_rd = [id_result['time'],f'<JSON>{str_opertion}',result_replay]
                Replay.replay_data.append(list_rd)
            return result
        return wrapper
    return decorate


@deco_cmd('sys')
def execute_cmd(cmd, timeout=60):
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT,
                         stdout=subprocess.PIPE, shell=True)
    t_beginning = time.time()
    seconds_passed = 0
    while True:
        if p.poll() is not None:
            break
        seconds_passed = time.time() - t_beginning
        if timeout and seconds_passed > timeout:
            p.terminate()
            raise TimeoutError(cmd, timeout)
        time.sleep(0.1)
    output = p.stdout.read().decode()
    return output




def prt(str_, warning_level=0):
    if isinstance(warning_level, int):
        warning_str = '*' * warning_level
    else:
        warning_str = ''

    RPL = Replay.switch

    if not RPL:
        print(str(str_))
    else:
        db = LogDB()
        data = db.get_cmd_output()
        if not data["time"]:
            data["time"] = ''

        list_rd1 = [data['time'], '<Log Output>', data["output"]]
        list_rd2 = ['/','<This Output>',str_]
        Replay.replay_data.append(list_rd1)
        Replay.replay_data.append(list_rd2)

def prt_log(str_, warning_level):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    logger = log.Log()
    RPL = Replay.switch
    prt(str_, warning_level)

    if warning_level == 0:
        logger.write_to_log('INFO', 'INFO', 'finish', 'output', str_)
    elif warning_level == 1:
        logger.write_to_log('INFO', 'WARNING', 'fail', 'output', str_)
    elif warning_level == 2:
        logger.write_to_log('INFO', 'ERROR', 'exit', 'output', str_)
        if not RPL:
            sys.exit()
        else:
            raise consts.ReplayExit


def deco_color(func):
    """
    装饰器，给特定的linstor数据进行着色
    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args):
        status_true = ['UpToDate', 'Online','ONLINE', 'Ok', 'InUse']
        data = func(*args)
        for lst in data:
            if lst[-1] in status_true:
                lst[-1] = ca.Fore.GREEN + lst[-1] + ca.Style.RESET_ALL
            else:
                lst[-1] = ca.Fore.RED + lst[-1] + ca.Style.RESET_ALL
        return data
    return wrapper




def deco_db_insert(func):
    @wraps(func)
    def wrapper(self, sql, data, tablename):
        RPL = Replay.switch
        if not RPL:
            logger = log.Log()
            oprt_id = log.create_oprt_id()
            logger.write_to_log('DATA', 'STR', func.__name__, '', oprt_id)
            logger.write_to_log('OPRT', 'SQL', func.__name__, oprt_id, sql)
            func(self,sql, data, tablename)
            logger.write_to_log('DATA', 'SQL', func.__name__, oprt_id, data)
        else:
            logdb = LogDB()
            id_result = logdb.get_id(func.__name__)
            func(self, sql, data, tablename)
            replay_data = json.dumps(data,indent=2)
            list_rd1 = [id_result['time'],'<sql>insert table',tablename]
            list_rd2 = [id_result['time'],'<sql>insert data',replay_data]
            Replay.replay_data.append(list_rd1)
            Replay.replay_data.append(list_rd2)

    return wrapper


def handle_exception():
    RPL = Replay.switch
    if RPL:
        print('The Data cannot be obtained in the log, and the program cannot continue to execute normally')
        raise consts.ReplayExit
    else:
        print('The command result cannot be obtained, please check')
        raise consts.CmdError



