import sys
import time
from collections import Counter
from unittest.mock import patch

import pytest

import consts
import iscsi_json
import log
import sundry
from execute import crm, iscsi
import subprocess

from execute.crm import execute_crm_cmd


# def test_module():
#     """模块初始化函数，初始化 consts 类跨模块变量"""
#     # print('test_module')
#     sys.path.append('../')
#     consts.init()
#
#     # transaction_id = s.create_transaction_id()
#     # logger = log.Log('test',transaction_id)
#     # consts.set_glo_log(logger)
#     # consts.set_glo_tsc_id(transaction_id)
#     # # consts.set_glo_id(99)
#     # # consts.set_glo_str('test')
#     # consts.set_glo_rpl('no')
#     # transaction_id = sundry.create_transaction_id()
#     # logger = log.Log('test', transaction_id)
#     logger = log.Log()
#     # consts.set_glo_log(logger)
#     consts.set_glo_rpl('no')


def test_execute_crm_cmd():
    """测试执行 crm 命令方法"""
    assert crm.execute_crm_cmd('pwd') is not None


class TestCRMData:

    def setup_class(self):
        self.crmdata = crm.CRMData()

    # result 类型 str ，命令行输出内容
    def test_get_crm_conf(self):
        """测试输出 crm 配置文件内容方法"""
        result = self.crmdata.get_crm_conf()
        assert str == type(result)
        # assert 'res_a' in result
        assert 'primitive' in result

    # 函数名有改动/该函数被删除
    # def test_get_resource_data(self):
    #     assert self.crmdata.get_resource_data()
    #
    # def test_get_vip_data(self):
    #     assert self.crmdata.get_vip_data() is not None
    #
    # def test_get_target_data(self):
    #     assert self.crmdata.get_target_data() is not None
    #

    @pytest.mark.portal
    def test_get_vip(self):
        """获取 crm 全部 vip 信息"""
        # print('get_vip', self.crmdata.get_vip())
        assert self.crmdata.get_vip() is not None

    @pytest.mark.portal
    def test_get_portblock(self):
        """获取 crm 全部 portblock 信息"""
        # print('get_portblock', self.crmdata.get_portblock())
        assert self.crmdata.get_portblock() is not None

    @pytest.mark.portal
    def test_get_target(self):
        """获取 crm 全部 target 信息"""
        # print('get_target', self.crmdata.get_target())
        assert self.crmdata.get_target() is not None

    def test_get_iscsi_logical_unit(self):
        #mat:+
        pass

    # @pytest.mark.portal
    # def test_get_portal_data(self):
    # #mat:get_portal_data-->get_conf_portal
    #     """获取 crm 全部 portal data 信息"""
    #     # print('get_portal_data', self.crmdata.get_portal_data(self.crmdata.get_vip(), self.crmdata.get_portblock(),
    #     #                                    self.crmdata.get_target()))
    #     assert self.crmdata.get_portal_data(self.crmdata.get_vip(), self.crmdata.get_portblock(),
    #                                         self.crmdata.get_target()) is not None

    @pytest.mark.portal
    def test_get_order(self):
        """获取 crm 全部 order 信息"""
        assert self.crmdata.get_order() is not None

    @pytest.mark.portal
    def test_get_colocation(self):
        """获取 crm 全部 colocation 信息"""
        assert self.crmdata.get_colocation() is not None

    def test_get_conf_portal(self):
        #mat:+
        pass

    @pytest.mark.portal
    def test_check_portal_component(self):
        #mat:modify
        """对目前环境的portal组件(ipaddr,portblock）的检查，测试用例包括：已存在的ipaddr没有对应的portblock抛出异常/存在单独的portblock抛出异常/portal没有order和colcation/portal没有order/portal只有一个colocation/不存在异常情况检查通过"""
        # 共六个用例
        # 1.不存在单独的 portblock
        # 2.已存在的ipaddr，必须有对应的portblock组（block，unblock）
        # 尝试单独创建 ipaddr
        # 这些portal无法正常使用，请进行处理
        subprocess.run('crm cof primitive vip_pytest03 IPaddr2 params ip=10.203.1.202 cidr_netmask=24 -y', shell=True)
        # 需要重新实例化，不然单独创建 IPaddr2 没法在初始化的对象中读取
        crmdata = crm.CRMData()
        with pytest.raises(SystemExit) as exsinfo:
            crmdata.check_portal_component(crmdata.get_vip(), crmdata.get_portblock(), crmdata.get_order(), crmdata.get_colocation())
        assert exsinfo.type == SystemExit
        subprocess.run('crm res stop vip_pytest03', shell=True)
        subprocess.run('crm conf del vip_pytest03', shell=True)
        # 重新初始化对象
        # 尝试单独创建 portblock
        subprocess.run(
            'crm cof primitive vip_pytest03_prtblk_on portblock params ip=10.203.1.202 portno=24 protocol=tcp action=block op monitor timeout=20 interval=20 -y',
            shell=True)
        crmdata = crm.CRMData()
        with pytest.raises(SystemExit) as exsinfo:
            crmdata.check_portal_component(crmdata.get_vip(), crmdata.get_portblock(),crmdata.get_order(),crmdata.get_colocation())
        assert exsinfo.type == SystemExit
        subprocess.run('crm res stop vip_pytest03_prtblk_on', shell=True)
        subprocess.run('crm conf del vip_pytest03_prtblk_on', shell=True)
        # 重新初始化对象
        # 创建没有coloation 和 order
        subprocess.run('crm cof primitive vip_pytest03 IPaddr2 params ip=10.203.1.202 cidr_netmask=24', shell=True)
        subprocess.run('crm cof primitive vip_pytest03_prtblk_on portblock params ip=10.203.1.202 portno=3260 protocol=tcp action=block op monitor timeout=20 interval=20', shell=True)
        subprocess.run('crm cof primitive vip_pytest03_prtblk_off portblock params ip=10.203.1.202 portno=3260 protocol=tcp action=block op monitor timeout=20 interval=20', shell=True)
        crmdata = crm.CRMData()
        with pytest.raises(SystemExit) as exsinfo:
            crmdata.check_portal_component(crmdata.get_vip(), crmdata.get_portblock(), crmdata.get_order(), crmdata.get_colocation())
        assert exsinfo.type == SystemExit
        subprocess.run('crm res stop vip_pytest03', shell=True)
        subprocess.run('crm conf del vip_pytest03', shell=True)
        subprocess.run('crm res stop vip_pytest03_prtblk_on', shell=True)
        if subprocess.run('crm conf del vip_pytest03_prtblk_on', shell=True).returncode:
            subprocess.run('crm res ref', shell=True)
            subprocess.run('crm conf del vip_pytest03_prtblk_on', shell=True)
        else:
            pass
        subprocess.run('crm res stop vip_pytest03_prtblk_off', shell=True)
        if subprocess.run('crm conf del vip_pytest03_prtblk_off', shell=True).returncode:
            subprocess.run('crm res ref', shell=True)
            subprocess.run('crm conf del vip_pytest03_prtblk_off', shell=True)
        else:
            pass
        # 重新初始化对象
        # 创建没有 order
        subprocess.run('crm cof primitive vip_pytest03 IPaddr2 params ip=10.203.1.202 cidr_netmask=24', shell=True)
        subprocess.run(
            'crm cof primitive vip_pytest03_prtblk_on portblock params ip=10.203.1.202 portno=3260 protocol=tcp action=block op monitor timeout=20 interval=20',
            shell=True)
        subprocess.run(
            'crm cof primitive vip_pytest03_prtblk_off portblock params ip=10.203.1.202 portno=3260 protocol=tcp action=block op monitor timeout=20 interval=20',
            shell=True)
        subprocess.run('crm cof colocation col_vip_pytest03_prtblk_on inf: vip_pytest03_prtblk_on vip_pytest03', shell=True)
        subprocess.run('crm cof colocation col_vip_pytest03_prtblk_off inf: vip_pytest03_prtblk_off vip_pytest03', shell=True)
        crmdata = crm.CRMData()
        with pytest.raises(SystemExit) as exsinfo:
            crmdata.check_portal_component(crmdata.get_vip(), crmdata.get_portblock(), crmdata.get_order(),
                                           crmdata.get_colocation())
        assert exsinfo.type == SystemExit
        time.sleep(0.5)
        subprocess.run('crm res stop vip_pytest03', shell=True)
        subprocess.run('crm conf del vip_pytest03', shell=True)
        subprocess.run('crm res stop vip_pytest03_prtblk_on', shell=True)
        if subprocess.run('crm conf del vip_pytest03_prtblk_on', shell=True).returncode:
            subprocess.run('crm res ref', shell=True)
            subprocess.run('crm conf del vip_pytest03_prtblk_on', shell=True)
        else:
            pass
        subprocess.run('crm res stop vip_pytest03_prtblk_off', shell=True)
        if subprocess.run('crm conf del vip_pytest03_prtblk_off', shell=True).returncode:
            subprocess.run('crm res ref', shell=True)
            subprocess.run('crm conf del vip_pytest03_prtblk_off', shell=True)
        else:
            pass
        # ps： col 和 order 会自已删除不需要手动删除
        # 没有其中一个col
        subprocess.run('crm cof primitive vip_pytest03 IPaddr2 params ip=10.203.1.202 cidr_netmask=24', shell=True)
        subprocess.run(
            'crm cof primitive vip_pytest03_prtblk_on portblock params ip=10.203.1.202 portno=3260 protocol=tcp action=block op monitor timeout=20 interval=20',
            shell=True)
        subprocess.run(
            'crm cof primitive vip_pytest03_prtblk_off portblock params ip=10.203.1.202 portno=3260 protocol=tcp action=block op monitor timeout=20 interval=20',
            shell=True)
        subprocess.run('crm cof colocation col_vip_pytest03_prtblk_on inf: vip_pytest03_prtblk_on vip_pytest03',
                       shell=True)
        subprocess.run('crm cof order or_vip_pytest03_prtblk_on vip_pytest03_prtblk_on vip_pytest03', shell=True)
        crmdata = crm.CRMData()
        with pytest.raises(SystemExit) as exsinfo:
            crmdata.check_portal_component(crmdata.get_vip(), crmdata.get_portblock(), crmdata.get_order(),
                                           crmdata.get_colocation())
        assert exsinfo.type == SystemExit
        time.sleep(0.5)
        subprocess.run('crm res stop vip_pytest03', shell=True)
        subprocess.run('crm conf del vip_pytest03', shell=True)
        subprocess.run('crm res stop vip_pytest03_prtblk_on', shell=True)
        if subprocess.run('crm conf del vip_pytest03_prtblk_on', shell=True).returncode:
            subprocess.run('crm res ref', shell=True)
            subprocess.run('crm conf del vip_pytest03_prtblk_on', shell=True)
        else:
            pass
        subprocess.run('crm res stop vip_pytest03_prtblk_off', shell=True)
        if subprocess.run('crm conf del vip_pytest03_prtblk_off', shell=True).returncode:
            subprocess.run('crm res ref', shell=True)
            subprocess.run('crm conf del vip_pytest03_prtblk_off', shell=True)
        else:
            pass
        # 重新初始化对象
        crmdata = crm.CRMData()
        assert crmdata.check_portal_component(crmdata.get_vip(), crmdata.get_portblock(), crmdata.get_order(), crmdata.get_colocation()) is None

    # check 函数调用 check_portal_component 和 check_env_sync 函数不作用例分析
    @pytest.mark.portal
    def test_check(self):
        """check 函数调用 check_portal_component 和 check_env_sync 函数不作用例分析"""
        assert self.crmdata.check() is None

    @pytest.mark.portal
    def test_check_env_sync(self):
        #mat:modify
        """检查CRM环境与JSON配置文件所记录的Portal、Target的数据是否一致,测试用例包括：json文件不包含Portal/json文件不包括Target/json文件的portal与crm不一致/json文件的target与crm的不一致"""
        assert self.crmdata.check_env_sync(self.crmdata.get_vip(), self.crmdata.get_portblock(),
                                           self.crmdata.get_target()) is None
        js = iscsi_json.JsonOperation()
        js.json_data = {
            "Host": {},
            "Disk": {},
            "HostGroup": {},
            "DiskGroup": {},
            "Map": {}
        }
        with pytest.raises(SystemExit) as exsinfo:
            self.crmdata.check_env_sync(self.crmdata.get_vip(), self.crmdata.get_portblock(),
                                        self.crmdata.get_target())
        assert exsinfo.type == SystemExit
        js.json_data = {
            "Host": {},
            "Disk": {},
            "HostGroup": {},
            "DiskGroup": {},
            "Map": {},
            "Portal": {}
        }
        with pytest.raises(SystemExit) as exsinfo:
            self.crmdata.check_env_sync(self.crmdata.get_vip(), self.crmdata.get_portblock(),
                                        self.crmdata.get_target())
        assert exsinfo.type == SystemExit
        js.json_data = {
            "Host": {},
            "Disk": {},
            "HostGroup": {},
            "DiskGroup": {},
            "Map": {},
            "Portal": {
                "portal_test_6": {
                    "ip": "10.203.1.201",
                    "port": "3260",
                    "netmask": "24",
                    "target": []
                }
            },
            "Target": {}
        }
        with pytest.raises(SystemExit) as exsinfo:
            self.crmdata.check_env_sync(self.crmdata.get_vip(), self.crmdata.get_portblock(),
                                        self.crmdata.get_target())
        assert exsinfo.type == SystemExit
        js.json_data = {
            "Host": {},
            "Disk": {},
            "HostGroup": {},
            "DiskGroup": {},
            "Map": {},
            "Portal": {
                "portal_test_4": {
                    "ip": "10.203.1.201",
                    "port": "3260",
                    "netmask": "24",
                    "target": []
                },
                "vip": {
                    "ip": "10.203.1.75",
                    "port": "3260",
                    "netmask": "24",
                    "target": [
                        "t_test"
                    ]
                },
                "vip_test2": {
                    "ip": "10.203.1.206",
                    "port": "3260",
                    "netmask": "24",
                    "target": [
                        "target_test"
                    ]
                }
            },
            "Target": {
                "t_test": {
                    "target_iqn": "iqn.2020-04.feixitek.com:versaplx00",
                    "ip": "10.203.1.75",
                    "port": "3260"
                }
            }
        }
        with pytest.raises(SystemExit) as exsinfo:
            self.crmdata.check_env_sync(self.crmdata.get_vip(), self.crmdata.get_portblock(),
                                        self.crmdata.get_target())
        assert exsinfo.type == SystemExit
        target = self.crmdata.get_target()
        vip = self.crmdata.get_vip()
        portblock = self.crmdata.get_portblock()
        #mat:get_portal_data-->get_conf_portal
        portal = self.crmdata.get_portal_data(vip, portblock, target)
        js.cover_data('Portal', portal)
        js.cover_data('Target', target)
        js.commit_data()
        # print(js.json_data)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)


class TestCRMConfig:

    # def setup_class(self):
    #     self.crmconfig = crm.CRMConfig()

    def setup_class(self):
        subprocess.run('python3 vtel.py stor r c res_test -s 10m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        subprocess.run('python3 vtel.py iscsi dg c test_dg res_test', shell=True)
        subprocess.run('python3 vtel.py iscsi h c test_host iqn.2020-11.com.example:pytest01', shell=True)
        subprocess.run('python3 vtel.py iscsi hg c test_hg test_host', shell=True)
        self.crmconfig = crm.CRMConfig()

    def teardown_class(self):
        subprocess.run('python3 vtel.py iscsi hg d test_hg -y', shell=True)
        subprocess.run('python3 vtel.py iscsi h d test_host -y', shell=True)
        subprocess.run('python3 vtel.py iscsi dg d test_dg -y', shell=True)
        try:
            execute_crm_cmd('crm res stop res_test')
            execute_crm_cmd('crm conf del res_test')
        except Exception:
            print(Exception)
        finally:
            subprocess.run('python3 vtel.py stor r d res_test -y', shell=True)
            subprocess.run('python3 vtel.py iscsi d s', shell=True)

    # def test_create_crm_res(self):
    #     #mat:del
    #     """测试创建 crm res资源方法"""
    #     disk = iscsi.Disk()
    #     # attention
    #     disk_data = disk.show('res_test')
    #     path = disk_data[0][1]
    #     id = int(path[-4:]) - 1000
    #     assert self.crmconfig.create_crm_res('res_test', 'iqn.2020-04.feixitek.com:versaplx00', id, path,
    #                                          'iqn.2020-11.com.example:pytest01') is True

    # 函数已删除
    # def test_get_res_status(self):
    #
    #     assert self.crmconfig.get_res_status('res_test') is False
    #     self.crmconfig.start_res('res_test')
    #     time.sleep(5)
    #     assert self.crmconfig.get_res_status('res_test') is True

    # 函数已删除
    # def test_checkout_status_start(self):
    #     assert self.crmconfig.checkout_status_start('res_test') is True

    def test_stop_res(self):
        """测试停止 crm res资源方法"""
        assert self.crmconfig.stop_res('res_test') is True

    # # 函数已删除
    # # def test_checkout_status_stop(self):
    # #     assert self.crmconfig.checkout_status_stop('res_test') is True
    #
    # def test_create_col(self):
    #     assert self.crmconfig.create_col('res_test', 't_test') is True
    #
    # def test_create_order(self):
    #     assert self.crmconfig.create_order('res_test', 't_test') is True

    def test_start_res(self):
        """测试启动 crm res资源方法"""
        assert self.crmconfig.start_res('res_test') is True
        self.crmconfig.stop_res('res_test')

    # 函数已删除
    # def test_delete_conf_res(self):
    #     assert self.crmconfig.delete_conf_res('res_test') is True

    # ------------- add ----------------   2020.12.28

    # def test_change_initiator(self):
    #     assert self.crmconfig.change_initiator('res_test', ['iqn.2020-11.com.example:pytest01'])

    def test_monitor_status(self):
        #mat：modify
        """检查crm res的状态"""
        assert self.crmconfig.monitor_status('res_test', 'iSCSILogicalUnit', 'NOT_STARTED') is True
        assert self.crmconfig.monitor_status('', 'iSCSILogicalUnit', 'Started') is None

    def test_monitor_status_by_time(self):
        #mat：+
        pass

    def test_delete_res(self):
        #mat:看看
        """测试删除 crm res资源方法，测试用例包括：删除存在资源/删除不存在资源"""
        assert self.crmconfig.delete_res('res_test', 'iSCSILogicalUnit')
        # 删除一个不存在资源
        with patch('builtins.print') as terminal_print:
            self.crmconfig.delete_res('res_test0', 'iSCSILogicalUnit')
            terminal_print.assert_called_with('Delete res_test0 fail')



    def test_execute_delete(self):
        """测试执行删除 res"""
        # 删除不存在资源
        assert not self.crmconfig.execute_delete('res_test0')

    # def test_refresh(self):
    #     """刷新函数暂时未调用"""
    #     # 暂未调用，单独使用刷新命令result['sts'] == 0 if 条件不通过
    #     pass

    # 函数已删除
    # 有调用关系，不能单独测，create_res调用create_crm_res再调用create_set然后在调用create_col和create_order
    # 需要先创建crm_res,create_set方法主要是创建colocation和order
    # def test_create_set(self):
    #     disk = iscsi.Disk()
    #     disk_data = disk.get_all_disk()
    #     path = disk_data['res_test']
    #     lunid = int(path[-4:]) - 1000
    #     self.crmconfig.create_crm_res('res_test', 'iqn.2020-04.feixitek.com:versaplx00', lunid, path,
    #                                   'iqn.2020-11.com.example:pytest01')
    #     assert self.crmconfig.create_set('res_test', 't_test')
    #     self.crmconfig.delete_res('res_test', 'iSCSILogicalUnit')
    #     # 如果 crm_res 不存在该函数调用失败
    #     with patch('builtins.print') as terminal_print:
    #         self.crmconfig.create_set('res_test', 't_test')
    #         terminal_print.assert_called_with('create colocation fail')

    # 函数未被调用
    # def test_refresh(self):
    #     assert self.crmconfig.refresh() is True
    @pytest.mark.portal
    def test_get_failed_actions(self):
        """提取 vip 错误信息，测试用例包括：该vip有错误信息/该vip没有错误信息"""
        subprocess.run('crm cof primitive vip_pytest10 IPaddr2 params ip=10.203.1.209 cidr_netmask=50', shell=True)
        crmconfig = crm.CRMConfig()
        assert crmconfig.get_failed_actions('vip_pytest10') == 0
        # 没有报错信息，return None
        assert crmconfig.get_failed_actions('abd') is None
        subprocess.run('crm conf del vip_pytest10', shell=True)

    @pytest.mark.portal
    def test_get_crm_res_status(self):
        #mat:看看
        """获取crm res的状态，测试用例包括：获取状态成功/资源类型输入错误/资源名字与类型不对应/资源名字不存在"""
        assert self.crmconfig.get_crm_res_status('vip_pytest', 'IPaddr2')
        assert self.crmconfig.get_crm_res_status('vip_pytest', 'portblock') is None
        assert self.crmconfig.get_crm_res_status('p_iscsi_portblock_off', 'IPaddr2') is None
        with pytest.raises(ValueError) as exsinfo:
            self.crmconfig.get_crm_res_status('vip', 'IPaddr1')
        assert exsinfo.type == ValueError


# class TestRollback:
#     """#mat:忽略"""
#
#     def setup_class(self):
#         self.rb = crm.RollBack()
#
#     def test_rollback(self):
#         # rollback 调用 rb_ipaddr2() rb.rb_block() rb_target()
#         assert self.rb.rollback() is None
#
#     def test_rb_ipaddr2(self):
#         assert self.rb.rb_ipaddr2() is None
#
#     def test_rb_block(self):
#         assert self.rb.rb_block() is None
#
#     def test_rb_target(self):
#         assert self.rb.rb_target() is None

@pytest.mark.portal
class TestIPaddr2:

    def setup_class(self):
        self.ipaddr2 = crm.IPaddr2()

    def test_create(self):
        """创建IPaddr2，测试用例包括：创建IPaddr2成功/IPaddr2已存在创建失败"""
        # 端口 与ip 前面函数已校验
        with patch('builtins.print') as terminal_print:
            self.ipaddr2.create('vip_pytest03', '10.203.1.202', '24')
            terminal_print.assert_called_with('Create vip:vip_pytest03 successfully')
        # with pytest.raises(consts.CmdError) as exsinfo:
        #     self.ipaddr2.create.__wrapped__(self, 'vip_pytest04', '10.203.1....202', '24')
        # assert exsinfo.type == consts.CmdError
        # with pytest.raises(consts.CmdError) as exsinfo:
        #     self.ipaddr2.create.__wrapped__(self, 'vip_pytest05', '10.203.1.206', '40')
        # assert exsinfo.type == consts.CmdError
        with pytest.raises(consts.CmdError) as exsinfo:
            self.ipaddr2.create('vip_pytest03', '10.203.1.202', '40')
        assert exsinfo.type == consts.CmdError

    def test_modify(self):
        """修改IPaddr2，测试用例包括：修改IPaddr2成功/IPaddr2不存在修改失败"""
        with patch('builtins.print') as terminal_print:
            self.ipaddr2.modify('vip_pytest03', '10.203.1.203','40')
            terminal_print.assert_called_with('Modify vip:vip_pytest03 (IP and Netmask) successfully')
        # ip格式问题前面函数已校验
        # with pytest.raises(consts.CmdError) as exsinfo:
        #     self.ipaddr2.modify.__wrapped__(self, 'vip_pytest03', '10.203.1.202....')
        # assert exsinfo.type == consts.CmdError
        with pytest.raises(consts.CmdError) as exsinfo:
            self.ipaddr2.modify('vip_pytest0', '10.203.1.202', '40')
        assert exsinfo.type == consts.CmdError

    def test_delete(self):
        """删除IPaddr2，测试用例包括：删除IPaddr2成功/IPaddr2不存在删除失败"""
        with patch('builtins.print') as terminal_print:
            self.ipaddr2.delete('vip_pytest03')
            terminal_print.assert_called_with('Delete vip:vip_pytest03 successfully')
        with pytest.raises(consts.CmdError) as exsinfo:
            self.ipaddr2.delete('vip_pytest05')
        assert exsinfo.type == consts.CmdError


@pytest.mark.portal
class TestPortBlockGroup:

    def setup_class(self):
        self.pbg = crm.PortBlockGroup()

    def test_create(self):
        """创建PortBlockGroup，测试用例包括：创建类型非block/unblock创建失败/创建成功/已存在创建失败"""
        with pytest.raises(TypeError) as exsinfo:
            self.pbg.create('vip_pytest03_prtblk_on', '10.203.1.202', '24', None)
        assert exsinfo.type == TypeError
        with patch('builtins.print') as terminal_print:
            self.pbg.create('vip_pytest03_prtblk_on', '10.203.1.202', '24', 'block')
            terminal_print.assert_called_with('Create portblock:vip_pytest03_prtblk_on successfully')

        with patch('builtins.print') as terminal_print:
            self.pbg.create('vip_pytest03_prtblk_off', '10.203.1.202', '24', 'unblock')
            terminal_print.assert_called_with('Create portblock:vip_pytest03_prtblk_off successfully')

        with pytest.raises(consts.CmdError) as exsinfo:
            self.pbg.create('vip_pytest03_prtblk_off', '10.203.1.202', '24', 'unblock')
        assert exsinfo.type == consts.CmdError

    def test_modify(self):
        """修改PortBlockGroup，测试用例包括：修改成功/不存在修改失败"""
        with patch('builtins.print') as terminal_print:
            self.pbg.modify('vip_pytest03_prtblk_on', '10.203.1.203', '24')
            terminal_print.assert_called_with('Modify portblock:vip_pytest03_prtblk_on (IP and Port) successfully')

        with patch('builtins.print') as terminal_print:
            self.pbg.modify('vip_pytest03_prtblk_off', '10.203.1.203', '24')
            terminal_print.assert_called_with('Modify portblock:vip_pytest03_prtblk_off (IP and Port) successfully')
        with pytest.raises(consts.CmdError) as exsinfo:
            self.pbg.modify('vip_pytest0000_prtblk_off', '10.203.1.203', '24')
        assert exsinfo.type == consts.CmdError

    def test_delete(self):
        """删除PortBlockGroup，测试用例包括：删除成功/不存在删除失败"""
        with patch('builtins.print') as terminal_print:
            self.pbg.delete('vip_pytest03_prtblk_on')
            terminal_print.assert_called_with('Delete portblock:vip_pytest03_prtblk_on successfully')

        with patch('builtins.print') as terminal_print:
            self.pbg.delete('vip_pytest03_prtblk_off')
            terminal_print.assert_called_with('Delete portblock:vip_pytest03_prtblk_off successfully')

        with pytest.raises(consts.CmdError) as exsinfo:
            self.pbg.delete('vip_pytest0000_prtblk_off')
        assert exsinfo.type == consts.CmdError


@pytest.mark.portal
class TestColocation:
    def test_create(self):
        """创建Colocation，测试用例包括：创建Colocation成功/使用不存在资源创建Colocation"""
        subprocess.run('python3 vtel.py stor r c res_test -s 10m -a -num 1', shell=True)
        disk = iscsi.Disk()
        disk_data = disk.show('res_test')
        path = disk_data[0][1]
        lunid = int(path[-4:]) - 1000
        # 要先创建 resource 才可以创建 colocation
        colocation = crm.Colocation()
        iscsilu = crm.ISCSILogicalUnit()
        iscsilu.create('res_test', 'iqn.2020-04.feixitek.com:versaplx00', lunid, path,
                       'iqn.2020-11.com.example:pytest01')
        # 创建成功
        assert colocation.create('col_res_test', 'res_test', iscsilu.target_name)
        # 数据清除
        subprocess.run('crm res stop res_test', shell=True)
        subprocess.run('crm conf del res_test', shell=True)
        subprocess.run('python3 vtel.py stor r d res_test -y', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        # resource 不存在
        with pytest.raises(consts.CmdError) as exsinfo:
            colocation.create('col_res_test0', 'res_test0', iscsilu.target_name)
        assert exsinfo.type == consts.CmdError


@pytest.mark.portal
class TestOrder:
    def test_create(self):
        """创建Order，测试用例包括：创建Colocation成功/使用不存在资源创建Colocation"""
        subprocess.run('python3 vtel.py stor r c res_test -s 10m -a -num 1', shell=True)
        disk = iscsi.Disk()
        disk_data = disk.show('res_test')
        path = disk_data[0][1]
        lunid = int(path[-4:]) - 1000
        iscsilu = crm.ISCSILogicalUnit()
        iscsilu.create('res_test', 'iqn.2020-04.feixitek.com:versaplx00', lunid, path,
                       'iqn.2020-11.com.example:pytest01')
        # 要先创建 resource 才可以创建 colocation
        order = crm.Order()
        # 创建成功
        assert order.create('or_res_test', iscsilu.target_name, 'res_test')
        # 数据清除
        subprocess.run('crm res stop res_test', shell=True)
        subprocess.run('crm conf del res_test', shell=True)
        subprocess.run('python3 vtel.py stor r d res_test -y', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        # resource和colocation不存在
        with pytest.raises(consts.CmdError) as exsinfo:
            assert order.create('or_res_test0', iscsilu.target_name, 'res_test0')
        assert exsinfo.type == consts.CmdError

@pytest.mark.target
class TestISCSITarget:
    def setup_class(self):
        # subprocess.run('crm cof primitive pytest_it_portal_1 IPaddr2 params ip=10.203.1.98 cidr_netmask=24', shell=True)
        # subprocess.run('crm cof primitive pytest_it_portal_2 IPaddr2 params ip=10.203.1.88 cidr_netmask=24', shell=True)
        # subprocess.run('crm cof primitive pytm_it_target_1 iSCSITarget params iqn="iqn.2020-02.com.example:pymtest1" implementation=lio-t portals="10.203.1.98:3260" op start timeout=50 stop timeout=40 op monitor interval=15 timeout=40 meta target-role=Stopped', shell=True)

        subprocess.run('python3 vtel.py iscsi portal c pytest_it_portal_1 -ip 10.203.1.88', shell=True)
        time.sleep(5)
        subprocess.run('python3 vtel.py iscsi portal c pytest_it_portal_2 -ip 10.203.1.98', shell=True)
        time.sleep(5)
        subprocess.run(
            'crm cof primitive pytm_it_target_1 iSCSITarget params iqn="iqn.2020-02.com.example:pyitmtest1" implementation=lio-t portals="10.203.1.88:3260" op start timeout=50 stop timeout=40 op monitor interval=15 timeout=40 meta target-role=Stopped',
            shell=True)
        subprocess.run('crm cof colocation col_pytm_it_target_1_pytest_it_portal_1 inf: pytm_it_target_1 pytest_it_portal_1',
                       shell=True)
        subprocess.run('crm cof order or_pytm_it_target_1_pytest_it_portal_1 pytest_it_portal_1 pytm_it_target_1', shell=True)
        subprocess.run('crm res start pytm_it_target_1', shell=True)
        subprocess.run(
            'crm cof primitive pytm_it_target_2 iSCSITarget params iqn="iqn.2020-02.com.example:pyitmtest2" implementation=lio-t portals="10.203.1.98:3260" op start timeout=50 stop timeout=40 op monitor interval=15 timeout=40 meta target-role=Stopped',
            shell=True)
        subprocess.run('crm cof colocation col_pytm_it_target_2_pytest_it_portal_1 inf: pytm_it_target_2 pytest_it_portal_1',
                       shell=True)
        subprocess.run('crm cof order or_pytm_it_target_2_pytest_it_portal_1 pytm_it_portal_1 pytm_it_target_2', shell=True)
        subprocess.run('crm res start pytm_it_target_2', shell=True)
        time.sleep(5)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)

        self.target = crm.ISCSITarget()

    def teardown_class(self):
        subprocess.run('crm res stop pytm_it_target_1', shell=True)
        # time.sleep(1)
        # subprocess.run('crm res ref', shell=True)
        time.sleep(3)
        subprocess.run('crm conf del pytm_it_target_1', shell=True)
        time.sleep(3)
        subprocess.run('crm res stop pytm_it_target_2', shell=True)
        # time.sleep(1)
        # subprocess.run('crm res ref', shell=True)
        time.sleep(3)
        subprocess.run('crm conf del pytm_it_target_2', shell=True)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        # subprocess.run('crm res stop pytm_it_portal_1', shell=True)
        # time.sleep(1)
        # subprocess.run('crm res ref', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi portal d pytest_it_portal_1', shell=True)
        time.sleep(3)
        # subprocess.run('crm res stop pytm_it_portal_2', shell=True)
        # subprocess.run('crm res ref', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi portal d pytest_it_portal_2', shell=True)

    def test_create(self):
        assert self.target.create.func(self.target, 'pytc_it_target_1', 'iqn.2020-02.com.example:pyittarget1' ,'10.203.1.88', '3260') is True
        with pytest.raises(consts.CmdError) as exsinfo:
            assert self.target.create('pytc_it_target_1', 'iqn.2020-02.com.example:pyittarget1', '10.203.1.99', '3260')
        assert exsinfo.type == consts.CmdError
        subprocess.run('crm res stop pytc_it_target_1', shell=True)
        time.sleep(2)
        subprocess.run('crm conf del pytc_it_target_1', shell=True)

    def test_modify_iqn(self):
        assert self.target.modify_iqn.func(self.target, 'pytm_it_target_1', 'iqn.2020-02.com.example:pyitmtarget3') is True
        with pytest.raises(consts.CmdError) as exsinfo:
            assert self.target.modify_iqn('t_test0', 'iqn.2020-02.com.example:pyittarget_2')
        assert exsinfo.type == consts.CmdError

    def test_modify_portal(self):
        """修改ISCSITarget，当修改已配置target的portal信息时，对应的target也会修改,测试用例包括：修改target成功/target不存在修改失败"""
        assert self.target.modify_portal.func(self.target, 'pytm_it_target_1', '10.203.1.88', '3260') is True
        with pytest.raises(consts.CmdError) as exsinfo:
            assert self.target.modify_portal('t_test0', '10.203.1.99', '3260')
        assert exsinfo.type == consts.CmdError

    def test_delete(self):
        subprocess.run('crm cof primitive pytd_it_target_1 iSCSITarget params iqn="iqn.2020-02.com.example:pyitdtest1" implementation=lio-t portals="10.203.1.98:3260" op start timeout=50 stop timeout=40 op monitor interval=15 timeout=40 meta target-role=Stopped', shell=True)
        assert self.target.delete.func(self.target, 'pytd_it_target_1')
        with pytest.raises(consts.CmdError) as exsinfo:
            assert self.target.delete('pytd_it_target_1')
        assert exsinfo.type == consts.CmdError


@pytest.mark.ilu
class TestISCSILogicalUnit:

    def setup_class(self):
        subprocess.run('python3 vtel.py stor r c res_pyilu -s 4m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py stor r c res_pyilu1 -s 4m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py stor r c res_pyilu2 -s 4m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py stor r c res_pyilu3 -s 4m -a -num 1', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py iscsi h c pyilu_host1 iqn.2020-04.feixitek.com:pyilu01', shell=True)
        subprocess.run('python3 vtel.py iscsi h c pyilu_host2 iqn.2020-04.feixitek.com:pyilu02', shell=True)
        subprocess.run('python3 vtel.py iscsi pt c pyilu_portal_1 -ip 10.203.1.184', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi tg c pyilu_target_1 -iqn iqn.2020-02.com.example:pyilu1 -portal pyilu_portal_1', shell=True)
        self.iscsilu = crm.ISCSILogicalUnit()
        path = self.iscsilu.js.json_data['Disk']['res_pyilu1']
        lunid = int(path[-4:]) - 1000
        create_ilu_cmd = f'crm conf primitive res_pyilu1 iSCSILogicalUnit params ' \
              f'target_iqn="iqn.2020-02.com.example:pyilu1" ' \
              f'implementation=lio-t ' \
              f'lun={lunid} ' \
              f'path={path} ' \
              f'allowed_initiators="iqn.2020-04.feixitek.com:pyilu01" ' \
              f'op start timeout=40 interval=0 ' \
              f'op stop timeout=40 interval=0 ' \
              f'op monitor timeout=40 interval=15 ' \
              f'meta target-role=Stopped'
        subprocess.run(create_ilu_cmd, shell=True)
        subprocess.run('crm cof colocation col_res_pyilu1 inf: res_pyilu1 pyilu_target_1', shell=True)
        subprocess.run('crm cof order or_res_pyilu1 pyilu_target_1 res_pyilu1', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)

    def teardown_class(self):
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        subprocess.run('crm res stop res_pyilu1', shell=True)
        subprocess.run('crm conf del res_pyilu1', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py stor r d res_pyilu -y', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py stor r d res_pyilu1 -y', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py stor r d res_pyilu2 -y', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py stor r d res_pyilu3 -y', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py iscsi tg d pyilu_target_1', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py iscsi pt d pyilu_portal_1', shell=True)
        # 手动删host
        # subprocess.run('python3 vtel.py iscsi h d pyilu_host1', shell=True)
        # subprocess.run('python3 vtel.py iscsi h d pyilu_host2', shell=True)

    def test_create(self):
        """创建ISCSILogicalUnit"""
        self.iscsilu.js.json_data = self.iscsilu.js.read_json()
        path = self.iscsilu.js.json_data['Disk']['res_pyilu']
        # disk = iscsi.Disk()
        # disk_data = disk.show('res_pyilu')
        # path = disk_data[0][1]
        lunid = int(path[-4:]) - 1000
        # iscsilu = crm.ISCSILogicalUnit()
        assert self.iscsilu.create('res_pyilu', 'iqn.2020-04.feixitek.com:pycversaplx00', lunid, path,
                              'iqn.2020-11.com.example:pytest01') is True
        # ISCSILogicalUnit 已存在
        with pytest.raises(consts.CmdError) as exsinfo:
            self.iscsilu.create('res_pyilu1', 'iqn.2020-04.feixitek.com:versaplx00', lunid, path,
                           'iqn.2020-11.com.example:pytest01')
        assert exsinfo.type == consts.CmdError
        # 数据清洗
        subprocess.run('crm res stop res_pyilu', shell=True)
        time.sleep(3)
        subprocess.run('crm conf del res_pyilu', shell=True)

    def test_modify_initiators(self):
        """修改ISCSILogicalUnit映射iqn"""
        assert self.iscsilu.modify_initiators('res_pyilu1', ['iqn.2020-04.feixitek.com:pyilu01', 'iqn.2020-04.feixitek.com:pyilu02'])
        with pytest.raises(consts.CmdError) as exsinfo:
            self.iscsilu.modify_initiators('res_pyilu_1', ['iqn.2020-04.feixitek.com:pyilu01', 'iqn.2020-04.feixitek.com:pyilu02'])
        assert exsinfo.type == consts.CmdError

    def test_modify_target_iqn(self):
        """修改Target IQN"""
        assert self.iscsilu.modify_target_iqn('res_pyilu1', 'iqn.2020-02.com.example:pyilu2')
        with pytest.raises(consts.CmdError) as exsinfo:
            self.iscsilu.modify_target_iqn('res_pyilu_1', 'aiqn.2020-02.com.example:pyilu2')
        assert exsinfo.type == consts.CmdError

    def test_create_mapping(self):
        """创建mapping"""
        assert self.iscsilu.create_mapping('res_pyilu2','pyilu_target_1', ['iqn.2020-04.feixitek.com:pyilu01']) is True
        subprocess.run('crm res stop res_pyilu2', shell=True)
        time.sleep(3)
        subprocess.run('crm conf del res_pyilu2', shell=True)

    def test_delete(self):
        """删除ISCSILogicalUnit"""
        self.iscsilu.create_mapping('res_pyilu3', 'pyilu_target_1', ['iqn.2020-04.feixitek.com:pyilu01'])
        assert self.iscsilu.delete('res_pyilu3') is True
        # 删除不存在
        with pytest.raises(consts.CmdError) as exsinfo:
            self.iscsilu.delete('res_pyilu3')
        assert exsinfo.type == consts.CmdError