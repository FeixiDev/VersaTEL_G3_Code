# -*- coding:utf-8 -*-
import os
import re
import yaml
import pprint
from execute.linstor_api import LinstorAPI
import utils
import sys
import sundry as s


class ClusterLVM(object):
    def __init__(self, node):
        self.api = LinstorAPI()
        try:
            self.sp = self.api.get_storagepool([node])
            self.res = self.api.get_resource([node])
        except AttributeError:
            self.sp = None
            self.res = None

        if node == utils.get_hostname():
            self.conn = None
        else:
            self.conn = utils.SSHConn(node)

        self.pv_list = self.get_pvs()
        self.vg_list = self.get_vgs()
        self.lv_list = self.get_lvs()

    # def create_linstor_thinpool(self, name, node, list_pv):
    #     pv = ' '.join(list_pv)
    #     cmd = f"linstor ps cdp --pool-name {name} lvmthin {node} {pv}"
    #     result = utils.exec_cmd(cmd, self.conn)
    #     if result["st"]:
    #         return True
    #     else:
    #         print(f"Failed to create Thinpool {name} via LINSTOR")
    #         return False

    # def create_linstor_vg(self, name, node, list_pv):
    #     pv = ' '.join(list_pv)
    #     cmd = f"linstor ps cdp --pool-name {name} lvm {node} {pv}"
    #     result = utils.exec_cmd(cmd, self.conn)
    #     if result["st"]:
    #         return True
    #     else:
    #         print(f"Failed to create VG {name} via LINSTOR")
    #         return False

    # def show_unused_device(self):
    #     """使用linstor命令展示可用的设备"""
    #     cmd = "linstor ps l"
    #     result = utils.exec_cmd(cmd, self.conn)
    #     if result["st"]:
    #         print(result["rt"])

    def get_lvm_device(self):
        """获取所有可见的LVM2设备"""
        cmd = "lvmdiskscan"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                lvm_list = re.findall('(/dev/sd\S+)\s+\[\s*(\S+\s\w+)\]\s+', result["rt"])
                return lvm_list

    def get_filesys(self):
        """获取所有可见的LVM2设备"""
        cmd = "df"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                fs_list = re.findall('(\S+)(?:\s+(?:\d+|-)){3}\s+\S+\s+\S\s*', result["rt"])
                print(fs_list)
                return fs_list

    def get_pvs(self):
        """获取pv类型数据"""
        cmd = "pvs --noheadings"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                vgs_list = re.findall('(\S+)\s+(\S*)\s+lvm2\s+\S+\s+(\S+)\s+(\S+)\s*?', result["rt"])
                # print(vgs_list)
                return vgs_list

    def get_vgs(self):
        """获取vg类型数据"""
        cmd = "vgs --noheadings"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                vgs_list = re.findall('(\S+)\s+(\d+)\s+(\d+)\s+\d+\s+\S+\s+(\S+)\s+(\S+)\s*?', result["rt"])
                # print(vgs_list)
                return vgs_list

    def get_lvs(self):
        """获取lv类型数据"""
        cmd = "lvs --noheadings"
        result = utils.exec_cmd(cmd, self.conn)
        if result:
            if result["st"]:
                vgs_list = re.findall('(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s(\S*).*\s', result["rt"])
                # pprint.pprint(vgs_list)
                return vgs_list

    def create_pv(self, device):
        """创建pv"""
        cmd = f"pvcreate {device} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(f"Success in createing PV: {device}")
            return True
        else:
            print(f"Failed to create PV {device}")
            return False

    def create_vg(self, name, list_pv):
        """创建vg"""
        pv = ' '.join(list_pv)
        cmd = f"vgcreate {name} {pv} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(f"Success in createing VG: {name}")
            return True
        else:
            print(f"Failed to create VG {name}")
            return False

    def create_lv(self, name, size, vg):
        """创建lv"""
        cmd = f"lvcreate -n {name} -L {size} {vg} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(f"Success in createing LV: {name}")
            return True
        else:
            print(f"Failed to create LV: {name}")
            return False

    def create_thinpool(self, name, size, vg):
        """创建thinpool"""
        cmd = f"lvcreate -T -L {size} {vg}/{name} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(f"Success in createing Thinpool: {name}")
            return True
        else:
            print(f"Failed to create Thinpool {name}")
            return False

    def create_thinlv(self, name, size, vg, thinpool):
        """创建thinlv"""
        cmd = f"lvcreate -V {size} -n {name} {vg}/{thinpool} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(f"Success in createing Thin LV: {name}")
            return True
        else:
            print(f"Failed to create Thin LV {name}")
            return False

    def del_pv(self, name):
        """删除PV"""
        cmd = f"pvremove {name} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(f"Success in deleting PV: {name}")
            return True
        else:
            print(f"Failed to delete PV {name}")
            return False

    def del_vg(self, name):
        """删除VG,删除前确认vg中是否还有lv"""
        self.vg_list = self.get_vgs()
        for vg in self.vg_list:
            if vg[0] == name:
                if int(vg[2]) > 0:
                    print(f"{name} still have other lv resource.Cancel delete {name}.")
                    sys.exit()
        cmd = f"vgremove {name} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(f"Success in deleting VG: {name}")
            return True
        else:
            print(f"Failed to delete VG {name}")
            return False

    def del_thinpool(self, vg, thinpool):
        """删除thinpool"""
        # lvremove /dev/linstor_vtel_pool/vtel_pool
        cmd = f"lvremove /dev/{vg}/{thinpool} -y"
        result = utils.exec_cmd(cmd, self.conn)
        if result["st"]:
            print(f"Success in deleting Thinpool: {vg}/{thinpool}")
            return True
        else:
            print(f"Failed to delete Thinpool: {vg}/{thinpool}")
            return False
        pass

    def check_thinpool(self, vg, thinpool):
        """
        检查Thinpool是不是被用作LINSTOR后端存储
        thinpool name: vg/poolname
        """
        if self.sp:
            for i in self.sp:
                if i['PoolName'] == f'{vg}/{thinpool}':
                    return i['StoragePool']

    def check_lv(self, lv):
        """检查lv是不是LINSTOR资源"""
        if self.res:
            for i in self.res:
                if f'{i["Resource"]}_00000' == lv:
                    return True

    def check_vg(self, vg):
        """检查vg是不是被用作LINSTOR后端存储"""
        if self.sp:
            for i in self.sp:
                if i["PoolName"] == vg:
                    return i["StoragePool"]

    def get_pv_via_vg(self, vg):
        """通过VG名获取对应的PV"""
        pv_dict = {}
        # pv_list = self.get_pvs()
        if self.pv_list:
            for pv in self.pv_list:
                if pv[1] == vg:
                    pv_dict[pv[0]] = pv[2]
        if not pv_dict:
            print(f"{vg} is not vg resource")
            sys.exit()
        # print(pv_dict)
        return pv_dict

    def get_vg_via_thinpool(self, thinpool):
        """通过thinpool名获取对应的VG"""
        vg_list = []
        # lv_list = self.get_lvs()
        if self.lv_list:
            for lv in self.lv_list:
                if lv[0] == thinpool:
                    vg_list.append(lv[1])
        if not vg_list:
            print(f"{thinpool} is not thinpool resource")
            sys.exit()
        # print(vg_list)
        return vg_list

    def get_lvm_on_node(self):
        """处理展示的数据"""

        if not self.vg_list:
            print("The node don't have VG.")
            sys.exit()
        # pprint.pprint(self.res)
        # pprint.pprint(self.sp)

        vg_dict = {}
        for vg in self.vg_list:
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

            if self.lv_list:
                for lv in self.lv_list:
                    if lv[1] == vg[0]:
                        # lv
                        if '-wi-' in lv[2]:
                            status = True if self.check_lv(lv[0]) else False
                            lv_dict[lv[0]] = {"size": lv[3], 'linstor resource': status}
                        # thinpool
                        elif 'twi-' in lv[2]:
                            sp_ = self.check_thinpool(lv[1], lv[0])
                            lv_dict[lv[0]] = {"size": lv[3], 'linstor storage pool': {'sp name': sp_}}
                        # elif 'Vwi-' in lv[2]:
                        #     lv_dict[lv[0]] = {"size": lv[3], 'linstor resource': False}
            vg_data[lv_key] = lv_dict if lv_dict else None

            for pool in lv_dict:
                pool_dict = {}
                # thinlv
                if self.lv_list:
                    for lv in self.lv_list:
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

    def show_vg(self, vg=None):
        """以YAML格式展示JSON数据"""
        dict_vg = self.get_lvm_on_node()
        if not self.res and not self.sp:
            print('-' * 10, "Can't get LINSTOR resource", '-' * 10)
        try:
            if vg:
                print('-' * 10, vg, '-' * 10)
                print(yaml.dump(dict_vg[vg], sort_keys=False))
            else:
                print(yaml.dump(dict_vg, sort_keys=False))
        except KeyError:
            print(f"{vg} does not exit.")

    def show_unused_lvm_device(self):
        """表格展示未被用来创建PV的LVM设备"""
        print('-' * 10, "Unused Device", '-' * 10)
        list_header = ["Device", "Size"]
        lvm_list = self.get_lvm_device()
        fs_list = self.get_filesys()
        print(lvm_list)
        if lvm_list:
            unused_lvm_device = list(lvm_list)
            if self.pv_list:
                for pv in self.pv_list:
                    for device in lvm_list:
                        if pv[0] == device[0]:
                            unused_lvm_device.remove(device)
            unused_lvm_device_without_fs = [i for i in unused_lvm_device if i[0] not in fs_list]
            print(s.make_table(list_header, unused_lvm_device_without_fs))
        else:
            print(f"No message of unused device")

    def delete_vg(self, vg):
        if not self.check_vg(vg):
            pv_dict = self.get_pv_via_vg(vg)
            if self.del_vg(vg):
                for pv in pv_dict.keys():
                    self.del_pv(pv)
        else:
            print(f"{vg} is in used")

    def delete_thinpool(self, thinpool, confirm):
        vg_list = self.get_vg_via_thinpool(thinpool)
        if len(vg_list) > 1:
            print(f'Thinpool with the same name "{thinpool}" exist in those vg: {vg_list}')
            vg = input("Input the VG Name that the thinpool you want to delete:")
            if vg.strip() in vg_list:
                vg = vg.strip()
            else:
                print("Error VG Name")
                sys.exit()
        else:
            vg = vg_list[0]
        if not self.check_thinpool(vg, thinpool):
            if self.del_thinpool(vg, thinpool):
                pv_dict = self.get_pv_via_vg(vg)
                if confirm:
                    if self.del_vg(vg):
                        for pv in pv_dict.keys():
                            self.del_pv(pv)
        else:
            print(f"{thinpool} is in used")
