# -*- coding:utf-8 -*-
import os
import re
import yaml
import pprint
from execute.linstor_api import LinstorAPI
import utils


# def exec_cmd(cmd):
#     """subprocess执行命令"""
#     p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
#     if p.returncode == 0:
#         result = p.stdout
#         result = result.decode() if isinstance(result, bytes) else result
#         # print("result", result)
#         return {"st": True, "rt": result}
#     else:
#         # print(f"  Failed to execute command: {cmd}")
#         print("  Error message:\n", p.stderr.decode())
#         return {"st": False, "rt": p.stderr}


class ClusterLVM(object):
    def __init__(self, node):
        self.api = LinstorAPI()
        try:
            self.sp = self.api.get_storagepool([node])
            self.res = self.api.get_resource([node])
        except AttributeError:
            self.sp = None
            self.res = None
            # print(f"Can't get LINSTOR resource on {node}.")

        if node == utils.get_hostname():
            self.conn = None
        else:
            self.conn = utils.SSHConn(node)

    def create_linstor_thinpool(self, name, node, list_pv):
        pv = ' '.join(list_pv)
        cmd = f"linstor ps cdp --pool-name {name} lvmthin {node} {pv}  --vdo-logical-size 5M"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to create Thinpool {name} via LINSTOR")
            return False

    def create_linstor_vg(self, name, node, list_pv):
        pv = ' '.join(list_pv)
        cmd = f"linstor ps cdp --pool-name {name} lvm {node} {pv}"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to create VG {name} via LINSTOR")
            return False

    def show_unused_device(self):
        cmd = "linstor ps l"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(result["rt"])

    def get_pvs(self):
        cmd = "pvs --noheadings"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            vgs_list = re.findall('(\S+)\s+(\S*)\s+lvm2\s+\S+\s+(\S+)\s+(\S+)\s*?', result["rt"])
            # print(vgs_list)
            return vgs_list

    def get_vgs(self):
        cmd = "vgs --noheadings"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                vgs_list = re.findall('(\S+)\s+(\d+)\s+(\d+)\s+\d+\s+\S+\s+(\S+)\s+(\S+)\s*?', result["rt"])
                # print(vgs_list)
                return vgs_list

    def get_lvs(self):
        cmd = "lvs --noheadings"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                vgs_list = re.findall('(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s(\S*).*\s', result["rt"])
                # pprint.pprint(vgs_list)
                return vgs_list

    def create_pv(self, device):
        cmd = f"pvcreate {device}"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to create PV {device}")
            return False

    def create_vg(self, name, list_pv):
        pv = ' '.join(list_pv)
        cmd = f"vgcreate {name} {pv}"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to create VG {name}")
            return False

    def create_lv(self, name, size, vg):
        cmd = f"lvcreate -n {name} -L {size} {vg}"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to create LV {name}")
            return False

    def create_thinpool(self, name, size, vg):
        cmd = f"lvcreate -T -L {size} {vg}/{name}"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to create Thinpool {name}")
            return False

    def create_thinlv(self, name, size, vg, thinpool):
        cmd = f"lvcreate -V {size} -n {name} {vg}/{thinpool}"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to create Thin LV {name}")
            return False

    def del_pv(self, name):
        cmd = f"pvremove {name} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to delete PV {name}")
            return False

    def del_vg(self, name):
        # vgremove
        cmd = f"vgremove {name} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to delete VG {name}")
            return False

    def del_thinpool(self, vg, thinpool):
        # lvremove /dev/linstor_vtel_pool/vtel_pool
        cmd = f"lvremove /dev/{vg}/{thinpool} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            return True
        else:
            print(f"Failed to delete Thinpool: {vg}/{thinpool}")
            return False
        pass

    def check_thinpool(self, vg, thinpool):
        """检查Thinpool是不是LINSTOR资源, vg/poolname"""
        if self.sp:
            for i in self.sp:
                if i['PoolName'] == f'{vg}/{thinpool}':
                    return i['StoragePool']

    def check_lv(self, lv):
        if self.res:
            for i in self.res:
                if f'{i["Resource"]}_00000' == lv:
                    return True

    def check_vg(self, vg):
        if self.sp:
            for i in self.sp:
                # vg属于linstor资源
                if i["PoolName"] == vg:
                    return i["StoragePool"]

    def get_pv_via_vg(self, vg):
        pv_dict = {}
        pv_list = self.get_pvs()
        for pv in pv_list:
            if pv[1] == vg:
                pv_dict[pv[0]] = pv[2]
        # print(pv_dict)
        return pv_dict

    def get_vg_via_thinpool(self, thinpool):
        vg_list = []
        lv_list = self.get_lvs()
        for lv in lv_list:
            if lv[0] == thinpool:
                vg_list.append(lv[1])
        # print(vg_list)
        return vg_list

    def get_lvm_on_node(self):
        # pv_list = self.get_pvs()
        vg_list = self.get_vgs()
        lv_list = self.get_lvs()

        # pprint.pprint(self.res)
        # pprint.pprint(self.sp)

        vg_dict = {}
        for vg in vg_list:
            vg_data = {'free size': None, 'total size': None, 'linstor storage pool': {'sp name': None}}
            pv_key = f'pvs({vg[1]})'
            lv_key = f'lvs({vg[2]})'
            vg_data['total size'] = vg[3]
            vg_data['free size'] = vg[4]
            vg_data[pv_key] = None
            vg_data[lv_key] = None
            lv_dict = {}
            pv_dict = self.get_pv_via_vg(vg[0])
            vg_data[pv_key] = pv_dict if pv_dict else None

            for lv in lv_list:
                if lv[1] == vg[0]:
                    # LV
                    if '-wi-' in lv[2]:
                        status = True if self.check_lv(lv[0]) else False
                        lv_dict[lv[0]] = {"size": lv[3], 'linstor resource': status}
                    # thinpool
                    elif 'twi-' in lv[2]:
                        sp_ = self.check_thinpool({lv[1]}, {lv[0]})
                        lv_dict[lv[0]] = {"size": lv[3], 'linstor storage pool': {'sp name': sp_}}
                    # elif 'Vwi-' in lv[2]:
                    #     lv_dict[lv[0]] = {"size": lv[3], 'linstor resource': False}
            vg_data[lv_key] = lv_dict if lv_dict else None

            for pool in lv_dict:
                pool_dict = {}
                for lv in lv_list:
                    if lv[4] == pool and lv[1] == vg[0]:
                        thinlv_status = True if self.check_lv(lv[0]) else False
                        pool_dict[lv[0]] = {"size": lv[3], 'linstor resource': thinlv_status}
                if len(pool_dict) != 0:
                    pool_key = f'lvs({len(pool_dict)})'
                    vg_data[lv_key][pool][pool_key] = pool_dict if pool_dict else None

            vg_dict[vg[0]] = vg_data

            vg_status = self.check_vg(vg[0])
            vg_data["linstor storage pool"]["sp name"] = vg_status

            vg_dict[vg[0]] = vg_data
        return vg_dict

    def show(self, dict_vg, vg=None):
        """以YAML格式展示JSON数据"""
        # dict_vg = self.vg_template(["vg1", "vg2"])
        if not self.res and not self.sp:
            print('-' * 10, "Can't get LINSTOR resource", '-' * 10)
        if vg:
            print('-' * 10, vg, '-' * 10)
            print(yaml.dump(dict_vg[vg], sort_keys=False))
        else:
            print(yaml.dump(dict_vg, sort_keys=False))


class YamlData(object):
    def __init__(self):
        self.yaml_file = 'test.yaml'
        self.yaml_dict = None

    def read_yaml(self):
        """读YAML文件"""
        try:
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                yaml_dict = yaml.safe_load(f)
            return yaml_dict
        except FileNotFoundError:
            print("Please check the file name:", self.yaml_file)

    def update_yaml(self):
        """更新文件内容"""
        with open("test2.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(self.yaml_dict, f, default_flow_style=False)


if __name__ == '__main__':
    # conf.read_yaml()
    lvm_operation = ClusterLVM("mattie2")
    pv_list1 = ["/dev/sdd1", "/dev/sdd2"]
    pv_list2 = ["/dev/sdd3"]
    # lvm_operation.create_linstor_vg("vtel_vg","mattie1",pv_list1)
    # lvm_operation.create_linstor_thinpool("vtel_pool", "mattie1", pv_list2)

    # for pv in pv_list:
    #     lvm_operation.create_pv(pv)
    # lvm_operation.create_vg("vtel_vg",["/dev/sdd1", "/dev/sdd2"])
    # lvm_operation.create_thinpool('vtel_pool',"5M",'vg2')

    # conf = YamlData()
    dict_vg = lvm_operation.get_lvm_on_node()
    lvm_operation.show_unused_device()
    lvm_operation.show(dict_vg, None)

    # if not lvm_operation.check_vg("vgsdb1"):
    #     lvm_operation.del_vg("vgsdb1")
    # else:
    #     print("In Used")
    # a = lvm_operation.get_pv_via_vg("vg12")
    # for pv in a.keys():
    #     print(pv)
    # for pv in pv_list1:
    #     lvm_operation.del_pv(pv)
    # b = lvm_operation.get_vg_via_thinpool("lv_pool2")
    # print(b)
    # if not lvm_operation.check_thinpool("vg2", "vtel_pool"):
    #     if lvm_operation.del_thinpool("vg2", "vtel_pool"):
    #         lvm_operation.del_vg("vg2")
    # else:
    #     print("In Used")
    #
    # ssh_connect = utils.SSHConn("10.203.1.183")
    # ssh_connect = utils.SSHConn("mattie2")
    # print(utils.exec_cmd("hostname", ssh_connect))

    # conf.show(dict_vg, "v
