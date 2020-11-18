# coding=utf-8
import re
import consts
import sundry as s
import sys
import linstordb
from execute.lvm import LVM
import subprocess

import time

class TimeoutError(Exception):
    pass



def judge_result(result):
    # 对命令进行结果根据正则匹配进行分类
    re_suc = re.compile('SUCCESS')
    re_war = re.compile('WARNING')
    re_err = re.compile('ERROR')
    """
    suc : 0
    suc with war : 1
    war : 2
    err : 3
    """
    if re_err.search(result):
        result = {'sts':3,'rst':result}
    elif re_suc.search(result) and re_war.search(result):
        messege_war = get_war_mes(result)
        result = {'sts':1,'rst':messege_war}
    elif re_suc.search(result):
        result = {'sts':0,'rst':result}
    elif re_war.search(result):
        messege_war = get_war_mes(result)
        result = {'sts':2,'rst':messege_war}

    if result:
        return result
    else:
        s.handle_exception()

def get_err_detailes(result):
    re_ = re.compile(r'Description:\n[\t\s]*(.*)\n')
    if re_.search(result):
        return (re_.search(result).group(1))

def get_war_mes(result):
    re_ = re.compile(r'\x1b\[1;33mWARNING:\n\x1b(?:.*\s*)+\n$')
    if re_.search(result):
        return (re_.search(result).group())


@s.deco_cmd('linstor')
def execute_linstor_cmd(cmd,timeout=60):
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
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
    return judge_result(output)




class Node():
    def __init__(self):
        pass

    """node操作"""
    # 创建集群节点
    def create_node(self, node, ip, nt):
        cmd = f'linstor node create {node} {ip}  --node-type {nt}'
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
            result = execute_linstor_cmd(cmd)
            if result['sts'] == 0:
                s.prt_log('SUCCESS', 0)
            elif result['sts'] == 1:
                s.prt_log(f"SUCCESS\n{result['rst']}", 1)
            elif result['sts'] == 2:
                s.prt_log(f"FAIL\n{result['rst']}", 1)
            else:
                s.prt_log(f"FAIL\n{result['rst']}", 2)

    # 删除node
    def delete_node(self, node):
        cmd = f'linstor node delete {node}'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            s.prt_log('SUCCESS', 0)
        elif result['sts'] == 1:
            s.prt_log(f"SUCCESS\n{result['rst']}", 1)
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)

    def show_all_node(self, no_color='no'):
        collecter = linstordb.CollectData()
        if no_color == 'no':
            data = s.deco_color(collecter.get_all_node)()
        else:
            data = collecter.get_all_node()
        header = ["node", "node type", "res num", "stp num", "addr", "status"]
        table = s.show_linstor_data(header, data)
        s.prt_log(table,0)

    def show_one_node(self, node, no_color='no'):
        collecter = linstordb.CollectData()
        node_data = collecter.get_node_info(node)
        if not node_data:
            s.prt_log('The node does not exist',1)
        else:
            info = "node:%s\nnodetype:%s\nresource num:%s\nstoragepool num:%s\naddr:%s\nstatus:%s" % node_data
            if no_color == 'no':
                data_node = s.deco_color(collecter.get_one_node)(node)
                data_stp = s.deco_color(collecter.get_sp_in_node)(node)
            else:
                data_node = collecter.get_one_node(node)
                data_stp = collecter.get_sp_in_node(node)

            header_node = ['res_name', 'stp_name', 'size', 'device_name', 'used', 'status']
            header_stp = ['stp_name', 'node_name', 'res_num', 'driver', 'pool_name', 'free_size', 'total_size', 'snapshots',
                          'status']
            table_node = s.show_linstor_data(header_node, data_node)
            table_stp = s.show_linstor_data(header_stp, data_stp)
            result = '\n'.join([info, str(table_node), str(table_stp)])
            s.prt_log(result,0)



class StoragePool():
    def __init__(self):
        pass

    """storagepool操作"""
    # 创建storagepool
    def create_storagepool_lvm(self, node, stp, vg):
        obj_lvm = LVM()
        if not obj_lvm.is_vg_exists(vg):
            s.prt_log(f'Volume group:"{vg}" does not exist',1)
            return
        cmd = f'linstor storage-pool create lvm {node} {stp} {vg}'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            s.prt_log('SUCCESS', 0)
        elif result['sts'] == 1:
            s.prt_log(f"SUCCESS\n{result['rst']}", 1)
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)

    def create_storagepool_thinlv(self, node, stp, tlv):
        obj_lvm = LVM()
        if not obj_lvm.is_thinlv_exists(tlv):
            s.prt_log(f'Thin logical volume:"{tlv}" does not exist',1)
            return
        cmd = f'linstor storage-pool create lvmthin {node} {stp} {tlv}'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            s.prt_log('SUCCESS', 0)
        elif result['sts'] == 1:
            s.prt_log(f"SUCCESS\n{result['rst']}", 1)
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)

    # 删除storagepool -- ok
    def delete_storagepool(self, node, stp):
        cmd = f'linstor storage-pool delete {node} {stp}'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            s.prt_log('SUCCESS', 0)
        elif result['sts'] == 1:
            s.prt_log(f"SUCCESS\n{result['rst']}", 1)
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)


    def show_all_sp(self,no_color='no'):
        collector = linstordb.CollectData()
        if no_color == 'no':
            data = s.deco_color(collector.get_all_sp)()
        else:
            data = collector.get_all_sp()
        header = ['stp_name','node_name','res_num','driver','pool_name','free_size','total_size','snapshots','status']
        table = s.show_linstor_data(header, data)
        s.prt_log(table,0)


    def show_one_sp(self,sp,no_color='no'):
        collector = linstordb.CollectData()
        info_data = collector.get_sp_info(sp)
        if info_data[0] == 0:
            s.prt_log('The storagepool does not exist',1)
        else:
            info = 'The storagepool name for %s nodes is %s,they are %s.'%(info_data)
            if no_color == 'no':
                data = s.deco_color(collector.get_one_sp)(sp)
            else:
                data = collector.get_one_sp(sp)
            header = ['res_name', 'size', 'device_name', 'used', 'status']
            table = s.show_linstor_data(header, data)
            result = '\n'.join([info, str(table)])
            s.prt_log(result,0)



class Resource():
    def __init__(self):
        pass

    def collect_args(self,node,sp):
        """
        收集输入的参数，进行处理
        :param node: 列表，node名
        :param sp: 列表，storagepool名
        :return: 字典
        """

        dict_args = {}
        if len(sp) == 1:
            for node_one in node:
                dict_args.update({node_one:sp[0]})
        else:
            for node_one,sp_one in zip(node,sp):
                dict_args.update({node_one:sp_one})
        return dict_args


    def execute_create_res(self,res,node,sp):
        # 执行在指定节点和存储池上创建resource
        # 成功返回空字典，失败返回 {节点：错误原因}
        cmd = f'linstor resource create {node} {res} --storage-pool {sp}'
        try:
            result = execute_linstor_cmd(cmd)
            if result['sts'] == 2:
                s.prt_log(get_war_mes(result),1)
            if result['sts'] == 0:
                s.prt_log(f'Resource {res} was successfully created on Node {node}',0)
                return {}
            elif result['sts'] == 1:
                s.prt_log(f'Resource {res} was successfully created on Node {node}',0)
                return {}
            elif result['sts'] == 3:
                fail_cause = get_err_detailes(result['rst'])
                dict_fail = {node: fail_cause}
                return dict_fail

        except TimeoutError:
            result = f'{res} created timeout on node {node}, the operation has been cancelled'
            s.prt_log(result,2)
            return {node:'Execution creation timeout'}


    # 创建resource相关
    def linstor_delete_rd(self, res):
        cmd = f'linstor rd d {res}'
        execute_linstor_cmd(cmd)

    def linstor_create_rd(self, res):
        cmd = f'linstor rd c {res}'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            return True
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)
            return result



    def linstor_create_vd(self, res, size):
        cmd = f'linstor vd c {res} {size}'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            return True
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
            self.linstor_delete_rd(res)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)
            self.linstor_delete_rd(res)
            return result


    # 创建resource 自动
    def create_res_auto(self, res, size, num):
        cmd = f'linstor r c {res} --auto-place {num}'
        if self.linstor_create_rd(res) is True and self.linstor_create_vd(res, size) is True:
            result = execute_linstor_cmd(cmd)
            if result['sts'] == 0:
                s.prt_log('SUCCESS', 0)
                return True
            elif result['sts'] == 1:
                s.prt_log(f"SUCCESS\n{result['rst']}", 1)
                return True
            elif result['sts'] == 2:
                self.linstor_delete_rd(res)
                s.prt_log(f"FAIL\n{result['rst']}", 1)
                return result
            else:
                self.linstor_delete_rd(res)
                s.prt_log(f"FAIL\n{result['rst']}", 2)
                return result

        else:
            s.prt_log('The resource already exists',0)
            return ('The resource already exists')


    def create_res_manual(self, res, size, node, sp):
        dict_all_fail = {}
        dict_args = self.collect_args(node,sp)

        if self.linstor_create_rd(res) is True and self.linstor_create_vd(res, size) is True:
            pass
        else:
            s.prt_log('The resource already exists',1)
            return ('The resource already exists')

        for node_one,sp_one in dict_args.items():
            dict_one_result = self.execute_create_res(res,node_one,sp_one)
            dict_all_fail.update(dict_one_result)

        if len(dict_all_fail.keys()) == len(node):
            self.linstor_delete_rd(res)
        if len(dict_all_fail.keys()):
            fail_info = (f"Creation failure on {' '.join(dict_all_fail.keys())}\n")
            for node, cause in dict_all_fail.items():
                fail_cause = f"{node}:{cause}\n"
                fail_info = fail_info + fail_cause
            s.prt_log(fail_info,2)
            return dict_all_fail
        else:
            return True

    # 添加mirror（自动）
    def add_mirror_auto(self, res, num):
        cmd = f'linstor r c {res} --auto-place {num}'
        result = execute_linstor_cmd(cmd)
        # result = self.judge_result(output)
        if result['sts'] == 0:
            s.prt_log('SUCCESS', 0)
        elif result['sts'] == 1:
            s.prt_log(f"SUCCESS\n{result['rst']}", 1)
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)

    def add_mirror_manual(self, res, node, sp):
        dict_all_fail = {}
        dict_args = self.collect_args(node,sp)

        for node_one,sp_one in dict_args.items():
            dict_one_result = self.execute_create_res(res,node_one,sp_one)
            dict_all_fail.update(dict_one_result)

        if len(dict_all_fail.keys()):
            fail_info = (f"Creation failure on {' '.join(dict_all_fail.keys())}\n")
            for node, cause in dict_all_fail.items():
                fail_cause = f"{node}:{cause}\n"
                fail_info = fail_info + fail_cause
            s.prt_log(fail_info,2)
            return dict_all_fail
        else:
            return True

    # 创建resource --diskless
    def create_res_diskless(self, node, res):
        cmd = f'linstor r c {node[0]} {res} --diskless'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            s.prt_log('SUCCESS', 0)
        elif result['sts'] == 1:
            s.prt_log(f"SUCCESS\n{result['rst']}", 1)
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)

    # 删除resource,指定节点
    def delete_resource_des(self, node, res):
        cmd = f'linstor resource delete {node} {res}'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            s.prt_log('SUCCESS', 0)
        elif result['sts'] == 1:
            s.prt_log(f"SUCCESS\n{result['rst']}", 1)
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)

    # 删除resource，全部节点
    def delete_resource_all(self, res):
        cmd = f'linstor resource-definition delete {res}'
        result = execute_linstor_cmd(cmd)
        if result['sts'] == 0:
            s.prt_log('SUCCESS', 0)
        elif result['sts'] == 1:
            s.prt_log(f"SUCCESS\n{result['rst']}", 1)
        elif result['sts'] == 2:
            s.prt_log(f"FAIL\n{result['rst']}", 1)
        else:
            s.prt_log(f"FAIL\n{result['rst']}", 2)

    def show_all_res(self,no_color='no'):
        collecter = linstordb.CollectData()
        if no_color == 'no':
            data = s.deco_color(collecter.get_all_res)()
        else:
            data = collecter.get_all_res()
        header = ["resource", "mirror_way", "size", "device_name", "used"]
        table = s.show_linstor_data(header,data)
        s.prt_log(table,0)


    def show_one_res(self,res,no_color='no'):
        collecter = linstordb.CollectData()
        res_data = collecter.get_res_info(res)
        if not res_data:
            s.prt_log('The resource does not exist',1)
        else:
            info = ("resource:%s\nmirror_way:%s\nsize:%s\ndevice_name:%s\nused:%s" %res_data)
            if no_color == 'no':
                data = s.deco_color(collecter.get_one_res)(res)
            else:
                data = collecter.get_one_res(res)
            header = ['node_name', 'stp_name', 'drbd_role', 'status']
            table = s.show_linstor_data(header,data)
            result = '\n'.join([info, str(table)])
            s.prt_log(result,0)