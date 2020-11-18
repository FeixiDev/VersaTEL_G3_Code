# coding=utf-8
import consts
import sundry as s
import sys

class LVM():
    def __init__(self):
        self.data_vg = self.get_vg()
        self.data_lv = self.get_thinlv()

    def get_vg(self):
        cmd = 'vgs'
        result = s.execute_cmd(cmd)
        if result:
            return result
        else:
            s.handle_exception()

    def get_thinlv(self):
        cmd = 'lvs'
        result = s.execute_cmd(cmd)
        if result:
            return result
        else:
            s.handle_exception()

    def refine_thinlv(self):
        all_lv = self.data_lv.splitlines()
        list_thinlv = []
        re_ = '\s*(\S*)\s*(\S*)\s*\S*\s*(\S*)\s*\S*\s*\S*\s*\S*\s*?'
        for one in all_lv:
            if 'twi' in one:
                thinlv_one = s.re_findall(re_,one)
                list_thinlv.append(list(thinlv_one[0]))
        return list_thinlv

    def refine_vg(self):
        all_vg = self.data_vg.splitlines()
        list_vg = []
        re_ = '\s*(\S*)\s*\S*\s*\S*\s*\S*\s*\S*\s*(\S*)\s*(\S*)\s*?'
        for one in all_vg[1:]:
            vg_one = s.re_findall(re_,one)
            list_vg.append(list(vg_one[0]))
        return list_vg

    def is_vg_exists(self,vg):
        if vg in self.data_vg:
            return True

    def is_thinlv_exists(self,thinlv):
        """
        参数thinlv的正常格式：vg_name/thinlv_name
        判断传入的thinlv，跟系统存在的thinlv信息是否能够匹配，thinlv和vg都要一一对应
        :param thinlv:
        :return:
        """
        all_tlv_list = self.refine_thinlv()
        if '/' in thinlv:
            vg, thinlv = thinlv.split('/')
            for one in all_tlv_list:
                if thinlv ==one[0] and vg == one[1]:
                    return True
