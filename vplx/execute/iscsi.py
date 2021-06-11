# coding=utf-8
import time
import copy
import traceback

import iscsi_json
import sundry as s
from execute.linstor_api import LinstorAPI
from execute.crm import RollBack,CRMData, CRMConfig,IPaddr2,PortBlockGroup,Colocation,Order,ISCSITarget,ISCSILogicalUnit
import log
import consts


class IscsiConfig():
    def __init__(self, data_current, data_changed):
        self.logger = log.Log()
        dict_current = self.get_map_relation(data_current)
        dict_changed = self.get_map_relation(data_changed)

        self.diff, self.recover = self.get_dict_diff(dict_current, dict_changed)
        self.delete = self.diff['delete']
        self.create = self.diff['create']
        self.modify = self.diff['modify']

        if any([self.modify, self.delete]):
            self.obj_crm = CRMConfig()

        self.obj_iscsiLU = ISCSILogicalUnit()

        # 记载需要进行恢复的disk
        self.recovery_list = {'delete': set(), 'create': {}, 'modify': {}}

    def get_map_relation(self, data):
        dict_map_relation = {}
        for disk in data['Disk']:
            dict_map_relation.update({disk: set()})
        try:
            for map in data['Map'].values():
                for dg in map['DiskGroup']:
                    for disk in data['DiskGroup'][dg]:
                        set_iqn = set()
                        for hg in map['HostGroup']:
                            for host in data['HostGroup'][hg]:
                                set_iqn.add(data['Host'][host])
                        dict_map_relation[disk] = dict_map_relation[disk] | set_iqn
        except KeyError as key:
            s.prt_log(f'{key} does not exist in the configuration file, please check', 2)

        return dict_map_relation

    def get_dict_diff(self, dict1, dict2):
        # 判断dict2有没有dict1没有的key，如有dict1进行补充
        ex_key = dict2.keys() - dict1.keys()
        if ex_key:
            for i in ex_key:
                dict1.update({i: set()})

        diff = {'delete': set(), 'create': {}, 'modify': {}}
        recover = {'delete': set(), 'create': {}, 'modify': {}}
        for key in dict1:
            if set(dict1[key]) != set(dict2[key]):
                if not dict2[key]:
                    diff['delete'].add(key)
                    recover['create'].update({key: dict1[key]})
                elif not dict1[key]:
                    diff['create'].update({key: dict2[key]})
                    recover['delete'].add(key)
                else:
                    diff['modify'].update({key: dict2[key]})
                    recover['modify'].update({key: dict1[key]})

        self.logger.write_to_log('DATA', 'iSCSILogicalUnit', 'Data to be modified', '', diff)
        return diff, recover

    def show_info(self):
        nl = '\n'
        info = []
        if not any([self.create,self.delete,self.modify]):
            return ['Will not have any effect']
        if self.create:
            info_create = f'''create:\n{''.join([f"{disk}'s iqn ==> {','.join(iqn)}{nl}" for disk,iqn in self.create.items()])}'''
            info.append(info_create)
        if self.delete:
            info_delete = f'delete:\n{",".join(self.delete)}'
            info.append(info_delete)
        if self.modify:
            info_modify = f'''modify:\n{''.join([f"{disk}'s iqn ==> {','.join(iqn)}{nl}" for disk,iqn in self.modify.items()])}'''
            info.append(info_modify)
        return info


    def create_iscsilogicalunit(self,target):
        for disk, iqn in self.create.items():
            self.recovery_list['delete'].add(disk)
            self.obj_iscsiLU.create_mapping(disk, target, iqn)

    def delete_iscsilogicalunit(self):
        for disk in self.delete:
            self.recovery_list['create'].update({disk: self.recover['create'][disk]})
            self.obj_iscsiLU.delete(disk)

    def modify_iscsilogicalunit(self):
        for disk, iqn in self.modify.items():
            self.recovery_list['modify'].update({disk: self.recover['modify'][disk]})
            self.obj_iscsiLU.modify_initiators(disk, iqn)


    # 回滚功能，暂不调用
    def rollback(self):
        print("Mapping relationship rollback")
        for disk, iqn in self.recovery_list['create'].items():
            pass
            # 这里的回滚需要去获取到原lun的target,待处理
            # self.obj_iscsiLU.create_mapping(disk,target,iqn)
        for disk in self.recovery_list['delete']:
            self.obj_iscsiLU.delete(disk)
        for disk, iqn in self.recovery_list['modify'].items():
            self.obj_iscsiLU.modify_initiators(disk, iqn)
        print("Mapping relationship rollback ends")

    def comfirm_modify(self):
        print('\n'.join(self.show_info()))
        print(f'Are you sure? y/n')
        answer = s.get_answer()
        if not answer in ['y', 'yes', 'Y', 'YES']:
            s.prt_log(f'Cancel operation', 2)

    def crm_conf_change(self,target=None):
        try:
            self.create_iscsilogicalunit(target)
            self.delete_iscsilogicalunit()
            self.modify_iscsilogicalunit()
        except consts.CmdError:
            s.prt_log('Command execution failed',1)
            self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
            # self.rollback()
        except Exception:
            s.prt_log('Unknown exception',1)
            self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
            # self.rollback()


# 问题，这个disk数据是根据LINSTOR来的，那么是不是进行iscsi命令之前，需要更新这个数据，或者进行校验？
class Disk():
    """
    Disk
    """

    def __init__(self):
        self.js = iscsi_json.JsonOperation()

    def update_disk(self):
        # 更新disk数据并返回
        linstor = LinstorAPI()
        resource_all = linstor.get_resource()
        disks = {}
        for res in resource_all:
            # Resource,DeviceName
            disks.update({res['Resource']: res['DeviceName']})

        self.js.cover_data('Disk', disks)
        self.js.commit_data()
        return disks

    def show(self, disk):
        disk_all = self.update_disk()
        list_header = ["ResourceName", "Path"]
        list_data = []
        if disk == 'all' or disk is None:
            # show all
            for disk, path in disk_all.items():
                list_data.append([disk, path])
        else:
            # show one
            if self.js.check_key('Disk', disk):
                list_data.append([disk, disk_all[disk]])

        table = s.make_table(list_header, list_data)
        s.prt_log(table, 0)
        return list_data


class Host():
    """
    Host
    """

    def __init__(self):
        self.js = iscsi_json.JsonOperation()



    def _get_all_targetIqn(self):
        data = self.js.json_data['Target']
        return [x['target_iqn'] for x in data.values()]

    def _check_iqn_availability(self,iqn):
        data = self.js.json_data['Host']
        if not iqn in [x for x in data.values()]:
            return True

    def _check_iqn_format(self, iqn):
        """
        判断iqn是否符合格式
        """
        result = s.re_findall(
            r'^iqn\.\d{4}-\d{2}\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+(:[a-zA-Z0-9.:-]+)?$',
            iqn)
        return True if result else False

    def create(self, host, iqn):
        if self.js.check_key('Host', host):
            s.prt_log(f"Fail! The Host {host} already existed.", 1)
            return
        if not self._check_iqn_format(iqn):
            s.prt_log(f"The format of IQN is wrong. Please confirm and fill in again.", 1)
            return

        if not self._check_iqn_availability(iqn):
            s.prt_log(f"The iqn has been used",1)
            return

        self.js.update_data("Host", host, iqn)
        self.js.commit_data()
        s.prt_log("Create success!", 0)
        return True

    def show(self, host):
        list_header = ["HostName", "IQN"]
        list_data = []
        host_all = self.js.json_data['Host']
        if host == 'all' or host is None:
            # show all
            for host, iqn in host_all.items():
                list_data.append([host, iqn])
        else:
            # show one
            if self.js.check_key('Host', host):
                list_data.append([host, host_all[host]])
        table = s.make_table(list_header, list_data)
        s.prt_log(table, 0)
        return list_data


    def delete(self, host):
        if not self.js.check_key('Host',host):
            s.prt_log(f"Fail！Can't find {host}", 1)
            return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.delete_data('Host', host)
        self.js.arrange_data('Host', host)
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()
        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        self.js.commit_data()
        s.prt_log(f"Delete {host} successfully", 0)

    def modify(self, host, iqn):
        if not self.js.check_key('Host', host):
            s.prt_log(f"Fail! Can't find {host}", 1)
            return
        if not self._check_iqn_format(iqn):
            s.prt_log(f"The format of IQN is wrong. Please confirm and fill in again.", 1)
            return

        if not self._check_iqn_availability(iqn):
            s.prt_log(f"The iqn has been used",1)
            return


        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.update_data('Host', host, iqn)
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        self.js.commit_data()
        s.prt_log(f"Modify {host} successfully", 0)


class DiskGroup():
    """
    DiskGroup
    """

    def __init__(self):
        # 更新json文档中的disk信息
        disk = Disk()
        disk.update_disk()
        self.js = iscsi_json.JsonOperation()

    def create(self, diskgroup, disk):
        if self.js.check_key('DiskGroup', diskgroup):
            s.prt_log(f'Fail! The Disk Group {diskgroup} already existed.', 1)
            return
        for i in disk:
            if self.js.check_key('Disk', i) == False:
                s.prt_log(f"Fail! Can't find {i}.Please give the true name.", 1)
                return

        self.js.update_data('DiskGroup', diskgroup, disk)
        self.js.commit_data()
        s.prt_log("Create success!", 0)
        return True

    def show(self, dg):
        list_header = ["DiskgroupName", "DiskName"]
        list_data = []
        hg_all = self.js.json_data['DiskGroup']

        if dg == 'all' or dg is None:
            # show all
            for dg, disk in hg_all.items():
                list_data.append([dg, ' '.join(disk)])
        else:
            # show one
            if self.js.check_key('DiskGroup', dg):
                list_data.append([dg, ' '.join(hg_all[dg])])

        table = s.make_table(list_header, list_data)
        s.prt_log(table, 0)
        return list_data


    def delete(self, dg):
        if not self.js.check_key('DiskGroup', dg):
            s.prt_log(f"Fail! Can't find {dg}", 1)
            return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.delete_data('DiskGroup', dg)
        self.js.arrange_data('DiskGroup', dg)
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()
        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        self.js.commit_data()
        s.prt_log(f"Delete {dg} success!", 0)

    def add_disk(self, dg, list_disk):
        if not self.js.check_key('DiskGroup', dg):
            s.prt_log(f"Fail！Can't find {dg}", 1)
            return
        for disk in list_disk:
            if disk in self.js.json_data['DiskGroup'][dg]:
                s.prt_log(f'{disk} already exists in {dg}', 1)
                return
            if not self.js.check_key("Disk", disk):
                s.prt_log(f'The disk does not exist in the configuration file and cannot be added', 1)
                return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.append_member('DiskGroup', dg, list_disk)
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)
        self.js.commit_data()

    def remove_disk(self, dg, list_disk):
        if not self.js.check_key('DiskGroup', dg):
            s.prt_log(f"Fail！Can't find {dg}", 1)
            return
        for disk in list_disk:
            if not disk in self.js.json_data['DiskGroup'][dg]:
                s.prt_log(f'{disk} does not exist in {dg} and cannot be removed', 1)
                return


        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.remove_member('DiskGroup', dg, list_disk)
        if not self.js.json_data['DiskGroup'][dg]:
            self.js.delete_data('DiskGroup', dg)
            self.js.arrange_data('DiskGroup', dg)
            print(f'{dg} and the map related to {dg} have been modified/deleted')

        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        self.js.commit_data()

    """
    hostgroup 操作
    """


class HostGroup():
    def __init__(self):
        self.js = iscsi_json.JsonOperation()

    def create(self, hostgroup, host):
        if self.js.check_key('HostGroup', hostgroup):
            s.prt_log(f'Fail! The HostGroup {hostgroup} already existed.', 1)
            return
        for i in host:
            if self.js.check_key('Host', i) == False:
                s.prt_log(f"Fail! Can't find {i}.Please give the true name.", 1)
                return

        self.js.update_data('HostGroup', hostgroup, host)
        self.js.commit_data()
        s.prt_log("Create success!", 0)
        return True

    def show(self, hg):
        list_header = ["HostGroupName", "HostName"]
        list_data = []
        hg_all = self.js.json_data['HostGroup']

        if hg == 'all' or hg is None:
            # show all
            for hg, host in hg_all.items():
                list_data.append([hg, ' '.join(host)])
        else:
            # show one
            if self.js.check_key('HostGroup', hg):
                list_data.append([hg, ' '.join(hg_all[hg])])

        table = s.make_table(list_header, list_data)
        s.prt_log(table, 0)
        return list_data


    def delete(self, hg):
        if not self.js.check_key('HostGroup', hg):
            s.prt_log(f"Fail! Can't find {hg}", 1)
            return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.delete_data('HostGroup', hg)
        self.js.arrange_data('HostGroup', hg)
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()
        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        self.js.commit_data()
        s.prt_log(f"Delete {hg} success!", 0)

    def add_host(self, hg, list_host):
        if not self.js.check_key('HostGroup', hg):
            s.prt_log(f"Fail！Can't find {hg}", 1)
            return
        for host in list_host:
            if host in self.js.json_data['HostGroup'][hg]:
                s.prt_log(f'{host} already exists in {hg}', 1)
                return
            if not self.js.check_key("Host", host):
                s.prt_log(f'{host} does not exist in the configuration file and cannot be added', 1)
                return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.append_member('HostGroup', hg, list_host)
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        # 配置文件更新修改的资源
        self.js.commit_data()

    def remove_host(self, hg, list_host):
        if not self.js.check_key('HostGroup', hg):
            s.prt_log(f"Fail！Can't find {hg}", 1)
            return
        for host in list_host:
            if not host in self.js.json_data['HostGroup'][hg]:
                s.prt_log(f'{host} does not exist in {hg} and cannot be removed', 1)
                return
        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.remove_member('HostGroup', hg, list_host)
        if not self.js.json_data['HostGroup'][hg]:
            self.js.delete_data('HostGroup', hg)
            self.js.arrange_data('HostGroup',hg)
            print(f'{hg} and the map related to {hg} have been modified/deleted')
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        # 配置文件的改变
        self.js.commit_data()

    """
    map操作
    """


class Map():
    def __init__(self):
        self.js = iscsi_json.JsonOperation()
        disk = Disk()
        disk.update_disk()

        # 用于收集创建成功的resource
        # self.target_name, self.target_iqn = self.get_target()


    def create(self, map, target, list_hg, list_dg):
        """
        创建map
        :param map:
        :param hg: list,
        :param dg: list,
        :return:T/F
        """
        # 创建前的检查
        if self.js.check_key('Map', map):
            s.prt_log(f'The Map "{map}" already existed.', 1)
            return
        if not self.js.check_key('Target', target):
            s.prt_log(f"Can't find {target}", 1)
            return

        for hg in list_hg:
            if not self.js.check_key('HostGroup', hg):
                s.prt_log(f"Can't find {hg}", 1)
                return
        for dg in list_dg:
            if not self.js.check_key('DiskGroup', dg):
                s.prt_log(f"Can't find {dg}", 1)
                return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.update_data('Map', map, {'HostGroup': list_hg, 'DiskGroup': list_dg})
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)

        # 已经被使用过的disk(ilu)需不需要提示
        dict_disk_inuse = obj_iscsi.modify
        if dict_disk_inuse:
            s.prt_log(f"Disk:{','.join(dict_disk_inuse.keys())} has been mapped,will modify their allowed initiators",0)

        obj_iscsi.create_iscsilogicalunit(target)
        obj_iscsi.modify_iscsilogicalunit()

        self.js.commit_data()
        s.prt_log('Create map success!', 0)
        return True

    def show(self, map):
        list_header = ["MapName", "HostGroup", "DiskGroup"]
        list_data = []
        map_all = self.js.json_data['Map']

        if map == 'all' or map is None:
            # show all
            for map, data in map_all.items():
                list_data.append([map, " ".join(data['HostGroup']), " ".join(data['DiskGroup'])])
        else:
            # show one
            if self.js.check_key('Map', map):
                list_data.append([map, " ".join(map_all[map]['HostGroup']), " ".join(map_all[map]['DiskGroup'])])

        table = s.make_table(list_header, list_data)
        s.prt_log(table, 0)
        return list_data


    #  执行map展示的时候，会展示对应dg和hg的数据（全部三个表格），暂时保留代码
    # def get_spe_map(self, map):
    #     list_hg = []
    #     list_dg = []
    #     if not self.js.check_key('Map', map):
    #         s.prt_log('No map data', 2)
    #     # {map1: {"HostGroup": [hg1, hg2], "DiskGroup": [dg1, dg2]}
    #     map_data = self.js.get_data('Map').get(map)
    #     hg_list = map_data["HostGroup"]
    #     dg_list = map_data["DiskGroup"]
    #     for hg in hg_list:
    #         host = self.js.get_data('HostGroup').get(hg)
    #         for i in host:
    #             iqn = self.js.get_data('Host').get(i)
    #             list_hg.append([hg, i, iqn])
    #     for dg in dg_list:
    #         disk = self.js.get_data('DiskGroup').get(dg)
    #         for i in disk:
    #             path = self.js.get_data('Disk').get(i)
    #             list_dg.append([dg, i, path])
    #     return [{map: map_data}, list_hg, list_dg]
    #
    # def show_spe_map(self, map):
    #     list_data = self.get_spe_map(map)
    #     header_map = ["MapName", "HostGroup", "DiskGroup"]
    #     header_host = ["HostGroup", "HostName", "IQN"]
    #     header_disk = ["DiskGroup", "DiskName", "Disk"]
    #     table_map = s.show_map_data(header_map, list_data[0])
    #     table_hg = s.show_spe_map_data(header_host, list_data[1])
    #     table_dg = s.show_spe_map_data(header_disk, list_data[2])
    #     result = [str(table_map), str(table_hg), str(table_dg)]
    #     s.prt_log('\n'.join(result), 0)
    #     return list_data

    # 调用crm删除map
    def delete_map(self, map):
        if not self.js.check_key('Map', map):
            s.prt_log(f"Fail！Can't find {map}", 2)
            return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.delete_data('Map', map)
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()
        obj_iscsi.crm_conf_change()
        self.js.commit_data()
        s.prt_log("Delete map successfully", 0)
        return True

    def add_hg(self, map, list_hg):
        if not self.js.check_key('Map', map):
            s.prt_log(f"Fail！Can't find {map}", 1)
            return
        for hg in list_hg:
            if hg in self.js.json_data["Map"][map]["HostGroup"]:
                s.prt_log(f'{hg} already exists in {map}', 1)
                return
            if not self.js.check_key("HostGroup", hg):
                s.prt_log(f'{hg} does not exist in the configuration file and cannot be added', 1)
                return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.append_member('HostGroup', map, list_hg, type='Map')
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        # 提交json的修改
        self.js.commit_data()

    def add_dg(self, map, list_dg):
        if not self.js.check_key('Map', map):
            s.prt_log(f"Fail！Can't find {map}", 1)
            return
        for dg in list_dg:
            if dg in self.js.json_data["Map"][map]["DiskGroup"]:
                s.prt_log(f'{dg} already exists in {map}', 1)
                return
            if not self.js.check_key("DiskGroup", dg):
                s.prt_log(f'{dg} does not exist in the configuration file and cannot be added', 1)
                return

        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.append_member('DiskGroup', map, list_dg, type='Map')
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        # 提交json的修改
        self.js.commit_data()

    def remove_hg(self, map, list_hg):
        if not self.js.check_key('Map', map):
            s.prt_log(f"Fail！Can't find {map}", 1)
            return
        for hg in list_hg:
            if not hg in self.js.json_data["Map"][map]["HostGroup"]:
                s.prt_log(f'{hg} does not exist in {map} and cannot be removed', 1)
                return

        # 获取修改前的数据进行复制，之后进行对json数据的修改，从而去对比获取需要改动的映射关系再使用crm命令修改
        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.remove_member('HostGroup', map, list_hg, type='Map')
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        # 配置文件删除/移除成员
        if not self.js.json_data['Map'][map]['HostGroup']:
            self.js.delete_data('Map', map)
            print(f'{map} deleted')

        self.js.commit_data()

    def remove_dg(self, map, list_dg):
        # 验证
        if not self.js.check_key('Map', map):
            s.prt_log(f"Fail！Can't find {map}", 1)
            return
        for dg in list_dg:
            if not dg in self.js.json_data["Map"][map]["DiskGroup"]:
                s.prt_log(f'{dg} does not exist in {map} and cannot be removed', 1)
                return

        # 获取修改前的数据进行复制，之后进行对json数据的修改，从而去获取映射关系再使用crm命令修改
        json_data_before = copy.deepcopy(self.js.json_data)
        self.js.remove_member('DiskGroup', map, list_dg, type='Map')  # 对临时json对象的操作
        obj_iscsi = IscsiConfig(json_data_before, self.js.json_data)
        obj_iscsi.comfirm_modify()

        # 重新读取配置文件的数据，保证数据一致性
        json_data_now = self.js.read_json()
        if json_data_before == json_data_now:
            obj_iscsi.crm_conf_change()
        else:
            s.prt_log('The configuration file has been modified, please try again', 2)

        if not self.js.json_data['Map'][map]['DiskGroup']:
            self.js.delete_data('Map', map)
            print(f'{map} deleted')

        self.js.commit_data()


class Portal():
    def __init__(self):
        self.logger = log.Log()
        self.js = iscsi_json.JsonOperation()

    def create(self, name, ip, port=3260, netmask=24):
        if not self._check_name(name):
            s.prt_log(f'{name} naming does not conform to the specification', 1)
            return
        if not self._check_IP(ip):
            s.prt_log(f'{ip} does not meet specifications', 1)
            return
        if not self._check_port(port):
            s.prt_log(f'{port} does not meet specifications(Range：3260-65535)', 1)
            return
        if not self._check_netmask(netmask):
            s.prt_log(f'{netmask} does not meet specifications(Range：1-32)',1)
            return
        if self.js.check_key('Portal', name):
            s.prt_log(f'{name} already exists, please use another name', 1)
            return
        if self.js.check_in_res('Portal','ip',ip):
            s.prt_log(f'{ip} is already in use, please use another IP',1)
            return

        try:
            obj_ipadrr = IPaddr2()
            obj_ipadrr.create(name, ip, netmask)

            obj_portblock = PortBlockGroup()
            obj_portblock.create(f'{name}_prtblk_on', ip, port, action='block')
            obj_portblock.create(f'{name}_prtblk_off', ip, port, action='unblock')

            Colocation.create(f'col_{name}_prtblk_on', f'{name}_prtblk_on', name)
            Colocation.create(f'col_{name}_prtblk_off', f'{name}_prtblk_off', name)
            Order.create(f'or_{name}_prtblk_on', f'{name}_prtblk_on', name)
        except Exception as ex:
            self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
            RollBack.rollback('portal', ip,port,netmask)
            return

        # 验证
        status = self._check_status(name)

        if status == 'OK':
            self.js.update_data('Portal', name, {'ip': ip, 'port': str(port),'netmask':str(netmask),'target':[]})
            self.js.commit_data()
        elif status == 'NETWORK_ERROR':
            obj_ipadrr.delete(name)
            obj_portblock.delete(f'{name}_prtblk_on')
            obj_portblock.delete(f'{name}_prtblk_off')
            s.prt_log('The portal cannot be created normally due to the wrong IP address network segment or other network problems, please reconfigure', 1)


    def delete(self, name):
        if not self.js.check_key('Portal', name):
            s.prt_log(f"Fail！Can't find {name}", 1)
            return
        target = self.js.json_data['Portal'][name]['target']
        if target:
            s.prt_log(f'In use：{",".join(target)}. Can not delete', 1)
            return

        try:
            obj_ipadrr = IPaddr2()
            obj_ipadrr.delete(name)

            obj_portblock = PortBlockGroup()
            obj_portblock.delete(f'{name}_prtblk_on')
            obj_portblock.delete(f'{name}_prtblk_off')

        except Exception as ex:
            self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
            portal = self.js.json_data['Portal'][name]
            RollBack.rollback('portal', portal['ip'], portal['port'], portal['netmask'])
            # 恢复colocation和order
            if RollBack.dict_rollback['IPaddr2']:
                Colocation.create(f'col_{name}_prtblk_on', f'{name}_prtblk_on', name)
                Colocation.create(f'col_{name}_prtblk_off', f'{name}_prtblk_off', name)
                Order.create(f'or_{name}_prtblk_on', f'{name}_prtblk_on', name)
            return

        # 验证
        crm_data = CRMData()
        dict = crm_data.get_vip()
        if not name in dict.keys():
            self.js.delete_data('Portal',name)
            self.js.commit_data()
            print(f'Delete {name} successfully')
        else:
            print(f'Failed to delete {name}, please check')


    def modify(self, name, ip, port ,netmask):
        if not self.js.check_key('Portal',name):
            s.prt_log(f"Fail！Can't find {name}", 1)
            return
        flag_only_netmask = True
        portal = self.js.json_data['Portal'][name]

        # 指定了ip
        if ip:
            if not self._check_IP(ip):
                s.prt_log(f'{ip} does not meet specifications',1)
                return
            if self.js.check_in_res('Portal', 'ip', ip):
                s.prt_log(f'{ip} is already in use, please use another IP', 1)
                return
            flag_only_netmask = False
        else:
            ip = portal['ip']

        # 指定了port
        if port:
            if not self._check_port(port):
                s.prt_log(f'{port} does not meet specifications(Range：3260-65535)',1)
                return
            flag_only_netmask = False
        else:
            port = portal['port']
        # 指定了netmask
        if netmask:
            if not self._check_netmask(netmask):
                s.prt_log(f'{netmask} does not meet specifications(Range：1-32)', 1)
        else:
            netmask = portal['netmask']

        if portal['ip'] == ip and portal['port'] == str(port) and portal['netmask'] == str(netmask):
            s.prt_log(f'The parameters are the same, no need to modify',1)
            return

        if flag_only_netmask:
            # 只执行了netmask进行修改，这种情况下只需要对vip的netmask进行修改就行
            try:
                obj_ipadrr = IPaddr2()
                obj_ipadrr.modify(name, ip, netmask)

                obj_portblock = PortBlockGroup()
                obj_portblock.modify(f'{name}_prtblk_on', ip, port)
                obj_portblock.modify(f'{name}_prtblk_off', ip, port)
            except Exception as ex:
                self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
                RollBack.rollback('portal', portal['ip'],portal['port'],portal['netmask'])
                return

        else:
            if portal['target']:
                # 反馈修改影响
                print(f'Target：{",".join(portal["target"])}using this portal.These targets will be modified synchronously, whether to continue?y/n')
                answer = s.get_answer()
                if not answer in ['y', 'yes', 'Y', 'YES']:
                    s.prt_log('Modify canceled', 2)

                try:
                    obj_ipadrr = IPaddr2()
                    obj_ipadrr.modify(name, ip, netmask)

                    obj_portblock = PortBlockGroup()
                    obj_portblock.modify(f'{name}_prtblk_on', ip, port)
                    obj_portblock.modify(f'{name}_prtblk_off', ip, port)

                    obj_target = ISCSITarget()
                    for target in portal['target']:
                        obj_target.modify_portal(target, ip, port)
                except Exception as ex:
                    self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
                    RollBack.rollback('portal', portal['ip'], portal['port'], portal['netmask'])
                    return

            else:
                # 直接修改
                try:
                    obj_ipadrr = IPaddr2()
                    obj_ipadrr.modify(name, ip, netmask)

                    obj_portblock = PortBlockGroup()
                    obj_portblock.modify(f'{name}_prtblk_on', ip, port)
                    obj_portblock.modify(f'{name}_prtblk_off', ip, port)
                except Exception as ex:
                    self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
                    RollBack.rollback('portal', portal['ip'], portal['port'], portal['netmask'])
                    return

        # 暂不验证（见需求）

        # 更新数据
        portal['ip'] = ip
        portal['port'] = str(port)
        portal['netmask'] = str(netmask)
        for target in portal['target']:
            self.js.json_data['Target'][target]['ip'] = ip
            self.js.json_data['Target'][target]['port'] = str(port)
        self.js.commit_data()
        s.prt_log(f'Modify {name} successfully',0)


    def show(self):
        """
        用表格展示所有portal数据
        :return: all portal
        """
        list_header = ["Portal", "IP", "Port", "Netmask", "iSCSI Target"]
        list_data = []
        for portal, data in self.js.json_data['Portal'].items():
            if not data['target']:
                list_data.append([portal, data['ip'], data['port'], data['netmask'], '--'])
            else:
                list_data.append([portal, data['ip'], data['port'], data['netmask'], ",".join(data['target'])])
        table = s.make_table(list_header, list_data)
        s.prt_log(table, 0)
        return list_data


    def _check_name(self, name):
        result = s.re_search(r'^[a-zA-Z][a-zA-Z0-9_]*$', name)
        return True if result else False

    def _check_IP(self, ip):
        result = s.re_search(
            r'^((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})(\.((2([0-4]\d|5[0-5]))|[1-9]?\d|1\d{2})){3}$', ip)
        return True if result else False

    def _check_port(self, port):
        if not isinstance(port, int):
            return False
        return True if 3260 <= port <= 65535 else False

    def _check_netmask(self, netmask):
        if not isinstance(netmask, int):
            return False
        return True if 1 <= netmask <= 32 else False

    def _check_status(self, name):
        """
        验证portal的状态
        :param name: portal name
        :return:
        """
        time.sleep(1)
        obj_crm = CRMConfig()
        status = obj_crm.get_crm_res_status(name, type='IPaddr2')
        if status == 'Started':
            s.prt_log(f'Create {name} successfully', 1)
            return 'OK'
        elif 'Stopped' in status:
            failed_actions = obj_crm.get_failed_actions(name)
            if failed_actions == 0:
                return 'NETWORK_ERROR'
            elif failed_actions:
                s.prt_log(failed_actions, 1)
                return 'OTHER_ERROR'
            else:
                s.prt_log('Unknown error, please check', 1)
                return 'UNKNOWN_ERROR'
        else:
            s.prt_log(f'Failed to create {name}, please check', 1)
            return 'FAIL'


class Target():
    def __init__(self):
        self.logger = log.Log()
        self.js = iscsi_json.JsonOperation()


    def _get_all_targetIqn(self):
        data = self.js.json_data['Target']
        return [x['target_iqn'] for x in data.values()]


    def create(self,name, iqn, portal):
        # 前置判断
        if not self._check_name(name):
            s.prt_log(f'Wrong name:{name}. It must start with a letter and consist of letters, numbers, and "_" ', 1)
            return
        if not self._check_iqn(iqn):
            s.prt_log(f'Wrong iqn：{iqn}. Please enter the correct iqn.', 1)
            return

        if name in self.js.get_all_primitive_name():
            s.prt_log(f'This name is already in use, please use another name',1)
            return

        # if self.js.check_key('Target', name):
        #     s.prt_log(f'{name} already exists, please use another name', 1)
        #     return
        if not self.js.check_key('Portal',portal):
            s.prt_log(f'{portal} does not exist, please use the existing portal', 1)
            return

        # 检查iqn是否被使用(不进行集群其他节点的检查)
        if iqn in self._get_all_targetIqn():
            s.prt_log(f'The iqn:"{iqn}" has been used', 1)
            return

        # 执行
        dict_portal = self.js.json_data['Portal'][portal]
        ip = dict_portal['ip']
        port = dict_portal['port']

        try:
            ISCSITarget().create(name,iqn,ip,port)
            Order.create(f'or_{name}_{portal}',portal, name)
            Colocation.create(f'col_{name}_{portal}', name, portal)
            # raise TypeError
        except Exception as ex:
            self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
            RollBack.rollback('target', ip, port, iqn)
            return
        else:
            # 开启
            CRMConfig().start_res(name)

        # 验证
        status = self._check_status(name)
        if status == 'OK':
            self.js.update_data('Target', name, {'target_iqn': iqn, 'portal':portal,'lun':[]})
            self.js.json_data['Portal'][portal]['target'].append(name)
            self.js.commit_data()


    def modify(self, name, iqn, portal):
        if not self.js.check_key('Target',name):
            s.prt_log(f"Fail！Can't find {name}", 1)
            return
        if iqn:
            if not self._check_iqn(iqn):
                s.prt_log(f'Wrong iqn：{iqn}. Please enter the correct iqn.', 1)
                return
            # iqn的验证，同创建一样
            if iqn in self._get_all_targetIqn():
                s.prt_log(f'The iqn:"{iqn}" has been used', 1)
                return


        if portal:
            if portal == self.js.json_data['Target'][name]['portal']:
                s.prt_log(f'Same as the portal used, please specify another one', 1)
                return
            if not self.js.check_key('Portal',portal):
                s.prt_log(f"Fail！Can't find {portal}", 1)
                return

        dict_target = self.js.json_data['Target'][name]


        if portal == dict_target['portal'] and iqn == dict_target['target_iqn']:
            s.prt_log(f'The parameters are the same, no need to modify',1)
            return

        if dict_target['lun']:
            print(f'luns：{",".join(dict_target["lun"])}using this target.These luns will be suspended , whether to continue?y/n')
            answer = s.get_answer()
            if not answer in ['y', 'yes', 'Y', 'YES']:
                s.prt_log('Modify canceled', 2)


        obj_target = ISCSITarget()
        if iqn and iqn != dict_target['target_iqn']:
            try:
                obj_target.modify_iqn(name, iqn)
            except Exception as ex:
                self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
                RollBack.rollback('target','','',iqn)
                return
        if portal and portal != dict_target['portal']:
            dict_portal = self.js.json_data['Portal'][portal]
            try:
                obj_target.modify_portal(name, dict_portal['ip'], dict_portal['port'])
                Order.delete(f'or_{name}_{dict_target["portal"]}')
                Colocation.delete(f'col_{name}_{dict_target["portal"]}')
                Order.create(f'or_{name}_{portal}', portal, name)
                Colocation.create(f'col_{name}_{portal}', name, portal)
            except Exception as ex:
                self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
                RollBack.rollback('target',dict_portal['ip'],dict_portal['port'],'')
                Order.delete(f'or_{name}_{portal}')
                Colocation.delete(f'col_{name}_{portal}')
                Order.create(f'or_{name}_{dict_target["portal"]}', dict_target['portal'], name)
                Colocation.create(f'col_{name}_{dict_target["portal"]}', name, dict_target['portal'])
                return

        # 对有影响的lun做修改，有修改iqn的时候才影响
        if iqn:
            for lun in dict_target['lun']:
                # 修改这些lun的target_iqn
                try:
                    ISCSILogicalUnit().modify_target_iqn(lun,iqn)
                except Exception as ex:
                    self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
                    # 回滚待设置
                    return

        # 验证及数据更新
        crm_data = CRMData()
        target_now = crm_data.get_target()[name]
        json_data_target = self.js.json_data['Target'][name]
        json_data_portal = self.js.json_data['Portal']
        if iqn:
            if iqn == target_now['target_iqn']:
                json_data_target['target_iqn'] = iqn
        if portal:
            if dict_portal['ip'] == target_now['ip'] and dict_portal['port'] == target_now['port']:
                # lun = dict_portal['lun']
                # portal = self.js.json_data['Target'][name]['portal']
                json_data_portal[portal]['target'].append(name)
                json_data_portal[json_data_target['portal']]['target'].remove(name)
                json_data_target['portal'] = portal

        self.js.cover_data('Portal',json_data_portal)
        self.js.update_data('Target', name, json_data_target)
        self.js.commit_data()
        s.prt_log(f'Modify {name} successfully', 0)


    def delete(self, name):
        if not self.js.check_key('Target', name):
            s.prt_log(f"Fail！Can't find {name}", 1)
            return


        dict_target = self.js.json_data['Target'][name]
        lun = dict_target['lun']
        if lun:
            s.prt_log(f'In use：{",".join(lun)}. Can not delete', 1)
            return

        # 执行
        try:
            ISCSITarget().delete(name)
        except Exception as ex:
            self.logger.write_to_log('DATA', 'DEBUG', 'exception', 'Rollback', str(traceback.format_exc()))
            RollBack.rollback('target', dict_target['ip'], dict_target['port'], dict_target['iqn'])
            # 恢复colocation和order
            if RollBack.dict_rollback['ISCSITarget']:
                Order.create(f'or_{name}_{dict_target["portal"]}', dict_target["portal"], name)
                Colocation.create(f'col_{name}_{dict_target["portal"]}', name, dict_target["portal"])
            return

        # 验证
        if not CRMConfig().get_crm_res_status(name,'iSCSITarget'):
            portal = self.js.json_data['Target'][name]['portal']
            self.js.json_data['Portal'][portal]['target'].remove(name)
            self.js.delete_data('Target', name)
            self.js.commit_data()
            print(f'Delete target:{name} successfully')
        else:
            print(f'Failed to delete target:{name}, please check')


    def show(self):
        """
        用表格展示所有target数据
        :return: all portal
        """
        list_header = ["Target", "IQN", "Portal", "Status", "LUN(s)"]
        list_data = []

        dict_target = self.js.json_data['Target']
        dict_portal = self.js.json_data['Portal']
        for target, data in dict_target.items():
            status = CRMConfig().get_crm_res_status(target,'iSCSITarget')
            # 这里再决定好配置文件是否需要修改之后再进行具体的开发
            list_data.append([target, data['target_iqn'], data['portal'], status, ",".join(data['lun'])])

        table = s.make_table(list_header, list_data)
        s.prt_log(table, 0)
        return list_data


    def start(self,name):
        # 前置判断
        if not self.js.check_key('Target', name):
            s.prt_log(f'{name} does not exist', 1)
            return

        crm_config = CRMConfig()
        status = crm_config.get_crm_res_status(name, 'iSCSITarget')
        if status == 'Started':
            s.prt_log(f'{name} is in STARTED state', 1)
            return
        elif 'FAIL' in status:
            s.prt_log(f'{name} A is in FAILED state', 1)
            return


        # 执行
        crm_config.start_res(name)

        # 验证
        target = self.js.json_data['Target'][name]
        try:
            # 这里在设置的timeout内来监控状态，并且设置也还没有考虑luns
            crm_config.monitor_status_by_time(name,'iSCSITarget','Started',20)
            crm_config.monitor_status_by_time(f'{target["portal"]}_prtblk_off','portblock','Started',60)
        except TimeoutError as msg:
            s.prt_log(msg, 1)
        else:
            s.prt_log(f'{name} has been started', 0)


    def stop(self, name):
        # 前置判断
        if not self.js.check_key('Target', name):
            s.prt_log(f'{name} does not exist', 1)
            return

        crm_config = CRMConfig()
        status = crm_config.get_crm_res_status(name, 'iSCSITarget')
        if status == 'Stopped (disabled)':
            s.prt_log(f'{name} has been stopped', 1)
            return
        elif 'FAIL' in status:
            s.prt_log(f'{name} A is in FAILED state', 1)
            return
        elif status == 'Stopped':
            s.prt_log(f'{name} has been stopped for other reasons, but you can continue to stop it.(y/n)', 1)
            answer = s.get_answer()
            if not answer in ['y', 'yes', 'Y', 'YES']:
                s.prt_log('already cancelled', 2)

        s.prt_log('Trying to stop',0)
        # 执行
        crm_config.stop_res(name)

        #验证,验证的时间跟这个target被多少资源使用有关系，越多资源使用，需要的时间越多，暂时没有做特殊处理（比如通过判断被多少资源使用，动态赋予timeout的数值）
        try:
            crm_config.monitor_status_by_time(name,'iSCSITarget','Stopped (disabled)',timeout=60)
        except TimeoutError as msg:
            s.prt_log(msg,1)
        else:
            s.prt_log(f'{name} has been stopped', 0)


    def _check_name(self, name):
        result = s.re_search(r'^[a-zA-Z][a-zA-Z0-9_]*$', name)
        return True if result else False

    def _check_iqn(self, iqn):
        result = s.re_findall(
            r'^iqn\.\d{4}-(0[0-9]|1[0-9]|20)\.[a-z0-9][-a-z0-9]{0,62}(\.[a-z0-9][-a-z0-9]{0,62})+(:[a-z0-9.:-]+)?$',
            iqn)
        return True if result else False


    def _check_status(self, name):
        """
        验证target的状态
        :param name: portal name
        :return:
        """
        time.sleep(2)
        obj_crm = CRMConfig()
        status = obj_crm.get_crm_res_status(name, type='iSCSITarget')
        if status == 'Started':
            s.prt_log(f'Create {name} successfully', 1)
            return 'OK'
        elif 'Stopped' in status:
            failed_actions = obj_crm.get_failed_actions(name)
            if failed_actions:
                s.prt_log(failed_actions, 1)
                return 'OTHER_ERROR'
            else:
                s.prt_log('Unknown error, please check', 1)
                return 'UNKNOWN_ERROR'
        else:
            s.prt_log(f'Failed to create {name}, please check', 1)
            return 'FAIL'


class LogicalUnit():
    def __init__(self):
        self.logger = log.Log()
        self.js = iscsi_json.JsonOperation()


    def _get_all_drbdInuse(self):
        data = self.js.json_data['LogicalUnit']
        return [x['path'] for x in data.values()]

    def create(self,target,disk,hosts):
        """
        create iSCSI Logical Unit
        :param target:
        :param path: str
        :param initiator_iqns: list
        :return:
        """

        # 验证
        if not self.js.check_key('Disk',disk):
            s.prt_log(f"Fail！Can't find {disk}", 1)
            return

        # 一个disk只能被一个logical unit使用
        drbd_path = self.js.json_data['Disk'][disk]
        if drbd_path in self._get_all_drbdInuse():
            s.prt_log(f'The disk "{disk}" has been used',1)
            return

        if not self.js.check_key('Target',target):
            s.prt_log(f"Fail！Can't find {target}", 1)
            return


        for host in hosts:
            if self.js.check_key('Host', host) == False:
                s.prt_log(f"Fail! Can't find {host}.Please give the true name.", 1)
                return


        name = f'lun_{disk}'
        target_iqn = self._get_target_iqn(target)
        path = self._get_path(disk)
        lunid = str(int(path[-4:]) - 1000)
        initiator_iqns = self._get_initiator_iqns(hosts)
        portal = self.js.json_data['Target'][target]['portal']

        # 执行
        try:
            ISCSILogicalUnit().create(name,target_iqn,lunid,path," ".join(initiator_iqns))
            Colocation().create(f'col_{name}', name, target) # 这里的name，是指disk，还是logicalunit？
            Order().create(f'or_{name}', target, name)
            Order().create(f'or_{name}_prtblk_off', name, f'{portal}_prtblk_off')
        except Exception as ex:
            s.prt_log('出错，退出',1)
            return

        else:
            #启动资源
            CRMConfig().start_res(name)

        # 配置文件更新
        status = self._check_status(name)
        if status == 'OK':
            self.js.update_data('LogicalUnit', name, {'lun_id': lunid, 'target':target,'path':path,'initiators':initiator_iqns})
            self.js.json_data['Target'][target]['lun'].append(name)
            self.js.commit_data()


    def modify(self):
        # 可以设置修改target_iqn
        pass


    def delete(self,name):
        # 验证

        if not self.js.check_key('LogicalUnit',name):
            s.prt_log(f"Fail！Can't find {name}", 1)
            return


        # LogicalUnit正在使用中时，直接退出
        # dict_logicalunit = self.js.json_data['LogicalUnit'][name]
        # hosts = dict_logicalunit['hosts']
        # if hosts:
        #     s.prt_log(f'In use：{",".join(hosts)}. Can not delete', 1)
        #     return

        # 正在使用中时，交互确认
        if CRMConfig().get_crm_res_status(name,'iSCSILogicalUnit') == 'Started':
            print(f'resource {name} is running, confirm to delete? y/n')
            answer = s.get_answer()
            if not answer in ['y', 'yes', 'Y', 'YES']:
                s.prt_log('Delete canceled', 2)

        # 执行
        ISCSILogicalUnit().delete(name)

        # 验证
        if not CRMConfig().get_crm_res_status(name,'iSCSILogicalUnit'):
            target = self.js.json_data['LogicalUnit'][name]['target']
            self.js.json_data['Target'][target]['lun'].remove(name)
            self.js.delete_data('LogicalUnit', name)
            self.js.commit_data()
            print(f'Delete {name} successfully')
        else:
            print(f'Failed to delete {name}, please check')


    def show(self):
        """
        用表格展示所有logical unit数据
        :return: all logical unit
        """
        list_header = ["LogicalUnit", "Lun ID", "Target", "Path", "Hosts", "Status"]
        list_data = []

        dict_logicalunit = self.js.json_data['LogicalUnit']
        for target, data in dict_logicalunit.items():
            status = CRMConfig().get_crm_res_status(target,'iSCSILogicalUnit')
            hosts = self._get_host_data_for_show(data['initiators'])
            list_data.append([target, data['lun_id'], data['target'], data['path'], hosts, status])

        table = s.make_table(list_header, list_data)
        s.prt_log(table, 0)
        return list_data


    def add(self, logicalunit, hosts):
        if not self.js.check_key('LogicalUnit',logicalunit):
            s.prt_log(f"Fail！Can't find {logicalunit}", 1)
            return

        initiators_add = []
        for host in hosts:
            if not self.js.check_key("Host", host):
                s.prt_log(f"Fail！Can't find {host}", 1)
                return
            initiator = self.js.json_data['Host'][host]
            if initiator in self.js.json_data["LogicalUnit"][logicalunit]["initiators"]:
                s.prt_log(f'{host} is already on the "allowed initiators"', 1)
                return
            initiators_add.append(initiator)

        initiators = self.js.json_data['LogicalUnit'][logicalunit]['initiators']
        initiators.extend(initiators_add)
        ISCSILogicalUnit().modify_initiators(logicalunit,initiators)

        # 配置文件更新
        self.js.commit_data()


    def remove(self, logicalunit, hosts):
        if not self.js.check_key('LogicalUnit', logicalunit):
            s.prt_log(f"Fail！Can't find {logicalunit}", 1)
            return

        initiators_remove = []
        for host in hosts:
            if not self.js.check_key("Host", host):
                s.prt_log(f"Fail！Can't find {host}", 1)
                return
            initiator = self.js.json_data['Host'][host]
            if not initiator in self.js.json_data["LogicalUnit"][logicalunit]["initiators"]:
                s.prt_log(f'{host} is not in the "allowed initiators"', 1)
                return
            initiators_remove.append(initiator)

        initiators = self.js.json_data['LogicalUnit'][logicalunit]['initiators']
        initiators = list(set(initiators)-set(initiators_remove))

        if not initiators:
            s.prt_log('Please keep at least one initiators',1)
            return

        ISCSILogicalUnit().modify_initiators(logicalunit,initiators)

        # 配置文件更新
        self.js.json_data['LogicalUnit'][logicalunit]['initiators'] = initiators
        self.js.commit_data()


    def start(self, name):
        if not self.js.check_key('LogicalUnit', name):
            s.prt_log(f'{name} does not exist', 1)
            return

        crm_config = CRMConfig()
        status = crm_config.get_crm_res_status(name, 'iSCSILogicalUnit')
        if status == 'Started':
            s.prt_log(f'{name} is in STARTED state', 1)
            return
        elif 'FAIL' in status:
            s.prt_log(f'{name} A is in FAILED state', 1)
            return
        # 执行
        crm_config.start_res(name)

        # 验证, 还没有确定判断是否成功启动的条件
        try:
            crm_config.monitor_status_by_time(name,'iSCSILogicalUnit','Started',20)
        except TimeoutError as msg:
            s.prt_log(msg, 1)
        else:
            s.prt_log(f'{name} has been started', 0)


    def stop(self, name):
        # 前置判断
        if not self.js.check_key('LogicalUnit', name):
            s.prt_log(f'{name} does not exist', 1)
            return

        crm_config = CRMConfig()
        status = crm_config.get_crm_res_status(name, 'iSCSILogicalUnit')
        if status == 'Stopped (disabled)':
            s.prt_log(f'{name} has been stopped', 1)
            return
        elif 'FAIL' in status:
            s.prt_log(f'{name} A is in FAILED state', 1)
            return
        elif status == 'Stopped':
            s.prt_log(f'{name} has been stopped for other reasons, but you can continue to stop it.(y/n)', 1)
            answer = s.get_answer()
            if not answer in ['y', 'yes', 'Y', 'YES']:
                s.prt_log('already cancelled', 2)

        s.prt_log('Trying to stop', 0)
        # 执行
        crm_config.stop_res(name)

        # 验证
        try:
            crm_config.monitor_status_by_time(name, 'iSCSILogicalUnit', 'Stopped (disabled)', timeout=60)
        except TimeoutError as msg:
            s.prt_log(msg, 1)
        else:
            s.prt_log(f'{name} has been stopped', 0)


    def _get_path(self,disk):
        return self.js.json_data['Disk'][disk]

    def _get_target_iqn(self,target):
        return self.js.json_data['Target'][target]['target_iqn']

    def _get_initiator_iqns(self,hosts):
        return [self.js.json_data['Host'][host] for host in hosts]

    def _get_host_data_for_show(self,list_iqn):
        data_list = []
        for iqn in list_iqn:
            for k,v in self.js.json_data['Host'].items():
                if iqn == v:
                    one = f'{iqn}({k})'
                    break
            else:
                one = f'{iqn}()'
            data_list.append(one)
        return "\n".join(data_list)

    def _check_status(self, name):
        """
        验证iscsilogicalunit的状态
        :param name: portal name
        :return:
        """
        time.sleep(2)
        obj_crm = CRMConfig()
        status = obj_crm.get_crm_res_status(name, type='iSCSILogicalUnit')
        if status == 'Started':
            s.prt_log(f'Create {name} successfully', 1)
            return 'OK'
        elif 'Stopped' in status:
            failed_actions = obj_crm.get_failed_actions(name)
            if failed_actions:
                s.prt_log(failed_actions, 1)
                return 'OTHER_ERROR'
            else:
                s.prt_log('Unknown error, please check', 1)
                return 'UNKNOWN_ERROR'
        else:
            s.prt_log(f'Failed to create {name}, please check', 1)
            return 'FAIL'


class ISCSI():
    def __init__(self):
        self.js = iscsi_json.JsonOperation()
        self.crm = CRMData()
        self.crm.get_crm_st()


    def _get_portal(self,portal):
        data = self.js.json_data['Portal'][portal]
        status = self.crm.get_res_status(portal,type='IPaddr2')
        result = {"portals":{data['ip']:{"status":status}}}
        return result


    def _get_lun(self,lun):
        data = self.js.json_data['LogicalUnit'][lun]
        status = self.crm.get_res_status(lun,type='iSCSILogicalUnit')
        result = {"path":data['path'],"lun id":data['lun_id'],"status":status}
        return result


    def _get_initiators(self,host,luns):
        iqn = self.js.json_data['Host'][host]
        dict_luns = {}
        for lun in luns:
            dict_luns.update({lun:self._get_lun(lun)})
        result = {host:{"iqn":iqn,"map lun":len(luns)}}
        result[host].update(dict_luns)
        return result


    def _get_target(self,target,sep_initiator_list=None):
        data = self.js.json_data['Target'][target]
        status = self.crm.get_res_status(target,type='iSCSITarget')

        initiators = {}
        for iqn,luns in self._get_luns(target).items():
            host = self._get_host(iqn)
            if not sep_initiator_list:
                initiator_data = self._get_initiators(host, luns)
                initiators.update(initiator_data)
            elif sep_initiator_list and host in sep_initiator_list:
                initiator_data = self._get_initiators(host,luns)
                initiators.update(initiator_data)
                break

        portal = self._get_portal(data['portal'])
        result = {target:[data['target_iqn'],{"status":status},{"initiator":initiators},portal]}
        return result

    def show(self,sep_node_list=None,sep_target_list=None,sep_initiator_list=None):
        # 检查指定的参数是否在配值文件中
        result = {}
        for node, targets in self.crm.get_target_and_node().items():
            target_data = {}
            if not sep_node_list:
                for target in targets:
                    if sep_target_list and target in sep_target_list:
                        tg = self._get_target(target,sep_initiator_list)
                        target_data.update(tg)
                    elif not sep_target_list:
                        tg = self._get_target(target,sep_initiator_list)
                        target_data.update(tg)
                result.update({node:target_data})

            elif sep_node_list and node in sep_node_list:
                for target in targets:
                    if sep_target_list and target in sep_target_list:
                        tg = self._get_target(target,sep_initiator_list)
                        target_data.update(tg)
                    elif not sep_target_list:
                        tg = self._get_target(target,sep_initiator_list)
                        target_data.update(tg)
                result.update({node:target_data})

        import yaml
        print(yaml.dump(result,sort_keys=False))
        return result


    def _get_host(self,sep_iqn):
        for host,iqn in self.js.json_data['Host'].items():
            if iqn == sep_iqn:
                return host


    def _get_luns(self,target):
        luns = self.js.json_data['Target'][target]['lun']
        _dict = {}
        for lun in luns:
            initiators = self.js.json_data['LogicalUnit'][lun]['initiators']
            for initiator in initiators:
                if initiator in _dict.keys():
                    _dict[initiator].append(lun)
                else:
                    _dict.update({initiator: [lun]})

        return _dict

