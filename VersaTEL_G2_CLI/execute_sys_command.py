# coding=utf-8
import re
import subprocess
import time
from collections import OrderedDict
import log

_logger = log.Log()
_collector = log.Collector()


class crm():
    def re_data(self, crmdatas):
        crmdata = str(crmdatas)
        plogical = re.compile(
            r'primitive\s(\w*)\s\w*\s\\\s*\w*\starget_iqn="([a-zA-Z0-9.:-]*)"\s[a-z=-]*\slun=(\d*)\spath="([a-zA-Z0-9/]*)"\sallowed_initiators="([a-zA-Z0-9.: -]+)"(?:.*\s*){2}meta target-role=(\w*)')
        pvip = re.compile(
            r'primitive\s(\w*)\sIPaddr2\s\\\s*\w*\sip=([0-9.]*)\s\w*=(\d*)\s')
        ptarget = re.compile(
            r'primitive\s(\w*)\s\w*\s\\\s*params\siqn="([a-zA-Z0-9.:-]*)"\s[a-z=-]*\sportals="([0-9.]*):\d*"\s\\')
        redata = [
            plogical.findall(crmdata),
            pvip.findall(crmdata),
            ptarget.findall(crmdata)]
        print("get crm config data")
        return redata

    def get_data_crm(self):
        crmconfig = subprocess.getoutput('crm configure show')
        print("do crm configure show")
        # print("crmconfig:",crmconfig)
        return crmconfig

    def get_data_linstor(self):
        linstorres = subprocess.getoutput('linstor --no-color --no-utf8 r lv')
        print("do linstor r lv")
        return linstorres

    def createres(self, res, hostiqn, targetiqn):
        initiator = " ".join(hostiqn)
        lunid = str(int(res[1][1:]))
        op = " op start timeout=40 interval=0" \
             " op stop timeout=40 interval=0" \
             " op monitor timeout=40 interval=15"
        meta = " meta target-role=Stopped"
        mstr = "crm conf primitive " + res[0] \
               + " iSCSILogicalUnit params target_iqn=\"" + targetiqn \
               + "\" implementation=lio-t lun=" + lunid \
               + " path=\"" + res[2] \
               + "\" allowed_initiators=\"" + initiator + "\"" \
               + op + meta
        print(mstr)
        createcrm = subprocess.call(mstr, shell=True)
        print("call", mstr)
        if createcrm == 0:
            print("create iSCSILogicalUnit success")
            return True
        else:
            return False

    def delres(self, res):
        # crm res stop <LUN_NAME>
        stopsub = subprocess.call("crm res stop " + res, shell=True)
        if stopsub == 0:
            print("crm res stop " + res)
            n = 0
            while n < 10:
                n += 1
                if self.resstate(res):
                    print(res + " is Started, Wait a moment...")
                    time.sleep(1)
                else:
                    print(res + " is Stopped")
                    break
            else:
                print("Stop ressource " + res + " fail, Please try again.")
                return False

            time.sleep(3)
            # crm conf del <LUN_NAME>
            delsub = subprocess.call("crm conf del " + res, shell=True)
            if delsub == 0:
                print("crm conf del " + res)
                return True
            else:
                print("crm delete fail")
                return False
        else:
            print("crm res stop fail")
            return False

    def createco(self, res, target):
        # crm conf colocation <COLOCATION_NAME> inf: <LUN_NAME> <TARGET_NAME>
        print("crm conf colocation co_" + res + " inf: " + res + " " + target)
        coclocation = subprocess.call(
            "crm conf colocation co_" +
            res +
            " inf: " +
            res +
            " " +
            target,
            shell=True)
        if coclocation == 0:
            print("set coclocation")
            return True
        else:
            return False

    def createor(self, res, target):
        # crm conf order <ORDER_NAME1> <TARGET_NAME> <LUN_NAME>
        print("crm conf order or_" + res + " " + target + " " + res)
        order = subprocess.call(
            "crm conf order or_" +
            res +
            " " +
            target +
            " " +
            res,
            shell=True)
        if order == 0:
            print("set order")
            return True
        else:
            return False

    def resstart(self, res):
        # crm res start <LUN_NAME>
        print("crm res start " + res)
        start = subprocess.call("crm res start " + res, shell=True)
        if start == 0:
            return True
        else:
            return False

    def resstate(self, res):
        crm_show = self.get_data_crm()
        redata = self.re_data(crm_show)
        for s in redata[0]:
            if s[0] == res:
                if s[-1] == 'Stopped':
                    return False
                else:
                    return True


class lvm():

    @staticmethod
    def get_vg():
        result_vg = subprocess.Popen(
            'vgs',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return result_vg.stdout.read().decode()

    @staticmethod
    def get_thinlv():
        result_thinlv = subprocess.Popen(
            'lvs',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return result_thinlv.stdout.read().decode()

    @staticmethod
    def refine_thinlv(str):
        list_tb = str.splitlines()
        list_thinlv = []
        re_ = re.compile(
            r'\s*(\S*)\s*(\S*)\s*\S*\s*(\S*)\s*\S*\s*\S*\s*\S*\s*?')
        for list_one in list_tb:
            if 'twi' in list_one:
                thinlv_one = re_.findall(list_one)
                list_thinlv.append(list(thinlv_one[0]))
        return list_thinlv

    @staticmethod
    def refine_vg(str):
        list_tb = str.splitlines()
        list_vg = []
        re_ = re.compile(
            r'\s*(\S*)\s*\S*\s*\S*\s*\S*\s*\S*\s*(\S*)\s*(\S*)\s*?')
        for list_one in list_tb[1:]:
            vg_one = re_.findall(list_one)
            list_vg.append(list(vg_one[0]))
        return list_vg


class linstor():
    @staticmethod
    def get_node():
        result_node = subprocess.Popen(
            'linstor --no-color --no-utf8 n l',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return result_node.stdout.read().decode('utf-8')

    @staticmethod
    def get_res():
        result_res = subprocess.Popen(
            'linstor --no-color --no-utf8 r lv',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return result_res.stdout.read().decode('utf-8')

    @staticmethod
    def get_sp():
        result_sp = subprocess.Popen(
            'linstor --no-color --no-utf8 sp l',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return result_sp.stdout.read().decode('utf-8')

    @staticmethod
    def refine_linstor(table_data):
        reSeparate = re.compile(r'(.*?\s\|)')
        list_table = table_data.split('\n')
        list_data_all = []

        def clear_symbol(list_data):
            for i in range(len(list_data)):
                list_data[i] = list_data[i].replace(' ', '')
                list_data[i] = list_data[i].replace('|', '')

        for i in range(len(list_table)):
            if list_table[i].startswith('|') and '=' not in list_table[i]:
                valid_data = reSeparate.findall(list_table[i])
                clear_symbol(valid_data)
                list_data_all.append(valid_data)
        try:
            list_data_all.pop(0)
        except IndexError:
            print('The data cannot be read, please check whether LINSTOR is normal.')
        return list_data_all


# 子命令stor调用的方法
class stor():
    @staticmethod
    def judge_cmd_result_suc(cmd):
        re_suc = re.compile('SUCCESS')
        if re_suc.search(cmd):
            return True

    @staticmethod
    def judge_cmd_result_err(cmd):
        re_err = re.compile('ERROR')
        if re_err.search(cmd):
            return True

    @staticmethod
    def judge_cmd_result_war(cmd):
        re_err = re.compile('WARNING')
        if re_err.search(cmd):
            return True

    @staticmethod
    def get_err_not_vg(result, node, vg):
        re_ = re.compile(
            r'\(Node: \'' +
            node +
            r'\'\) Volume group \'' +
            vg +
            '\' not found')
        if re_.search(result):
            return (re_.search(result).group())

    @staticmethod
    def get_err_detailes(result):
        re_ = re.compile(r'Description:\n[\t\s]*(.*)\n')
        if re_.search(result):
            return (re_.search(result).group(1))

    @staticmethod
    def get_war_mes(result):
        re_ = re.compile(r'\x1b\[1;33mWARNING:\n\x1b(?:.*\s*)+\n$')
        if re_.search(result):
            return (re_.search(result).group())

    @staticmethod
    def execute_cmd(cmd):
        action = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        result = action.stdout.read()
        if stor.judge_cmd_result_err(str(result)):
            print(result.decode('utf-8'))
            return result.decode()
        elif stor.judge_cmd_result_suc(str(result)):
            return True
        if stor.judge_cmd_result_war(str(result)):
            messege_war = stor.get_war_mes(result.decode('utf-8'))
            print(messege_war)
            return messege_war

    @staticmethod
    def print_excute_result(cmd):
        result = stor.execute_cmd(cmd)
        if result:
            print('SUCCESS')
            return True
        else:
            print('FAIL')
            return result

    # 创建resource相关 -- ok
    @staticmethod
    def linstor_delete_rd(res):
        cmd = 'linstor rd d %s' % res
        subprocess.check_output(cmd, shell=True)

    @staticmethod
    def linstor_delete_vd(res):
        cmd = 'linstor vd d %s' % res
        subprocess.check_output(cmd, shell=True)

    @staticmethod
    def linstor_create_rd(res):
        cmd_rd = 'linstor rd c %s' % res
        result = stor.execute_cmd(cmd_rd)
        if result is True:
            return True
        else:
            _logger.InputLogger.error(
                'create res',
                extra={
                    'username': _collector.get_username(),
                    'type': 'return_to_show',
                    'describe1': result,
                    'describe2': '',
                    'data': 'FAIL'})
            print('FAIL')
            return result

    @staticmethod
    def linstor_create_vd(res, size):
        cmd_vd = 'linstor vd c %s %s' % (res, size)
        result = stor.execute_cmd(cmd_vd)
        if result is True:
            return True
        else:
            print('FAIL')
            stor.linstor_delete_rd(res)
            return result

    # 创建resource 自动
    @staticmethod
    def create_res_auto(res, size, num):
        cmd = 'linstor r c %s --auto-place %d' % (res, num)
        if stor.linstor_create_rd(res) is True and stor.linstor_create_vd(res, size) is True:
            result = stor.execute_cmd(cmd)
            if result:
                print('SUCCESS')
                _logger.InputLogger.debug(
                    'create res',
                    extra={
                        'username': _collector.get_username(),
                        'type': 'return_to_show',
                        'describe1': _collector.get_path(),
                        'describe2': '',
                        'data': 'SUCCESS'})
                return True
            else:
                print('FAIL')
                stor.linstor_delete_rd(res)
                _logger.InputLogger.debug(
                    'create res',
                    extra={
                        'username': _collector.get_username(),
                        'type': 'return_to_show',
                        'describe1': result,
                        'describe2': '',
                        'data': 'FAIL'})
                return result

        # 创建resource 手动

    @staticmethod
    def create_res_manual(res, size, node, stp):
        flag = OrderedDict()

        def print_fail_node():
            if len(flag.keys()):
                print('Creation failure on', *flag.keys(), sep=' ')
                for node, cause in flag.items():
                    print(node, ':', cause)
                return flag
            else:
                return True

        def whether_delete_rd():
            if len(flag.keys()) == len(node):
                stor.linstor_delete_rd(res)

        def create_resource(cmd):
            action = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            result = action.stdout
            if stor.judge_cmd_result_war(str(result)):
                print(stor.get_war_mes(result.decode('utf-8')))

            if stor.judge_cmd_result_suc(str(result)):
                print(
                    'Resource %s was successfully created on Node %s' %
                    (res, node_one))
            elif stor.judge_cmd_result_err(str(result)):
                str_fail_cause = stor.get_err_detailes(result.decode('utf-8'))
                dict_fail = {node_one: str_fail_cause}
                flag.update(dict_fail)

        if len(stp) == 1:
            if stor.linstor_create_rd(
                    res) is True and stor.linstor_create_vd(res, size) is True:
                for node_one in node:
                    cmd = 'linstor resource create %s %s --storage-pool %s' % (
                        node_one, res, stp[0])
                    create_resource(cmd)
                whether_delete_rd()
                return print_fail_node()
            else:
                # need to be prefect
                return ('The ResourceDefinition already exists')
        elif len(node) == len(stp):
            if stor.linstor_create_rd(
                    res) is True and stor.linstor_create_vd(res, size) is True:
                for node_one, stp_one in zip(node, stp):
                    cmd = 'linstor resource create %s %s --storage-pool %s' % (
                        node_one, res, stp_one)
                    create_resource(cmd)
                whether_delete_rd()
                return print_fail_node()
            else:
                return ('The ResourceDefinition already exists')
        else:
            print('The number of Node and Storage pool do not meet the requirements')

    # 添加mirror（自动）
    @staticmethod
    def add_mirror_auto(res, num):
        cmd = 'linstor r c %s --auto-place %d' % (res, num)
        return stor.print_excute_result(cmd)

    @staticmethod
    def add_mirror_manual(res, node, stp):
        flag = OrderedDict()

        def print_fail_node():
            if len(flag.keys()):
                print('Creation failure on', *flag.keys(), sep=' ')
                return flag
            else:
                return True

        def add_mirror():
            action = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            result = action.stdout
            if stor.judge_cmd_result_suc(str(result)):
                print(
                    'Resource %s was successfully created on Node %s' %
                    (res, node_one))
            elif stor.judge_cmd_result_err(str(result)):
                str_fail_cause = stor.get_err_detailes(result.decode('utf-8'))
                dict_fail = {node_one: str_fail_cause}
                flag.update(dict_fail)

        if len(stp) == 1:
            for node_one in node:
                cmd = 'linstor resource create %s %s --storage-pool %s' % (
                    node_one, res, stp[0])
                add_mirror()
            return print_fail_node()
        elif len(node) == len(stp):
            for node_one, stp_one in zip(node, stp):
                cmd = 'linstor resource create %s %s --storage-pool %s' % (
                    node_one, res, stp_one)
                add_mirror()
            return print_fail_node()
        else:
            print('The number of storage pools does not meet the requirements.')

    # 创建resource --diskless
    @staticmethod
    def create_res_diskless(node, res):
        cmd = 'linstor r c %s %s --diskless' % (node, res)
        return stor.print_excute_result(cmd)

    # 删除resource,指定节点 -- ok
    @staticmethod
    def delete_resource_des(node, res):
        cmd = 'linstor resource delete %s %s' % (node, res)
        return stor.print_excute_result(cmd)

    # 删除resource，全部节点 -- ok
    @staticmethod
    def delete_resource_all(res):
        cmd = 'linstor resource-definition delete %s' % res
        return stor.print_excute_result(cmd)

    # 创建storagepool  -- ok
    @staticmethod
    def create_storagepool_lvm(node, stp, vg):
        cmd = 'linstor storage-pool create lvm %s %s %s' % (node, stp, vg)
        action = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        result = action.stdout
        if stor.judge_cmd_result_war(str(result)):
            print(result.decode('utf-8'))
        # 发生ERROR的情况
        if stor.judge_cmd_result_err(str(result)):
            # 使用不存的vg
            if stor.get_err_not_vg(str(result), node, vg):
                print(stor.get_err_not_vg(str(result), node, vg))
                subprocess.check_output(
                    'linstor storage-pool delete %s %s' %
                    (node, stp), shell=True)
            else:
                print(result.decode('utf-8'))
                print('FAIL')
                return result.decode()
        # 成功
        elif stor.judge_cmd_result_suc(str(result)):
            print('SUCCESS')
            return True

    @staticmethod
    def create_storagepool_thinlv(node, stp, tlv):
        cmd = 'linstor storage-pool create lvmthin %s %s %s' % (node, stp, tlv)
        return stor.print_excute_result(cmd)

    # 删除storagepool -- ok
    @staticmethod
    def delete_storagepool(node, stp):
        cmd = 'linstor storage-pool delete %s %s' % (node, stp)
        return stor.print_excute_result(cmd)

    # 创建集群节点
    @staticmethod
    def create_node(node, ip, nt):
        cmd = 'linstor node create %s %s  --node-type %s' % (node, ip, nt)
        nt_value = [
            'Combined',
            'combined',
            'Controller',
            'Auxiliary',
            'Satellite']
        if nt not in nt_value:
            print('node type error,choose from ''Combined',
                  'Controller', 'Auxiliary', 'Satellite''')
        else:
            return stor.print_excute_result(cmd)
    # 删除node

    @staticmethod
    def delete_node(node):
        cmd = 'linstor node delete %s' % node
        return stor.print_excute_result(cmd)


class iscsi_map():

    # 获取并更新crm信息
    def crm_up(self, js):
        cd = crm()
        crm_config_statu = cd.get_data_crm()
        if 'ERROR' in crm_config_statu:
            print("Could not perform requested operations, are you root?")
            return False
        else:
            redata = cd.re_data(crm_config_statu)
            js.up_crmconfig(redata)
            return redata

    # 获取创建map所需的数据
    def map_data(self, js, crmdata, hg, dg):
        mapdata = {}
        hostiqn = []
        for h in js.get_data('HostGroup').get(hg):
            iqn = js.get_data('Host').get(h)
            hostiqn.append(iqn)
        mapdata.update({'host_iqn': hostiqn})
        disk = js.get_data('DiskGroup').get(dg)
        cd = crm()
        data = cd.get_data_linstor()
        linstorlv = linstor.refine_linstor(data)
        print("get linstor r lv data")
        diskd = {}
        for d in linstorlv:
            for i in disk:
                if i in d:
                    diskd.update({d[1]: [d[4], d[5]]})
        mapdata.update({'disk': diskd})
        mapdata.update({'target': crmdata[2]})
        return mapdata

    # 获取删除map所需的数据
    def map_data_d(self, js, mapname):
        dg = js.get_data('Map').get(mapname)[1]
        disk = js.get_data('DiskGroup').get(dg)
        return disk

    # 调用crm创建map
    def map_crm_c(self, mapdata):
        cd = crm()
        for i in mapdata['target']:
            target = i[0]
            targetiqn = i[1]
        for disk in mapdata['disk']:
            res = [
                disk,
                mapdata['disk'].get(disk)[0],
                mapdata['disk'].get(disk)[1]]
            if cd.createres(res, mapdata['host_iqn'], targetiqn):
                c = cd.createco(res[0], target)
                o = cd.createor(res[0], target)
                s = cd.resstart(res[0])
                if c and o and s:
                    print('create colocation and order success:', disk)
                else:
                    print("create colocation and order fail")
                    return False
            else:
                print('create resource Fail!')
                return False
        return True

    # 调用crm删除map
    def map_crm_d(self, resname):
        cd = crm()
        crm_config_statu = cd.get_data_crm()
        if 'ERROR' in crm_config_statu:
            print("Could not perform requested operations, are you root?")
            return False
        else:
            for disk in resname:
                if cd.delres(disk):
                    print("delete ", disk)
                else:
                    return False
            return True
