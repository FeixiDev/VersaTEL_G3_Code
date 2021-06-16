import json
import threading
import sundry as s




class JsonOperation(object):
#     _instance_lock = threading.Lock()
    json_data = None

    def __init__(self):
        if self.json_data is None:
            self.json_data = self.read_json()


    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
#             with JsonOperation._instance_lock:
#                 if not hasattr(cls, '_instance'):
#                     JsonOperation._instance = super().__new__(cls)
            JsonOperation._instance = super().__new__(cls)
        return JsonOperation._instance


    # 读取json文档
    @s.deco_json('read json')
    def read_json(self):
        try:
            json_data = open("../vplx/map_config.json", encoding='utf-8')
            json_dict = json.load(json_data)
            json_data.close()
            return json_dict

        except FileNotFoundError:
            with open('../vplx/map_config.json', "w") as fw:
                json_dict = {
                    "Host": {},
                    "Disk": {},
                    "HostGroup": {},
                    "DiskGroup": {},
                    "Map": {},
                    "Portal":{},
                    "Target":{},
                    "LogicalUnit":{}}
                json.dump(json_dict, fw, indent=4, separators=(',', ': '))
            s.prt_log('The configuration file has been created.Please continue after synchronizing data.',2)
        except json.decoder.JSONDecodeError:
            s.prt_log('Failed to read configuration file.',2)

    @s.deco_json('commit data')
    def commit_data(self):
        with open('../vplx/map_config.json', "w") as fw:
            json.dump(self.json_data, fw, indent=4, separators=(',', ': '))
        return self.json_data


    # 检查key值是否存在
    @s.deco_json('check key')
    def check_key(self, key, target):
        """
        检查某个类型的目标是不是在存在
        """
        if target in self.json_data[key]:
            return True
        else:
            return False


    # 检查value值是否存在
    @s.deco_json('check value')
    def check_value(self, key, target):
        """
        检查目标是不是作为某种资源的使用
        """
        for data in self.json_data[key].values():
            if target in data:
                return True
        return False


    @s.deco_json('check if it is used')
    def check_in_res(self,res,member,target):
        """
        检查目标资源在不在某个res的成员里面，res：Map，Target，Portal
        :param res:
        :param member: 比如HostGroup/DiskGroup
        :param target:
        :return:
        """
        for data in self.json_data[res].values():
            if target in data[member]:
                return True
        return False


    # 更新Host、HostGroup、DiskGroup、Map的某一个成员的数据
    @s.deco_json('update data')
    def update_data(self, first_key, data_key, data_value):
        self.json_data[first_key].update({data_key: data_value})
        return self.json_data[first_key]


    # 更新该资源的全部数据
    @s.deco_json('update all data')
    def cover_data(self, first_key, data):
        self.json_data[first_key] = data
        return self.json_data[first_key]
    
    
    # 删除Host、HostGroup、DiskGroup、Map
    @s.deco_json('delete data')
    def delete_data(self, first_key, data_key):
        self.json_data[first_key].pop(data_key)
        return self.json_data[first_key]


    def append_member(self,iscsi_type,target,member,type=None):
        """
        :param iscsi_type:
        :param target:
        :param member: list
        :param type: 'DiskGroup'/'HostGroup'
        :return:
        """
        if type == 'Map':
            list_member = self.json_data['Map'][target][iscsi_type]
        else:
            list_member = self.json_data[iscsi_type][target]
        list_member.extend(member)

        if type == 'Map':
            dict_map = self.json_data['Map'][target]
            dict_map.update({iscsi_type:list_member})
            self.update_data('Map',target,dict_map)
        else:
            self.update_data(iscsi_type, target, list(set(list_member)))

    def remove_member(self,iscsi_type,target,member,type=None):
        if type == 'Map':
            list_member = self.json_data['Map'][target][iscsi_type]
        else:
            list_member = self.json_data[iscsi_type][target]

        for i in member:
            list_member.remove(i)

        if type == 'Map':
            dict_map = self.json_data['Map'][target]
            dict_map.update({iscsi_type:list_member})
            self.update_data('Map',target,dict_map)
        else:
            self.update_data(iscsi_type, target, list(set(list_member)))


    def arrange_data(self,type,res):
        """
        删除了传入的资源之后，处理与之相关的其他资源数据
        :param type: 被删除的资源类型 host/hg/dg
        :param res: 被删除的资源名称
        :return:
        """
        import copy
        data = copy.deepcopy(self.json_data)

        if type == 'Host':
            # 会影响到hg，map
            list_hg_delete = []
            for hg,list_host in data['HostGroup'].items():
                if res in list_host:
                    if len(list_host) > 1:
                        self.remove_member('HostGroup',hg,[res])
                    else:
                        list_hg_delete.append(hg)
                        self.delete_data('HostGroup',hg)
            for hg in list_hg_delete:
                for map,map_data in data['Map'].items():
                    if hg in map_data['HostGroup']:
                        if len(data['Map'][map]['HostGroup'])>1:
                            self.remove_member('HostGroup', map, [hg], type='Map')
                        else:
                            self.delete_data('Map', map)

        elif type == 'hg' or type == 'HostGroup':
            # 会影响到map
            for map,map_data in data['Map'].items():
                if res in map_data['HostGroup']:
                    if len(data['Map'][map]['HostGroup']) > 1:
                        self.remove_member('HostGroup', map, [res], type='Map')
                    else:
                        self.delete_data('Map', map)

        elif type == 'dg' or type == 'DiskGroup':
            # 会影响到map
            for map,map_data in data['Map'].items():
                if res in map_data['DiskGroup']:
                    if len(data['Map'][map]['DiskGroup']) > 1:
                        self.remove_member('DiskGroup', map, [res], type='Map')
                    else:
                        self.delete_data('Map', map)
        else:
            raise TypeError('type must be "host/hg/dg"')


    def get_all_primitive_name(self):
        """
        获取所有crm中的primitive资源名（对应配置文件中的portal,target,logicalunit）
        :return:
        """
        lst = list(self.json_data['Portal'].keys())
        lst.extend(list(self.json_data['Target'].keys()))
        lst.extend(list(self.json_data['LogicalUnit'].keys()))

        return lst



