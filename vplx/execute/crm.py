# coding=utf-8
import re
import time
import traceback
import copy

import iscsi_json
import sundry as s
import subprocess
import consts

@s.deco_cmd('crm')
def execute_crm_cmd(cmd, timeout=60):
    """
    Execute the command cmd to return the content of the command output.
    If it times out, a TimeoutError exception will be thrown.
    cmd - Command to be executed
    timeout - The longest waiting time(unit:second)
    """
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
    t_beginning = time.time()
    seconds_passed = 0
    output = None
    while True:
        if p.poll() is not None:
            break
        if p.stderr:
            break
        seconds_passed = time.time() - t_beginning
        if timeout and seconds_passed > timeout:
            p.terminate()
            raise TimeoutError(cmd, timeout)
        time.sleep(0.1)
    out, err = p.communicate()
    if len(out) > 0:
        out = out.decode()
        output = {'sts': 1, 'rst': out}
    elif len(err) > 0:
        err = err.decode()
        output = {'sts': 0, 'rst': err}
    elif out == b'':  # 需要再考虑一下 res stop 执行成功没有返回，stop失败也没有返回（无法判断stop成不成功）
        out = out.decode()
        output = {'sts': 1, 'rst': out}

    if output:
        return output
    else:
        s.handle_exception()


class RollBack():
    """
    装饰器，记录执行进行操作CRM资源名，提供方法rollback可以回滚执行操作的操作
    """
    dict_rollback = {'IPaddr2':{}, 'PortBlockGroup':{} , 'ISCSITarget':{}}
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        self.type,self.oprt = self.func.__qualname__.split('.')
        if self.func(self, *args, **kwargs):
            self.dict_rollback[self.type].update({args[0]:self.oprt})

    # def __init__(self,func):
    #     self.func = func
    #     wraps(func)(self)
    #     self.type,self.oprt = func.__qualname__.split('.')
    #
    #
    # def __call__(self,*args, **kwargs):
    #     wraps(self.func)(self)
    #     self.type,self.oprt = self.func.__qualname__.split('.')
    #     if self.__wrapped__(*args, **kwargs):
    #         self.dict_rollback[self.type].update({args[1]:self.oprt})

    # 带参数的编写方式
    # def __init__(self,type):
    #     self.type = type
    #
    # def __call__(self,func):
    #     res, oprt = func.__qualname__.split('.')
    #     type = self.type
    #     dict_rb = self.dict_rb
    #     @wraps(func)
    #     def wrapper(self,*args):
    #         if func(self,*args):
    #             dict_rb[oprt].append(args[0])
    #     return wrapper


    # 保证调用被装饰的类方法时，有实例对象绑定类
    # def __get__(self, instance, cls):
    #     if instance is None:
    #         return self
    #     else:
    #         return types.MethodType(self, instance)



    @classmethod
    def rollback(cls,type, *args):
        # 目前只用于Portal的回滚，之后Target的回滚可以根据需要增加一个判断类型的参数
        print("Execution error, resource rollback")
        if type == 'portal':
            ip, port, netmask = args
            cls.rb_ipaddr2(cls, ip, port, netmask)
            cls.rb_block(cls, ip, port, netmask)
            cls.rb_target(cls, ip, port, 'iqn')
        elif type == 'target':
            ip, port, iqn = args
            cls.rb_target(cls,ip,port,iqn)
        print("resource rollback ends")


    # 回滚完之后考虑做一个对crm配置的检查？跟name相关的资源如果还存在，进行提示？

    def rb_ipaddr2(self,ip,port,netmask):
        if self.dict_rollback['IPaddr2']:
            obj_ipaddr2 = IPaddr2()
            # 实际上应该不可能需要循环
            for name, oprt in self.dict_rollback['IPaddr2'].items():
                if oprt == 'create':
                    obj_ipaddr2.delete(name)
                elif oprt == 'delete':
                    obj_ipaddr2.create(name,ip,netmask)
                elif oprt == 'modify':
                    obj_ipaddr2.modify(name,ip,netmask)


    def rb_block(self,ip,port,netmask):
        if self.dict_rollback['PortBlockGroup']:
            obj_block = PortBlockGroup()
            for name,oprt in self.dict_rollback['PortBlockGroup'].items():
                if oprt == 'create':
                    obj_block.delete(name)
                elif oprt == 'delete':
                    action = 'block'
                    if name.split('_')[2] == 'off':
                        action = 'unblock'
                    obj_block.create(name,ip,port,action)
                elif oprt == 'modify':
                    obj_block.modify(name,ip,port)


    def rb_target(self,ip,port,iqn):
        if self.dict_rollback['ISCSITarget']:
            obj_target = ISCSITarget()
            for name,oprt in self.dict_rollback['ISCSITarget'].items():
                if oprt == 'create':
                    obj_target.delete(name)
                elif oprt == 'modify_iqn':
                    obj_target.modify_iqn(name,iqn)
                elif oprt == 'modify_portal':
                    obj_target.modify_portal(name,ip,port)
                elif oprt == 'delete':
                    obj_target.create(name,iqn,ip,port)




class CRMData():
    def __init__(self):
        self.crm_conf_data = self.get_crm_conf()
        self.vip = None
        self.portblock = None
        self.target = None
        if 'ERROR' in self.crm_conf_data:
            s.prt_log("Could not perform requested operations, are you root?",2)

        self.crm_st = None


    def get_crm_conf(self):
        cmd = 'crm configure show | cat'
        result = execute_crm_cmd(cmd)
        if result:
            return result['rst']
        else:
            s.handle_exception()


    def get_crm_st(self):
        cmd = 'crm st | cat'
        result = execute_crm_cmd(cmd)
        if result:
            self.crm_st = result['rst']
            return result['rst']
        else:
            s.handle_exception()


    def get_target_and_node(self):
        target_all = re.findall('(\w*)\s*\(ocf::heartbeat:iSCSITarget\):\s*\w*\s(\w*)',self.crm_st)
        dict_target = {}
        for i in target_all:
            if i[1] in dict_target.keys():
                dict_target[i[1]].append(i[0])
            else:
                dict_target.update({i[1]: [i[0]]})
        return dict_target

    def get_res_status(self,res,type):
        # 获取target，lun，portal的status
        re_status = f'{res}\s*\(ocf::heartbeat:{type}\):\s*(.*?)\s'
        status = re.findall(re_status,self.crm_st)
        if status:
            return status[0]




    # 获取集群中各节点的资源
    # def get_cluster_res(self):
    #     cmd = "crm st | cat"
    #     result = execute_crm_cmd(cmd)
    #     target_all = re.findall('(\w*)\s*\(ocf::heartbeat:iSCSITarget\):\s*\w*\s(\w*)',result['rst'])
    #     lun_all = re.findall('(\w*)\s*\(ocf::heartbeat:iSCSILogicalUnit\):\s*\w*\s(\w*)',result['rst'])
    #
    #
    #     dict_target = {}
    #     dict_lun = {}
    #     for i in target_all:
    #         dict_target.update({i[1]:i[0]})
    #
    #     for i in lun_all:
    #         dict_lun.update({i[1]:i[0]})






    def get_vip(self):
        re_vip = re.compile(
            r'primitive\s(\S+)\sIPaddr2.*\s*params\sip=([0-9.]+)\scidr_netmask=(\d+)')
        result = s.re_findall(re_vip, self.crm_conf_data)
        dict_vip = {}
        for vip in result:
            dict_vip.update({vip[0]:{'ip':vip[1],'netmask':vip[2]}})
        self.vip = dict_vip
        return dict_vip

    def get_portblock(self):
        re_portblock = re.compile(
            r'primitive\s(\S+)\sportblock.*\s*params\sip=([0-9.]+)\sportno=(\d+).*action=(\w+)')
        result = s.re_findall(re_portblock,self.crm_conf_data)
        dict_portblock = {}
        for portblock in result:
            dict_portblock.update({portblock[0]:{'ip':portblock[1],'port':portblock[2],'type':portblock[3]}})
        self.portblock = dict_portblock
        return dict_portblock

    def get_target(self):
        re_target = re.compile(
            r'primitive\s(\S+)\siSCSITarget.*\s*params\siqn="?(\S+?)"?\s.*portals="([0-9.]+):(\d+)"')
        result = s.re_findall(re_target, self.crm_conf_data)
        dict_target = {}
        for target in result:
            dict_target.update({target[0]:{'target_iqn':target[1],'ip':target[2],'port':target[3]}})
        self.target = dict_target
        return dict_target

    def get_iscsi_logical_unit(self):
        # ilu : iscsi logical unit
        re_ilu = re.compile(
            r'primitive\s(\S+)\siSCSILogicalUnit.*\s*params\starget_iqn="(\S+)"\s.*?lun=(\d+)\spath="(\S+)"\sallowed_initiators="(.*?)"')
        result = s.re_findall(re_ilu, self.crm_conf_data)
        dict_ilu = {}
        for ilu in result:
            dict_ilu.update({ilu[0]:{'target_iqn':ilu[1],'lun':ilu[2],'path':ilu[3],'initiators':ilu[4].split(' ')}})
        self.ilu = dict_ilu
        return dict_ilu


    def get_order(self):
        re_order = re.compile(r'^order\s(.*?)\s(.*?)\s(.*?)$',re.MULTILINE)
        result = s.re_findall(re_order,self.crm_conf_data)
        dict_order = {}
        for order in result:
            dict_order.update({order[0]:[order[1],order[2]]})
        return dict_order

    def get_colocation(self):
        re_colocation = re.compile(r'^colocation\s(.*?)\sinf:\s(.*?)\s(.*?)$',re.MULTILINE)
        result = s.re_findall(re_colocation,self.crm_conf_data)
        dict_colocation = {}
        for colocation in result:
            dict_colocation.update({colocation[0]:{colocation[1],colocation[2]}})
        return dict_colocation

    def get_conf_portal(self,vip_all,portblock_all,target_all):
        """
        获取现在CRM的环境下所有Portal的数据，
        :param vip_all: 目前CRM环境的所有vip数据
        :param portblock_all:目前CRM环境下的所有portblock数据
        :param target_all: 目前CRM环境下的所有target数据
        :return:
        """
        dict_portal = {}
        for vip in vip_all:
            dict_portal.update(
                {vip: {'ip': vip_all[vip]['ip'], 'port': '', 'netmask': vip_all[vip]['netmask'], 'target': []}})

            for portblock in portblock_all:
                if portblock_all[portblock]['ip'] == vip_all[vip]['ip']:
                    dict_portal[vip]['port'] = portblock_all[portblock]['port']
                    continue

            for target in target_all:
                if target_all[target]['ip'] == vip_all[vip]['ip']:
                    dict_portal[vip]['target'].append(target)

        return dict_portal


    def get_conf_target(self,vip_all,target_all,lun_all):
        """
        获取现在CRM环境下的所有Target数据，组成与配置文件同样的结构返回
        """
        dict_target = {}
        for target in target_all:
            dict_target.update({target: {'target_iqn': target_all[target]['target_iqn'], 'portal':'','lun':[]}})
            for vip in vip_all:
                # 对target添加portal
                if target_all[target]['ip'] == vip_all[vip]['ip']:
                    dict_target[target]['portal'] = vip
            for lun in lun_all:
                # 对target添加lun
                if target_all[target]['target_iqn'] == lun_all[lun]['target_iqn']:
                    dict_target[target]['lun'].append(lun)
        return dict_target


    def get_conf_lun(self,target_all,lun_all):
        """
        获取现在CRM环境下的所有LogicalUnit数据，组成与配置文件同样的结构返回
        """
        dict_lun = {}
        for lun in lun_all:
            dict_lun.update({lun:{'lun_id':lun_all[lun]['lun'],
                                                  'target':'',
                                                  'path':lun_all[lun]['path'],
                                                  'initiators':lun_all[lun]['initiators']}})
            for target in target_all:
                if target_all[target]['target_iqn'] == lun_all[lun]['target_iqn']:
                    dict_lun[lun]['target'] = target

        return dict_lun



    def check_portal_component(self,vip,portblock,order,colocation):
        """
        对目前环境的portal组件(ipaddr,portblock）的检查，需满足：
        1.不存在单独的portblock/vip
        2.已存在的ipaddr，必须有对应的portblock组（block，unblock）以及对应的order和colocation
        不满足条件时提示并退出
        :param vip_all: dict
        :param portblock_all: dict
        :return:None
        """
        dict_portal = {}
        list_normal_portblock = []
        for vip_name,vip_data in list(vip.items()):
            dict_portal.update({vip_name:{}}) #error/normal
            for pb_name,pb_data in list(portblock.items()):
                if vip_data['ip'] == pb_data['ip']:
                    dict_portal[vip_name].update({pb_name:pb_data['type']})
                    list_normal_portblock.append(pb_name)
            if len(dict_portal[vip_name]) == 2:
                if 'block' and 'unblock' in dict_portal[vip_name].values():
                    dict_portal[vip_name] = {pb_type:pb for pb,pb_type in dict_portal[vip_name].items()}
                    for ord_name,ord_data in list(order.items()):
                        if [dict_portal[vip_name]['block'],vip_name] == ord_data:
                            # 这里没考虑符合条件的多个order的这种情况
                            dict_portal[vip_name].update({'order':ord_name})

                    for col_name,col_data in list(colocation.items()):
                        # 这里同样没考虑多个符合条件的colocatin这种情况
                        if {vip_name,dict_portal[vip_name]['block']} == col_data:
                            dict_portal[vip_name].update({'colocation_block':col_name})
                        if {vip_name,dict_portal[vip_name]['unblock']}== col_data:
                            dict_portal[vip_name].update({'colocation_unblock':col_name})


        error_portblock = set(portblock.keys()) - set(list_normal_portblock)
        if error_portblock:
            s.prt_log(f'Portblock:{",".join(error_portblock)} do not have corresponding VIP, please proceed',2)
        list_portal = [] # portal如果没有block和unblock，则会加进这个列表

        for portal_name,portal_data in list(dict_portal.items()):
            if len(dict_portal[portal_name]) != 5:
                list_portal.append(portal_name)
        if list_portal:
            s.prt_log(f'Portal:{",".join(list_portal)} can not be used normally,  please proceed',2)
        # 收集了不符合规范的portal对应的所有组件，但是目前还没有进行提示


    def check_env_sync(self,vip,portblock,target,lun):
        """
        检查CRM环境与JSON配置文件所记录的Portal、Target、LogicalUnit的数据是否一致，不一致提示后退出
        :param vip_all:目前CRM环境的vip数据
        :param target_all:目前CRM环境的target数据
        :return:
        """
        js = iscsi_json.JsonOperation()
        all_key = js.json_data.keys()
        if not 'Portal' in all_key:
            s.prt_log('"Portal" do not exist in the JSON configuration file',2)
            return
        if not 'Target' in all_key:
            s.prt_log('"Target" do not exist in the JSON configuration file',2)
            return
        if not 'LogicalUnit' in all_key:
            s.prt_log('"LogicalUnit" do not exist in the JSON configuration file',2)
            return


        crm_portal = self.get_conf_portal(vip,portblock,target)
        json_portal = copy.deepcopy(js.json_data['Portal']) # 防止对json对象的数据修改，进行深拷贝，之后修改数据结构再修改

        crm_target = self.get_conf_target(vip,target,lun)
        json_target = copy.deepcopy(js.json_data['Target'])

        crm_lun = self.get_conf_lun(target,lun)
        json_lun = copy.deepcopy(js.json_data['LogicalUnit'])


        # 处理列表的顺序问题
        try:
            for portal_name,portal_data in crm_portal.items():
                portal_data['target'] = set(portal_data['target'])

            for portal_name,portal_data in json_portal.items():
                portal_data['target'] = set(portal_data['target'])

            for target_name,target_data in crm_target.items():
                target_data['lun'] = set(target_data['lun'])

            for target_name,target_data in json_target.items():
                target_data['lun'] = set(target_data['lun'])

            for lun_name,lun_data in crm_target.items():
                lun_data['lun'] = set(lun_data['lun'])

            for lun_name,lun_data in json_target.items():
                lun_data['lun'] = set(lun_data['lun'])

            if not crm_portal == json_portal:
                s.prt_log('The data Portal of the JSON configuration file is inconsistent, please check and try again',2)
                return
            if not crm_target == json_target:
                s.prt_log('The data Target of the JSON configuration file is inconsistent, please check and try again',2)
                return
            if not crm_lun == json_lun:
                s.prt_log('The data LogicalUnit of the JSON configuration file is inconsistent, please check and try again',2)
                return

        except KeyError as key:
            s.prt_log(f'The configuration file is missing a key: {key}',2)

    def check(self):
        """
        进行Portal/iSCSITarget的创建时候，需要进行的所有检查，不通过则中断程序
        :return: None
        """
        vip = self.get_vip()
        portblock = self.get_portblock()
        target = self.get_target()
        lun = self.get_iscsi_logical_unit()
        order = self.get_order()
        colocation = self.get_colocation()
        self.check_portal_component(vip,portblock,order,colocation)
        self.check_env_sync(vip,portblock,target,lun)


    def update(self):
        js = iscsi_json.JsonOperation()

        # 获取数据
        vip = self.get_vip()
        portblock = self.get_portblock()
        target = self.get_target()
        iscsilogicalunit = self.get_iscsi_logical_unit()

        portal = self.get_conf_portal(vip,portblock,target)
        js.cover_data('Portal',portal)
        target = self.get_conf_target(vip,target,iscsilogicalunit)
        js.cover_data('Target',target)
        logical = self.get_conf_lun(target,iscsilogicalunit)
        js.cover_data('LogicalUnit',logical)
        js.commit_data()



class CRMConfig():
    def __init__(self):
        pass


    def get_failed_actions(self, res):
        # 检查crm整体状态，但是目前好像只是用于提取vip的错误信息
        exitreason = None
        cmd_result = execute_crm_cmd('crm st | cat')
        re_error = re.compile(
            f"\*\s({res})\w*\son\s(\S*)\s'(.*)'\s.*exitreason='(.*)',")
        result = s.re_findall(re_error,cmd_result['rst'])
        if result:
            if result[0][3] == '[findif] failed':
                exitreason = 0
            else:
                exitreason = result
        return exitreason

    def get_crm_res_status(self, res, type):
        """
        获取crm res的状态
        :param res:
        :param type:
        :return: string
        """
        if not type in ['IPaddr2','iSCSITarget','portblock','iSCSILogicalUnit']:
            raise ValueError('"type" must one of [IPaddr2,iSCSITarget,portblock,iSCSILogicalUnit]')

        cmd_result = execute_crm_cmd(f'crm res list | grep {res}')
        re_status = f'{res}\s*\(ocf::heartbeat:{type}\):\s*(.*?)\n'
        status = s.re_search(re_status,cmd_result['rst'],output_type='groups')
        if status:
            return status[0]

    def monitor_status(self, res, type, expect_status, times=5):
        """
        检查crm res的状态
        :param res: 需要检查的资源
        :param type_res: 需要检查的资源类型
        :param times: 需要检查的次数
        :param expect_status: 预期状态
        :return: 返回True则说明是预期效果
        """
        n = 0
        while n < times:
            n += 1
            if expect_status in self.get_crm_res_status(res,type):
                s.prt_log(f'The status of {res} is {expect_status} now.',0)
                return True
            else:
                time.sleep(1)
        else:
            s.prt_log("Does not meet expectations, please try again.", 1)


    def monitor_status_by_time(self,res, type, expect_status, timeout=20):
        """
        检查crm res的状态
        :param res: 需要检查的资源
        :param type_res: 需要检查的资源类型
        :param timeout: 监控时间限制
        :param expect_status: 预期状态
        :return: 返回True则说明是预期效果
        """
        t_beginning = time.time()
        while True:
            if expect_status in self.get_crm_res_status(res, type):
                s.prt_log(f'The status of {res} is {expect_status} now.', 0)
                return True
            else:
                time.sleep(1)

            seconds_passed = time.time() - t_beginning
            if timeout and seconds_passed > timeout:
                raise TimeoutError(res)


    def stop_res(self, res):
        # 执行停用res
        cmd = f'crm res stop {res}'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            return True
        else:
            s.prt_log(f"Stop {res} fail",1)

    def execute_delete(self, res):
        # 执行删除res
        cmd = f'crm conf del {res}'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log(f"Delete {res} success", 0)
            return True
        else:
            output = result['rst']
            re_str = re.compile(rf'INFO: hanging colocation:.*? deleted\nINFO: hanging order:.*? deleted\n')
            if s.re_search(re_str, output):
                s.prt_log(f"Delete {res} success(including colocation and order)", 0)
                return True
            else:
                s.prt_log(result['rst'],1)
                return False

    def delete_res(self, res, type):
        # 删除一个crm res，完整的流程
        if self.stop_res(res):
            if self.monitor_status(res,type,'Stopped'):
                if self.execute_delete(res):
                    return True
        s.prt_log(f"Delete {res} fail",1)

    def start_res(self, res):
        s.prt_log(f"try to start {res}", 0)
        cmd = f'crm res start {res}'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            return True

    # 刷新recourse状态，后续会用到
    def refresh(self):
        cmd = f'crm resource refresh'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log("refresh",0)
            return True


class IPaddr2():
    def __init__(self):
        pass

    @RollBack
    def create(self,name,ip,netmask):
        cmd = f'crm cof primitive {name} IPaddr2 params ' \
              f'ip={ip} cidr_netmask={netmask} ' \
              f'op monitor interval=10 timeout=20'
        cmd_result = execute_crm_cmd(cmd)
        if not cmd_result['sts']:
            # 创建失败，输出原命令报错信息
            s.prt_log(cmd_result['rst'],1)
            raise consts.CmdError
        else:
            s.prt_log(f'Create vip:{name} successfully',0)
            return True

    @RollBack
    def delete(self,name):
        obj_crm = CRMConfig()
        result = obj_crm.delete_res(name,type='IPaddr2')
        if not result:
            raise consts.CmdError
        else:
            s.prt_log(f'Delete vip:{name} successfully',0)
            return True

    @RollBack
    def modify(self,name,ip,netmask):
        cmd_ip = f'crm cof set {name}.ip {ip}'
        cmd_netmask = f'crm conf set {name}.cidr_netmask {netmask}'
        cmd_result_ip = execute_crm_cmd(cmd_ip)
        cmd_result_netmask = execute_crm_cmd(cmd_netmask)
        if not cmd_result_ip['sts'] or not cmd_result_netmask['sts']:
            # 创建失败，输出原命令报错信息
            s.prt_log(cmd_result_ip['rst'],1)
            s.prt_log(cmd_result_netmask['rst'],1)
            raise consts.CmdError
        else:
            s.prt_log(f'Modify vip:{name} (IP and Netmask) successfully',0)
            return True


class PortBlockGroup():
    # 需不需要block的限制关系？创建完block之后才能创建unblock？
    def __init__(self):
        self.block = None
        self.unblock = None

    @RollBack
    def create(self,name,ip,port,action):
        """
        :param name:
        :param ip:
        :param port:
        :param action: block/unblock
        :return:
        """
        if not action in ['block','unblock']:
            raise TypeError('Parameters "action" must be selected：block/unblock')

        cmd = f'crm cof primitive {name} portblock ' \
              f'params ip={ip} portno={port} protocol=tcp action={action} ' \
              f'op monitor timeout=20 interval=20'
        cmd_result = execute_crm_cmd(cmd)
        if not cmd_result['sts']:
            # 创建失败，输出原命令报错信息
            s.prt_log(cmd_result['rst'],1)
            raise consts.CmdError
        else:
            s.prt_log(f'Create portblock:{name} successfully',0)
            return True

    @RollBack
    def delete(self,name):
        obj_crm = CRMConfig()
        result = obj_crm.delete_res(name,type='portblock')
        if not result:
            raise consts.CmdError
        else:
            s.prt_log(f'Delete portblock:{name} successfully',0)
            return True

    @RollBack
    def modify(self,name,ip,port):
        cmd_ip = f'crm cof set {name}.ip {ip}'
        cmd_port = f'crm cof set {name}.portno {port}'
        cmd_result_ip = execute_crm_cmd(cmd_ip)
        cmd_result_port = execute_crm_cmd(cmd_port)
        if not cmd_result_ip['sts'] or not cmd_result_port['sts']:
            s.prt_log(cmd_result_ip['rst'],1)
            s.prt_log(cmd_result_port['rst'], 1)
            raise consts.CmdError
        else:
            s.prt_log(f"Modify portblock:{name} (IP and Port) successfully",0)
            return True



class Colocation():
    def __init__(self):
        pass

    @classmethod
    def create(cls,name,target1,target2):
        cmd = f'crm cof colocation {name} inf: {target1} {target2}'
        cmd_result = execute_crm_cmd(cmd)
        if not cmd_result['sts']:
            # 创建失败，输出原命令报错信息
            s.prt_log(cmd_result['rst'],1)
            raise consts.CmdError
        else:
            s.prt_log(f'Create colocation:{name} successfully',0)
            return True

    @classmethod
    def delete(cls,name):
        cmd = f'crm conf del {name}'
        result = execute_crm_cmd(cmd)


class Order():
    def __init__(self):
        pass

    @classmethod
    def create(cls,name, target1 ,target2):
        cmd = f'crm cof order {name} {target1} {target2}'
        cmd_result = execute_crm_cmd(cmd)
        if not cmd_result['sts']:
            # 创建失败，输出原命令报错信息
            s.prt_log(cmd_result['rst'],1)
            raise consts.CmdError
        else:
            s.prt_log(f'Create order:{name} successfully',0)
            return True

    @classmethod
    def delete(cls,name):
        cmd = f'crm conf del {name}'
        result = execute_crm_cmd(cmd)


class ISCSITarget():
    def __init__(self):
        pass

    @RollBack
    def create(self,name,iqn,ip,port):
        cmd = f'crm cof primitive {name} iSCSITarget params iqn="{iqn}" implementation=lio-t portals="{ip}:{port}" op start timeout=50 stop timeout=40 op monitor interval=15 timeout=40 meta target-role=Stopped'
        cmd_result = execute_crm_cmd(cmd)
        if not cmd_result['sts']:
            # 创建失败，输出原命令报错信息
            s.prt_log(cmd_result['rst'],1)
            raise consts.CmdError
        else:
            # s.prt_log(f'Create iscsitarget:{name} successfully',0)
            return True

    @RollBack
    def modify_iqn(self,name,iqn):
        cmd = f'crm conf set {name}.iqn {iqn}'
        cmd_result = execute_crm_cmd(cmd)
        if not cmd_result['sts'] :
            s.prt_log(cmd_result['rst'],1)
            raise consts.CmdError
        else:
            s.prt_log(f"Modify iSCSITarget:{name} (iqn) successfully",0)
            return True


    @RollBack
    def modify_portal(self,name,ip,port):
        cmd = f'crm cof set {name}.portals {ip}:{port}'
        cmd_result = execute_crm_cmd(cmd)
        if not cmd_result['sts'] :
            s.prt_log(cmd_result['rst'],1)
            raise consts.CmdError
        else:
            s.prt_log(f"Modify iSCSITarget:{name} (portal) successfully",0)
            return True


    @RollBack
    def delete(self,name):
        obj_crm = CRMConfig()
        result = obj_crm.delete_res(name,type='iSCSITarget')
        if not result:
            raise consts.CmdError
        else:
            s.prt_log(f'Delete iSCSITarget:{name} successfully',0)
            return True


    def start(self, name):
        pass

    def stop(self, name):
        pass


class ISCSILogicalUnit():
    def __init__(self):
        self.js = iscsi_json.JsonOperation()
        self.list_res_created = []


    # @RollBack
    def create(self, name, target_iqn, lunid, path, initiator):
        cmd = f'crm conf primitive {name} iSCSILogicalUnit params ' \
            f'target_iqn="{target_iqn}" ' \
            f'implementation=lio-t ' \
            f'lun={lunid} ' \
            f'path={path} ' \
            f'allowed_initiators="{initiator}" ' \
            f'op start timeout=40 interval=0 ' \
            f'op stop timeout=40 interval=0 ' \
            f'op monitor timeout=40 interval=15 ' \
            f'meta target-role=Stopped'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            # s.prt_log(f"Create iSCSILogicalUnit:{name} successfully",0)
            return True
        else:
            raise consts.CmdError


    # @RollBack
    def delete(self,name):
        obj_crm = CRMConfig()
        result = obj_crm.delete_res(name,type='iSCSILogicalUnit')
        if not result:
            raise consts.CmdError
        else:
            # s.prt_log(f'Delete iSCSILogicalUnit:{name} successfully',0)
            return True


    # @RollBack
    def modify_initiators(self,name,list_iqns):
        iqns = ' '.join(list_iqns)
        cmd = f"crm config set {name}.allowed_initiators \"{iqns}\""
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log(f"Modify the allowed initiators of {name} successfully",0)
            return True
        else:
            s.prt_log(result['rst'],1)
            raise consts.CmdError


    def modify_target_iqn(self,name,target_iqn):
        # 适用于target_iqn只有一个的情况（一个target只使用一个portal）
        cmd = f"crm config set {name}.target_iqn \"{target_iqn}\""
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log(f"Modify the target iqn of {name} successfully",0)
            return True
        else:
            s.prt_log(result['rst'],1)
            raise consts.CmdError


    def create_mapping(self,name,target,list_iqn):
        path = self.js.json_data['Disk'][name]
        lunid = int(path[-4:]) - 1000
        initiator = ' '.join(list_iqn)
        target_iqn = self.js.json_data['Target'][target]['target_iqn']
        portal = self.js.json_data['Target'][target]['portal']

        try:
            # 执行iscsilogicalunit创建
            self.create(name,target_iqn,lunid,path,initiator)
            self.list_res_created.append(name)

            #Colocation和Order创建
            Colocation.create(f'col_{name}', name, target)
            Order.create(f'or_{name}', target, name)
            Order.create(f'or_{name}_prtblk_off', name, f'{portal}_prtblk_off')
            s.prt_log(f'create colocation:co_{name}, order:or_{name} success', 0)
        except Exception as ex:
            # 回滚（暂用这种方法）
            s.prt_log('Fail to create iSCSILogicalUnit', 1)
            for i in self.list_res_created:
                self.delete(i)
            print('Failed during creation, the following is the error message：')
            print(str(traceback.format_exc()))
            return False

        else:
            #启动资源,成功与否不影响创建
            obj_crm = CRMConfig()
            obj_crm.start_res(name)
            obj_crm.monitor_status(name, 'iSCSILogicalUnit', 'Started')

        # 验证？
        return True

