# coding=utf-8
import re
import consts
import sundry as s
import sys



class Linstor():
    def __init__(self):
        self.logger = consts.glo_log()

    def refine_linstor(self,data):
        reSeparate = re.compile(r'(.*?\s\|)')
        list_table = data.split('\n')
        list_data_all = []

        oprt_id = s.create_oprt_id()
        self.logger.write_to_log('DATA','STR','refine_linstor','',oprt_id)
        self.logger.write_to_log('OPRT','REGULAR','findall',oprt_id,{'re':reSeparate})

        def _clear_symbol(list_data):
            for i in range(len(list_data)):
                list_data[i] = list_data[i].replace(' ', '')
                list_data[i] = list_data[i].replace('|', '')

        for i in range(len(list_table)):
            if list_table[i].startswith('|') and '=' not in list_table[i]:
                valid_data = reSeparate.findall(list_table[i])
                _clear_symbol(valid_data)
                list_data_all.append(valid_data)

        try:
            list_data_all.pop(0)
        except IndexError:
            s.prt_log('The data cannot be read, please check whether LINSTOR is normal.',2)
            sys.exit()
        if list_data_all:
            if not list_data_all[0]:
                s.prt_log('正则匹配出错,程序退出',2)
                sys.exit()

        self.logger.write_to_log('DATA', 'REGULAR', 'findall', oprt_id, list_data_all)
        return list_data_all

    def get_linstor_data(self,cmd):
        cmd_result = s.execute_cmd(cmd)
        return self.refine_linstor(cmd_result)
