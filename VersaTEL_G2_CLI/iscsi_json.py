import json
import consts
import sundry as s
from functools import wraps
import sys


class JsonOperation():
    def __init__(self):
        self.RPL = consts.glo_rpl()
        self.json_data = self.read_json()

    # 读取json文档
    @s.deco_json_operation('读取到的JSON数据')
    def read_json(self):
        try:
            json_data = open("iSCSI_Data.json", encoding='utf-8')
            json_dict = json.load(json_data)
            json_data.close()
            return json_dict

        except FileNotFoundError:
            with open('iSCSI_Data.json', "w") as fw:
                json_dict = {
                    "Host": {},
                    "Disk": {},
                    "HostGroup": {},
                    "DiskGroup": {},
                    "Map": {}}
                json.dump(json_dict, fw, indent=4, separators=(',', ': '))
            return json_dict
        except json.decoder.JSONDecodeError:
            print('Failed to read json file.')
            sys.exit()


    # 创建Host、HostGroup、DiskGroup、Map
    @s.deco_json_operation('JSON添加后的资源信息')
    def add_data(self, first_key, data_key, data_value):
        self.json_data[first_key].update({data_key: data_value})
        with open('iSCSI_Data.json', "w") as fw:
            json.dump(self.json_data, fw, indent=4, separators=(',', ': '))
        return self.json_data[first_key]



    def append_member(self,iscsi_type,target,member,type=None):
        if not isinstance(member,list):
            member = [member]
        if type == 'Map':
            list_member = self.get_data('Map')[target][iscsi_type]
        else:
            list_member = self.get_data(iscsi_type)[target]
        list_member.extend(member)
        self.add_data(iscsi_type,target,list(set(list_member)))




    def remove_member(self,iscsi_type,target,member,type=None):
        if not isinstance(member, list):
            member = [member]
        if type == 'Map':
            list_member = self.get_data('Map')[target][iscsi_type]
        else:
            list_member = self.get_data(iscsi_type)[target]
        for i in member:
            list_member.remove(i)
        self.add_data(iscsi_type,target,list(set(list_member)))



    # 删除Host、HostGroup、DiskGroup、Map
    @s.deco_json_operation('JSON删除后的资源信息')
    def delete_data(self, first_key, data_key):
        self.json_data[first_key].pop(data_key)
        with open('iSCSI_Data.json', "w") as fw:
            json.dump(self.json_data, fw, indent=4, separators=(',', ': '))
        return self.json_data[first_key]

    # 获取Host,Disk、Target，HostGroup、DiskGroup、Map的信息
    @s.deco_json_operation('JSON获取资源信息')
    def get_data(self, first_key):
        all_data = self.json_data[first_key]
        return all_data

    # 检查key值是否存在
    @s.deco_json_operation('JSON检查key值的结果')
    def check_key(self, first_key, data_key):
        if data_key in self.json_data[first_key]:
            return {'type': first_key, 'alias': data_key, 'result': True}
        else:
            return {'type': first_key, 'alias': data_key, 'result': False}

        # if not isinstance(data_key,list):
        #     if data_key in self.json_data[first_key]:
        #         return {'type':first_key,'alias':data_key, 'result':True}
        #     else:
        #         return {'type':first_key,'alias':data_key, 'result':False}
        # else:
        #     for i in data_key:
        #         if i in self.json_data[first_key]:
        #             pass
        #         else:
        #             return
        # return True


    # 检查value值是否存在
    @s.deco_json_operation('JSON检查value值的结果')
    def check_value(self, first_key, data_value):
        for key in self.json_data[first_key]:
            if data_value in self.json_data[first_key][key]:
                return {'type':first_key,'alias':data_value,'result':True}
        return {'type':first_key,'alias':data_value,'result':False}


    # 更新disk 可能需要注意的地方：没有限制可以修改的key
    @s.deco_json_operation(f'JSON更新资源信息')
    def update_data(self, first_key, data):
        self.json_data[first_key] = data
        with open('iSCSI_Data.json', "w") as fw:
            json.dump(self.json_data, fw, indent=4, separators=(',', ': '))
        return self.json_data[first_key]



    # 更新crm configure资源的信息
    @s.deco_json_operation('JSON更新CRM资源信息')
    def update_crm_conf(self, resource,vip,target):
        self.json_data.update({'crm': {}})
        self.json_data['crm'].update({'resource': resource})
        self.json_data['crm'].update({'vip': vip})
        self.json_data['crm'].update({'target': target})
        with open('iSCSI_Data.json', "w") as fw:
            json.dump(self.json_data, fw, indent=4, separators=(',', ': '))
        return self.json_data['crm']



    def check_value_in_key(self, type, key, value):
        """
        检查某个key值是否存在某个value值
        """
        if key in self.json_data[type]:
            if value in self.json_data[type][key]:
                return {'type': type, 'key': key, 'value': value, 'result': True}
            else:
                return {'type': type, 'key': key, 'value': value, 'result': False}

    def check_map_member(self,map,member,type):
        """
        检查某个member是否存在指定的map中
        :param map:
        :param hg:
        :param type: "HostGroup"/"DiskGroup"
        :return:
        """
        if member in self.json_data["Map"][map][type]:
            return True
        else:
            return False

    def get_hg_by_host(self,host):
        """
        通过host取到使用这个host的所有hg
        :param host:
        :return:list
        """
        list_host = []
        for hg,hg_member in self.json_data["HostGroup"].items():
            if host in hg_member:
                list_host.append(hg)
        return list_host


    def get_map_by_hg(self,hg):
        """
        通过hg取到使用这个hg的所有map
        :param hg:
        :return:list
        """
        list_map = []
        for map,map_member in self.json_data['Map'].items():
            if hg in map_member['HostGroup']:
                list_map.append(map)
        return list_map



    def get_disk_by_dg(self,list_dg):
        """
        通过list_dg获取到所有disk
        :param list_dg:
        :return:
        """
        list_disk = []
        for dg in list_dg:
            list_disk+=self.get_data('DiskGroup')[dg]
        return list(set(list_disk))


    def get_map_by_host(self,host):
        list_map = []
        list_hg = self.get_hg_by_host(host)
        for hg in list_hg:
            list_map+=self.get_map_by_hg(hg)
        return list_map

    def get_map_by_disk(self, disk):
        dg_dict = self.get_data("DiskGroup")
        map_dict = self.get_data("Map")
        # 根据disk获取dg
        dg_list = []
        for dg in dg_dict.items():
            if disk in dg[1]:
                dg_list.append(dg[0])
        # 根据dg获取map
        map_list = []
        for dg in dg_list:
            for map in map_dict.items():
                if dg in map[1]['DiskGroup']:
                    map_list.append(map[0])
        return list(set(map_list))


    def get_res_initiator(self,disk):
        """
        通过disk获取到对应iSCSILogicalUnit的allowed initiators
        allowed initiators即host的iqn
        :param disk:str
        :return:list
        """
        # 通过disk获取dg
        list_initiator = []
        list_hg = []
        list_host = []
        list_map = self.get_map_by_disk(disk)
        for map in list_map:
            list_hg+=self.get_data('Map')[map]['HostGroup']

        for hg in set(list_hg):
            for host in self.get_data('HostGroup')[hg]:
                list_host.append(host)

        for host in set(list_host):
            list_initiator.append(self.get_data('Host')[host])

        return list(set(list_initiator))


    def get_res_initiator_by_hg(self,hg):
        list_iqn = []
        if not isinstance(hg,list):
            hg = [hg]
        for hg_one in hg:
            for h in self.get_data('HostGroup')[hg_one]:
                iqn = self.get_data('Host')[h]
                list_iqn.append(iqn)

        return list(set(list_iqn))


    def get_disk_by_map(self,map):
        list_dg = []
        for dg in self.get_data('Map')[map]["DiskGroup"]:
            list_dg.append(dg)
        return self.get_disk_by_dg(list_dg)


    def get_iqn_by_map(self, map):
        hg_list = self.get_data('Map')[map]['HostGroup']
        iqn_list = self.get_iqn_by_hglist(hg_list)
        return iqn_list


    def get_iqn_by_hglist(self,hg_list):
        iqn_list = []
        for hg in hg_list:
            for host in self.get_data('HostGroup')[hg]:
                iqn = self.get_data('Host')[host]
                iqn_list.append(iqn)
        return list(set(iqn_list))

