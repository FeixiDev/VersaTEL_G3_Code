# import os
# import sys
import time
from unittest.mock import patch
import pytest

# import iscsi_json
# import execute
# import iscsi_json
from execute import iscsi
from execute import crm
import sundry
import iscsi_json
import subprocess
from execute.crm import execute_crm_cmd


class TestDisk:

    def setup_class(self):
        subprocess.run('python3 vtel.py stor r c res_test1 -s 10m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py stor r c res_test2 -s 10m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        self.disk = iscsi.Disk()

    def teardown_class(self):
        print('\n------teardown-------')
        subprocess.run('python3 vtel.py stor r d res_test1 -y', shell=True)
        subprocess.run('python3 vtel.py stor r d res_test2 -y', shell=True)
        subprocess.run('python3 vtel.py stor r s', shell=True)
        # json 文件不能及时更新,调用方法进行手动更新该对象（不调用的话 json 文件的disk 还是在）
        print('teardown')
        self.disk.show('all')

    # 根据 linstor 资源更新 disk，无传入参数，返回 disks 字典(可能为空)
    def test_update_disk(self, mocker):
        """该方法根据 linstor 资源更新 disk，测试用例包括：获取非空字典/空字典"""
        assert len(self.disk.update_disk()) >= 2
        # 清空 disk
        # subprocess.run('python3 vtel.py stor r d res_test1 -y', shell=True)
        # subprocess.run('python3 vtel.py stor r d res_test2 -y', shell=True)
        # subprocess.run('python3 vtel.py stor r s', shell=True)
        # mocker.patch.object(iscsi.Disk.update_disk, 'linstor_res', [])
        mocker.patch.object(iscsi.Disk, 'update_disk', return_value=[])
        assert self.disk.update_disk() == []

    def test_show(self):
        """展示disk，测试用例包括：'all'/'res_name'/不存在资源"""
        # subprocess.run('python3 vtel.py stor r c res_test1 -s 10m -a -num 1', shell=True)
        # subprocess.run('python3 vtel.py stor r c res_test2 -s 10m -a -num 1', shell=True)
        # subprocess.run('python3 vtel.py iscsi d s', shell=True)
        assert len(self.disk.show('all')) >= 2
        assert self.disk.show('res_test1')[0][0] == 'res_test1'
        # 不存在
        assert self.disk.show('res_test3') == []


class TestHost:

    def setup_class(self):
        subprocess.run('python3 vtel.py stor r c res_test1 -s 10m -a -num 1', shell=True)
        self.host = iscsi.Host()
        self.hostg = iscsi.HostGroup()
        self.diskg = iscsi.DiskGroup()
        self.map = iscsi.Map()
        self.host.create('test_host', 'iqn.2020-04.feixitek.com:pytest001')
        self.host.create('test_host_hg1', 'iqn.2020-04.feixitek.com:pytest0991')
        self.host.create('test_host_hg2', 'iqn.2020-04.feixitek.com:pytest0992')
        self.host.create('test_host_hg3', 'iqn.2020-04.feixitek.com:pytest0993')

        self.host.show('all')
        self.hostg.create('test_hg1', ['test_host_hg1', 'test_host_hg2'])
        self.hostg.create('test_hg2', ['test_host_hg3'])
        self.diskg.create('test_dg', ['res_test1'])
        self.map.create('test_map', ['test_hg1', 'test_hg2'], ['test_dg'])

    def teardown_class(self):
        print('\n------teardown-------')
        self.host.show('all')
        execute_crm_cmd('crm res stop res_test1')
        execute_crm_cmd('crm conf del res_test1')
        subprocess.run('python3 vtel.py stor r d res_test1 -y', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)

    # -------------  add -------------- 2020.12.28
    def test_check_iqn(self):
        """检查iqn格式，测试用例包括：格式正确/格式不正确"""
        # ----- modify ------ 2021.01.11
        assert self.host._check_iqn('iqn1') is False
        assert self.host._check_iqn('iqn.2020-04.feixitek.com:pytest01') is True

    # ------------- modify ------------ 2021.01.11

    # 已存在返回 None ，iqn 格式不对返回 None ，新建成功返回 True
    def test_create(self):
        """创建host，测试用例包括：host 已存在/iqn格式不正确/创建成功"""
        # 已存在
        with patch('builtins.print') as terminal_print:
            self.host.create('test_host', 'iqn.2020-04.feixitek.com:pytest001')
            terminal_print.assert_called_with('Fail! The Host test_host already existed.')
        # 不存在，但iqn 格式不正确（要未新建过的host名才会判断iqn格式）
        with patch('builtins.print') as terminal_print:
            self.host.create('test_host3', 'iqn1')
            terminal_print.assert_called_with('The format of IQN is wrong. Please confirm and fill in again.')
        # 新建成功
        assert self.host.create('test_host1', 'iqn.2020-04.feixitek.com:pytest01')

    def test_show(self):
        """展示host，测试用例包括：全部 host 展示/展示指定 host /指定 host 不存在"""
        assert len(self.host.show('all')) >= 3
        assert self.host.show('test_host1') == [['test_host1', 'iqn.2020-04.feixitek.com:pytest01']]
        # 不存在
        assert self.host.show('test_host3') == []

    # 修改失败：1.不存在，return None 输入提示语句；修改成功：
    def test_modify(self, monkeypatch):
        monkeypatch.setattr('builtins.input', lambda: "y")
        """修改host，测试用例包括：host 不存在/修改成功"""
        # 不存在 host
        with patch('builtins.print') as terminal_print:
            self.host.modify('test_hostABC', 'iqn.2020-04.feixitek.com:pytest0999')
            terminal_print.assert_called_with('Fail! Can\'t find test_hostABC')
        # 修改成功
        assert not self.host.modify('test_host1', 'iqn.2020-04.feixitek.com:pytest0999')
        # assert not self.host.modify('test_host1', 'iqn')

    @pytest.fixture()
    def handle_data(self, monkeypatch):
        # 数据处理
        yield
        monkeypatch.setattr('builtins.input', lambda: "y")
        self.diskg.delete('test_dg')
        self.host.delete('test_host')

    # 删除失败：1.不存在，return None 输入提示语句 2.已配置在 HostGroup，return None 输出提示语句；删除成功： return True
    def test_delete(self, monkeypatch, handle_data):
        """删除 host，测试用例包括：host 不存在/ host 已配置在 HostGroup 中/删除成功"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        # 不存在
        with patch('builtins.print') as terminal_print:
            self.host.delete('test_hostABC')
            terminal_print.assert_called_with('Fail！Can\'t find test_hostABC')
        # 删除已存在而且没有配置在HostGroup中的host
        with patch('builtins.print') as terminal_print:
            self.host.delete('test_host1')
        terminal_print.assert_called_with('Delete test_host1 successfully')
        # 已配置 HostGroup , 能删除
        with patch('builtins.print') as terminal_print:
            self.host.delete('test_host_hg1')
            terminal_print.assert_called_with('Delete test_host_hg1 successfully')
        # 同时如果配置该host的hg是最后一个同时删除hg
        with patch('builtins.print') as terminal_print:
            self.host.delete('test_host_hg2')
            terminal_print.assert_called_with('Delete test_host_hg2 successfully')
        assert self.hostg.show('test_hg1') == []
        # 该 host 是 test_map 的 hostgroup 唯一成员，删除后该hostgroup被删除，同时test_map也被删除
        with patch('builtins.print') as terminal_print:
            self.host.delete('test_host_hg3')
            terminal_print.assert_called_with('Delete test_host_hg3 successfully')
        assert self.hostg.show('test_hg2') == []
        assert self.map.show('test_map') == []
        self.diskg.show('all')


class TestDiskGroup:

    def setup_class(self):
        subprocess.run('python3 vtel.py stor r c res_test -s 10m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py stor r c res_test1 -s 10m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        self.host = iscsi.Host()
        self.hostg = iscsi.HostGroup()
        self.diskg = iscsi.DiskGroup()
        self.map = iscsi.Map()
        self.host.create('test_host', 'iqn.2020-04.feixitek.com:pytest0999')
        self.diskg.create('test_dg', ['res_test', 'res_test1'])
        self.diskg.create('test_dg2', ['res_test1'])
        self.diskg.show('all')

        self.hostg.create('test_hg', ['test_host'])
        self.map.create('map1', ['test_hg'], ['test_dg'])
        self.map.show('all')

    def teardown_class(self):
        print('\n------teardown-------')
        # 需要在前面删,不然在res删除之后删json文件不一致或者可以先同步res再删
        try:
            execute_crm_cmd('crm res stop res_test')
            execute_crm_cmd('crm conf del res_test')
            execute_crm_cmd('crm res stop res_test1')
            execute_crm_cmd('crm conf del res_test1')
        except Exception:
            print(Exception)
        finally:
            subprocess.run('python3 vtel.py stor r d res_test -y', shell=True)
            subprocess.run('python3 vtel.py stor r d res_test1 -y', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)

    # # 1.判断 DiskGroup 是否存在，存在返回 None 2.遍历 disk 列表，若发现 disk 不存在返回 None 3.创建成功返回 True
    # def test_create_diskgroup(self):
    #     # DiskGroup 已存在
    #     assert not self.diskg.create_diskgroup('test_dg', ['res_test'])
    #     with patch('builtins.print') as terminal_print:
    #         self.diskg.create_diskgroup('test_dg', ['res_test'])
    #         terminal_print.assert_called_with('Fail! The Disk Group test_dg already existed.')
    #     # disk 不存在
    #     with patch('builtins.print') as terminal_print:
    #         self.diskg.create_diskgroup('test_dg1', ['res_test', 'res_test0'])
    #         terminal_print.assert_called_with('Fail! Can\'t find res_test0.Please give the true name.')
    #     # 创建成功的测试用例
    #     assert self.diskg.create_diskgroup('test_dg1', ['res_test'])
    #
    # # 返回指定 DiskGroup ，如果为 DiskGroup 不存在，返回 None,否则返回该 DiskGroup
    # def test_get_spe_diskgroup(self):
    #     # DiskGroup 不存在测试用例
    #     assert not self.diskg.get_spe_diskgroup('test_dg2')
    #     # DiskGroup 存在测试用例
    #     assert self.diskg.get_spe_diskgroup('test_dg1')
    #
    # # 该函数没有返回值，调用了本模块get_all_diskgroup()和sundry的show_iscsi_data()
    # def test_show_all_diskgroup(self):
    #     assert self.diskg.show_all_diskgroup() is None
    #
    # # 该函数没有返回值，调用了本模块get_spe_diskgroup()和sundry的show_iscsi_data()
    # def test_show_spe_diskgroup(self):
    #     assert self.diskg.show_spe_diskgroup('test_dg1') is None
    #
    # # 1.先检查 HostGroup 是否存在，不存在返回 None 2.再判断 HostGroup 是否已经配置在 Map里，已配置返回None 3.不满足前两个返回条件，删除后依然返回None
    # # 这个方法无返回值
    # def test_delete_diskgroup(self):
    #     with patch('builtins.print') as terminal_print:
    #         self.diskg.delete_diskgroup('test_dg2')
    #         terminal_print.assert_called_with('Fail! Can\'t find test_dg2')
    #     # 保留测试用例，该分支有bug
    #     with patch('builtins.print') as terminal_print:
    #         self.map.show_spe_map('map1')
    #         self.diskg.delete_diskgroup('test_dg')
    #         terminal_print.assert_called_with('Fail! The diskgroup already map,Please delete the map')
    #     with patch('builtins.print') as terminal_print:
    #         self.diskg.delete_diskgroup('test_dg1')
    #         terminal_print.assert_called_with('Delete success!')

    # -------------- modify -------------- 2021.01.11
    def test_create(self):
        """创建 diskgroup，测试用例包括：diskgroup已存在，创建失败/所配置的disk不存在，创建失败/创建成功"""
        # DiskGroup 已存在
        assert not self.diskg.create('test_dg', ['res_test'])
        with patch('builtins.print') as terminal_print:
            self.diskg.create('test_dg', ['res_test'])
            terminal_print.assert_called_with('Fail! The Disk Group test_dg already existed.')
        # disk 不存在
        with patch('builtins.print') as terminal_print:
            self.diskg.create('test_dg1', ['res_test', 'res_test0'])
            terminal_print.assert_called_with('Fail! Can\'t find res_test0.Please give the true name.')
        # 创建成功的测试用例
        assert self.diskg.create('test_dg1', ['res_test'])

    def test_show(self):
        """展示 diskgroup，测试用例包括：'all'/'dg_name'/不存在的dg"""
        assert len(self.diskg.show('all')) >= 2
        assert self.diskg.show('test_dg1') == [['test_dg1', 'res_test']]
        assert self.diskg.show('test_dg0') == []

    def test_delete(self, monkeypatch):
        """删除 diskgroup，测试用例包括：diskg不存在，删除失败/已配置在map中，删除成功/删除成功"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        with patch('builtins.print') as terminal_print:
            self.diskg.delete('test_dg0')
            terminal_print.assert_called_with('Fail! Can\'t find test_dg0')
        # 已配置在map中
        with patch('builtins.print') as terminal_print:
            self.diskg.delete('test_dg')
            terminal_print.assert_called_with('Delete test_dg success!')
            assert self.map.show('map1') == []
        with patch('builtins.print') as terminal_print:
            self.diskg.delete('test_dg1')
            terminal_print.assert_called_with('Delete test_dg1 success!')

    # -----------   add  -----------------  2020.12.28
    def test_add_disk(self,monkeypatch):
        """diskgroup 新增 disk，测试用例包括：新增成功/新增失败：使用不存在的dg；使用已存在dg的res资源；使用不存在的res资源"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        self.diskg.create('test_dg', ['res_test'])
        self.map.create('map1', ['test_hg'], ['test_dg', 'test_dg2'])
        # 新增成功
        assert not self.diskg.add_disk('test_dg', ['res_test1'])
        # 不存在
        with patch('builtins.print') as terminal_print:
            self.diskg.add_disk('test_dg0', ['res_0'])
            terminal_print.assert_called_with('Fail！Can\'t find test_dg0')
        with patch('builtins.print') as terminal_print:
            self.diskg.add_disk('test_dg', ['res_test'])
            terminal_print.assert_called_with('res_test already exists in test_dg')
        with patch('builtins.print') as terminal_print:
            self.diskg.add_disk('test_dg', ['res_O'])
            terminal_print.assert_called_with('The disk does not exist in the configuration file and cannot be added')

    @pytest.fixture()
    def handle_data(self, monkeypatch):
        # 数据处理
        yield
        monkeypatch.setattr('builtins.input', lambda: "y")
        self.host.delete('test_host')

    def test_remove_disk(self, monkeypatch, handle_data):
        """diskgroup 移除 disk，测试用例包括：移除成功/移除失败：使用不存在的dg；使用不存在dg的res资源/移除全部的res会删除该dg"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        assert not self.diskg.remove_disk('test_dg', ['res_test'])
        # 移除失败
        with patch('builtins.print') as terminal_print:
            self.diskg.remove_disk('test_dg0', ['res_test1'])
            terminal_print.assert_called_with('Fail！Can\'t find test_dg0')
        with patch('builtins.print') as terminal_print:
            self.diskg.remove_disk('test_dg', ['res_O'])
            terminal_print.assert_called_with('res_O does not exist in test_dg and cannot be removed')
        # 只有一个资源移除后是否会删掉该dg , 会移除该 dg 和 所配置该 dg 的map
        self.diskg.remove_disk('test_dg', ['res_test1'])
        assert self.diskg.show('test_dg') == []
        # 该 map 还剩下一个 test_dg2，移除 test_dg2 的 res_test1 map会被删除
        self.diskg.remove_disk('test_dg2', ['res_test1'])
        assert self.diskg.show('test_dg2') == []
        assert self.map.show('map1') == []
        # 这里是输出删除 Iscsilogicalunit 提示语句


class TestHostGroup:

    def setup_class(self):
        subprocess.run('python3 vtel.py stor r c res_test -s 10m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        # 创建 Map
        # subprocess.run('python3 vtel.py iscsi m c map1 -dg test_dg -hg test_hg', shell=True)
        # subprocess.run('python3 vtel.py iscsi m s', shell=True)
        self.host = iscsi.Host()
        self.hostg = iscsi.HostGroup()
        self.map = iscsi.Map()
        self.diskg = iscsi.DiskGroup()
        self.host.create('test_host1', 'iqn.2020-04.feixitek.com:pytest01')
        self.host.create('test_host2', 'iqn.2020-04.feixitek.com:pytest002')

        self.diskg.create('test_dg', ['res_test'])
        self.hostg.create('test_hg', ['test_host1'])
        self.hostg.create('test_hg2', ['test_host2'])
        self.map.create('map1', ['test_hg'], ['test_dg'])

    def teardown_class(self):
        print('\n------teardown-------')
        execute_crm_cmd('crm res stop res_test')
        execute_crm_cmd('crm conf del res_test')
        subprocess.run('python3 vtel.py stor r d res_test -y', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)

    # # 1.判断 HostGroup 是否存在，存在返回 None 2.遍历 Host 列表，若发现 Host 不存在返回 None 3.创建成功返回 True
    # def test_create_hostgroup(self):
    #     # 已存在 HostGroup 测试用例
    #     with patch('builtins.print') as terminal_print:
    #         self.hostg.create_hostgroup('test_hg', ['test_host1'])
    #         terminal_print.assert_called_with('Fail! The HostGroup test_hg already existed.')
    #     # 提供的 host 列表中有不存在的 host 测试用例
    #     with patch('builtins.print') as terminal_print:
    #         self.hostg.create_hostgroup('test_hg1', ['test_host1', 'test_host0'])
    #         terminal_print.assert_called_with('Fail! Can\'t find test_host0.Please give the true name.')
    #     # 创建成功的测试用例
    #     assert self.hostg.create_hostgroup('test_hg1', ['test_host1'])
    #     # self.hostg.show_all_hostgroup()
    #
    # # 返回指定 DiskGroup ，如果为 DiskGroup 不存在，返回 None,否则返回该 DiskGroup
    # def test_get_spe_hostgroup(self):
    #     # DiskGroup 不存在
    #     assert not self.hostg.get_spe_hostgroup('test_hg2')
    #     # DiskGroup 存在
    #     assert self.hostg.get_spe_hostgroup('test_hg1')
    #
    # # 该函数没有返回值，调用了本模块get_all_hostgroup()和sundry的show_iscsi_data()
    # def test_show_all_hostgroup(self):
    #     assert self.hostg.show_all_hostgroup() is None
    #
    # # 该函数没有返回值，调用了本模块get_sep_hostgroup()和sundry的show_iscsi_data()
    # def test_show_spe_hostgroup(self):
    #     assert self.hostg.show_spe_hostgroup('test_hg1') is None
    #
    # # 1.先检查 HostGroup 是否存在，不存在返回 None 2.再判断 HostGroup 是否已经配置在 Map里，已配置返回None 3.不满足前两个返回条件，删除后依然返回None
    # # 这个方法无返回值
    # def test_delete_hostgroup(self):
    #     with patch('builtins.print') as terminal_print:
    #         self.hostg.delete_hostgroup('test_hg2')
    #         terminal_print.assert_called_with('Fail! Can\'t find test_hg2')
    #     # print(f'判断条件：{self.js.check_value("Map", "test_dg")["result"]}')
    #     # 保留测试用例，该分支有bug
    #     with patch('builtins.print') as terminal_print:
    #         # print(f'判断条件：{self.js.check_value("Map","test_dg")["result"]}')
    #         # self.map.show_all_map()
    #         self.hostg.delete_hostgroup('test_hg')
    #         terminal_print.assert_called_with('Fail! The hostgroup already map,Please delete the map')
    #     with patch('builtins.print') as terminal_print:
    #         self.hostg.delete_hostgroup('test_hg1')
    #         terminal_print.assert_called_with('Delete success!')

    # ------------------- modify ---------------- 2021.01.11
    def test_create(self):
        """创建HostGroup，测试用例包括：HostGroup已存在，创建失败/所配置的 host 不存在，创建失败/创建成功"""
        # 已存在 HostGroup 测试用例
        # print('test_hg', self.hostg.show('test_hg'))
        with patch('builtins.print') as terminal_print:
            self.hostg.create('test_hg', ['test_host1'])
            terminal_print.assert_called_with('Fail! The HostGroup test_hg already existed.')
        # 提供的 host 列表中有不存在的 host 测试用例
        with patch('builtins.print') as terminal_print:
            self.hostg.create('test_hg1', ['test_host1', 'test_host0'])
            terminal_print.assert_called_with('Fail! Can\'t find test_host0.Please give the true name.')
        # 创建成功的测试用例
        assert self.hostg.create('test_hg1', ['test_host1'])

    def test_show(self):
        """展示 HostGroup，测试用例包括：'all'/'hg_name'/不存在hg"""
        # assert self.hostg.show('all') == [['test_hg', 'test_host1'], ['test_hg1', 'test_host1']]
        assert len(self.hostg.show('all')) >= 1
        assert self.hostg.show('test_hg1') == [['test_hg1', 'test_host1']]
        assert self.hostg.show('test_hg0') == []

    def test_delete(self, monkeypatch):
        """删除 HostGroup，测试用例包括：HostGroup不存在，删除失败/已配置在map中，删除失败/删除成功"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        # assert self.hostg.create('test_hg1', ['test_host1'])
        # 不存在
        with patch('builtins.print') as terminal_print:
            self.hostg.delete('test_hg0')
            terminal_print.assert_called_with('Fail! Can\'t find test_hg0')
        # 已配置在map中
        with patch('builtins.print') as terminal_print:
            self.hostg.delete('test_hg')
            terminal_print.assert_called_with('Delete test_hg success!')
        assert self.map.show('map1') == []
        # 删除成功
        with patch('builtins.print') as terminal_print:
            self.hostg.delete('test_hg1')
            terminal_print.assert_called_with('Delete test_hg1 success!')
        self.hostg.create('test_hg', ['test_host1'])

    # --------------------- add  --------------  2020.12.28
    def test_add_host(self, monkeypatch):
        """hostgroup 新增 host,测试用例包括：新增 host 成功/新增失败：新增 host 不存在/新增 host 已存在于该 hostgroup/该 hostgroup 不存在"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        self.map.create('map1', ['test_hg', 'test_hg2'], ['test_dg'])
        # 存在
        assert not self.hostg.add_host('test_hg', ['test_host2'])
        # 不存在
        with patch('builtins.print') as terminal_print:
            self.hostg.add_host('test_hg0', ['test_host2'])
            terminal_print.assert_called_with('Fail！Can\'t find test_hg0')
        with patch('builtins.print') as terminal_print:
            self.hostg.add_host('test_hg', ['test_host1'])
            terminal_print.assert_called_with('test_host1 already exists in test_hg')
        with patch('builtins.print') as terminal_print:
            self.hostg.add_host('test_hg', ['test_host0'])
            terminal_print.assert_called_with('test_host0 does not exist in the configuration file and cannot be added')

    @pytest.fixture()
    def handle_data(self, monkeypatch):
        # 数据处理
        yield
        monkeypatch.setattr('builtins.input', lambda: "y")
        self.diskg.delete('test_dg')
        self.host.delete('test_host1')
        self.host.delete('test_host2')

    def test_remove_host(self, monkeypatch, handle_data):
        """hostgroup 移除 host，测试用例包括：移除 host 成功/新增失败：移除 host 不存在/移除 host 不存在于该 hostgroup/该 hostgroup 不存在/移除该 hostgroup最后一名成员"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        # 存在
        assert not self.hostg.remove_host('test_hg', ['test_host2'])
        # 不存在
        with patch('builtins.print') as terminal_print:
            self.hostg.remove_host('test_hg0', ['test_host2'])
            terminal_print.assert_called_with('Fail！Can\'t find test_hg0')
        with patch('builtins.print') as terminal_print:
            self.hostg.remove_host('test_hg', ['test_host0'])
            terminal_print.assert_called_with('test_host0 does not exist in test_hg and cannot be removed')
        # hg 的 host 全部移除，配置了该 hg 的 map 同时被删除
        # with 结构中会屏蔽输出
        # 移除 test_hg 最后一个 host，test_hg会被删除
        self.hostg.remove_host('test_hg', ['test_host1'])
        assert self.hostg.show('test_hg') == []
        # map1 中 hostgroup 还有最后一个成员 test_hg2 ，test_hg2中还有最后一个成员 test_host2
        self.hostg.remove_host('test_hg2', ['test_host2'])
        assert self.hostg.show('test_hg2') == []
        assert self.map.show('map1') == []
        # 输出使用 disk iscsilogicalunit 删除提示

    # # 返回所有 HostGroup，如果为 HostGroup 空，返回{},否则返回 HostGroup 非空字典
    # def test_get_all_hostgroup(self):
    #     # HostGroup 不为空
    #     assert self.hostg.get_all_hostgroup()
    #     # HostGroup 为空
    #     self.map.delete_map('map1')
    #     self.hostg.delete_hostgroup('test_hg')
    #     assert self.hostg.get_all_hostgroup() == {}


class TestMap:

    def setup_class(self):
        # 创建没有被使用过的disk
        subprocess.run('python3 vtel.py stor r c res_test1 -s 10m -a -num 1', shell=True)

        subprocess.run('python3 vtel.py stor r c res_test -s 10m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        self.host = iscsi.Host()
        self.hostg = iscsi.HostGroup()
        self.map = iscsi.Map()
        self.diskg = iscsi.DiskGroup()
        self.host.create('test_host1', 'iqn.2020-04.feixitek.com:pytest0101')
        self.host.create('test_host', 'iqn.2020-04.feixitek.com:pytest01')
        self.diskg.create('test_dg1', ['res_test1'])
        self.diskg.create('test_dg', ['res_test'])
        self.hostg.create('test_hg1', ['test_host1'])
        self.hostg.create('test_hg', ['test_host'])
        self.map.create('test_map', ['test_hg'], ['test_dg'])

    def teardown_class(self):
        print('\n------teardown-------')
        execute_crm_cmd('crm res stop res_test')
        execute_crm_cmd('crm conf del res_test')
        execute_crm_cmd('crm res stop res_test1')
        execute_crm_cmd('crm conf del res_test1')
        subprocess.run('python3 vtel.py stor r d res_test -y', shell=True)
        subprocess.run('python3 vtel.py stor r d res_test1 -y', shell=True)

        subprocess.run('python3 vtel.py iscsi d s', shell=True)

    # 函数已修改
    # # 1.map 是否存在/hostgroup是否存在/diskgroup是否存在
    # def test_pre_check_create_map(self):
    #     # map 已存在
    #     with pytest.raises(SystemExit) as exsinfo:
    #         with patch('builtins.print') as terminal_print:
    #             self.map.pre_check_create_map('test_map', 'test_hg1', 'test_dg')
    #             terminal_print.assert_called_with('The Map "test_map" already existed.')
    #     assert exsinfo.type == SystemExit
    #     # hostgroup 不存在
    #     with pytest.raises(SystemExit) as exsinfo:
    #         with patch('builtins.print') as terminal_print:
    #             self.map.pre_check_create_map('test_map1', 'test_hg0', 'test_dg')
    #             terminal_print.assert_called_with('Can\'t find test_hg0')
    #     assert exsinfo.type == SystemExit
    #     # diskgroup 不存在
    #     with pytest.raises(SystemExit) as exsinfo:
    #         with patch('builtins.print') as terminal_print:
    #             self.map.pre_check_create_map('test_map1', 'test_hg', 'test_dg0')
    #             terminal_print.assert_called_with('Can\'t find test_dg0')
    #     assert exsinfo.type == SystemExit
    #     # 同时满足三个条件
    #     assert self.map.pre_check_create_map('test_map1', ['test_hg'], ['test_dg'])
    #
    # def test_get_target(self):
    #     # 检测该函数有返回值
    #     assert self.map.get_target() is not None
    #
    # 先调用pre_check_create_map()，这个函数已经在前面测试了
    # Q：已经被使用过的disk(ilu) 没有做处理？ A:已经被使用的disk 再映射到新的host会提示
    # 1.新建一个map，使用的是没有被使用的disk   create_iscsilogicalunit 没有对创建 iscsilogicalunit 失败做处理
    # 2.新建一个map，使用的是已经被使用的disk并映射到新的host上面
    # 3.同时符合以上两种条件内容的新建map
    # def test_create_map(self):
    #     # 1.使用的是没有被使用的disk，调用 create_iscsilogicalunit，
    #     assert self.map.create_map('test_map1', ['test_hg'], ['test_dg'])
    #     # 2.使用的是已经被使用的disk并映射到新的host上面 调用 modify_iscsilogicalunit 这里会满足提示分支
    #     print('提示分支')
    #     assert self.map.create_map('test_map2', ['test_hg1'], ['test_dg'])
    #     # 3.同时符合以上两种条件内容的新建map
    #     assert self.map.create_map('test_map3', ['test_hg1'], ['test_dg', 'test_dg1'])
    #
    # # map 是否存在，存在返回非空列表[{map: map_data}, list_hg, list_dg],不存在返回 None
    # def test_get_spe_map(self):
    #     # 不存在
    #     with pytest.raises(SystemExit) as exsinfo:
    #         with patch('builtins.print') as terminal_print:
    #             self.map.get_spe_map('test_map0')
    #             terminal_print.assert_called_with('No map data')
    #     assert exsinfo.type == SystemExit
    #     # 存在
    #     assert self.map.get_spe_map('test_map1')
    #
    # # 该函数没有返回值，调用了本模块get_all_map()和sundry的show_iscsi_data()
    # def test_show_all_map(self):
    #     assert self.map.show_all_map() is None
    #
    # def test_show_spe_map(self):
    #     assert self.map.show_spe_map('test_map1') is not None
    #
    # # 1.map 存在返回 True，不存在返回 None
    # def test_pre_check_delete_map(self):
    #     # 不存在,warning_level = 1
    #     assert not self.map.pre_check_delete_map('test_map0')
    #     # 存在
    #     assert self.map.pre_check_delete_map('test_map1')

    # ----------modify ----------- 2021.01.11
    def test_create(self):
        """创建 Map，测试用例包括：Map 已存在，创建失败/所配置的 hostgroup 不存在，创建失败/所配置 diskgroup 不存在,创建失败/创建成功"""
        # 创建失败
        # map 已存在
        with pytest.raises(SystemExit) as exsinfo:
            with patch('builtins.print') as terminal_print:
                self.map.create('test_map', 'test_hg1', 'test_dg')
                terminal_print.assert_called_with('The Map "test_map" already existed.')
        assert exsinfo.type == SystemExit
        # hostgroup 不存在
        with pytest.raises(SystemExit) as exsinfo:
            with patch('builtins.print') as terminal_print:
                self.map.create('test_map1', 'test_hg0', 'test_dg')
                terminal_print.assert_called_with('Can\'t find test_hg0')
        assert exsinfo.type == SystemExit
        # diskgroup 不存在
        with pytest.raises(SystemExit) as exsinfo:
            with patch('builtins.print') as terminal_print:
                self.map.create('test_map1', 'test_hg', 'test_dg0')
                terminal_print.assert_called_with('Can\'t find test_dg0')
        assert exsinfo.type == SystemExit
        # 创建成功
        # 1.使用的是没有被使用的disk，调用 create_iscsilogicalunit，
        assert self.map.create('test_map1', ['test_hg'], ['test_dg'])
        # 2.使用的是已经被使用的disk并映射到新的host上面 调用 modify_iscsilogicalunit 这里会满足提示分支
        assert self.map.create('test_map2', ['test_hg1'], ['test_dg'])
        # 3.同时符合以上两种条件内容的新建map
        assert self.map.create('test_map3', ['test_hg1'], ['test_dg', 'test_dg1'])

    def test_show(self):
        """展示 Map，测试用例包括：'all'/'map_name'/不存在map"""
        assert len(self.map.show('all')) >= 4
        assert self.map.show('test_map3') == [['test_map3', 'test_hg1', 'test_dg test_dg1']]
        assert self.map.show('test_map0') == []

    # 1.使用pre_check_delete_map检查，map 不存在返回 None，删除成功返回 True
    def test_delete_map(self, monkeypatch):
        """删除 Map，测试用例包括：Map 不存在删除失败/删除成功"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        # 不存在
        with pytest.raises(SystemExit) as exsinfo:
            self.map.delete_map('test_map0')
        assert exsinfo.type == SystemExit
        # 删除成功
        assert self.map.delete_map('test_map3')

    # map modify -hg -a 调用
    def test_add_hg(self, monkeypatch):
        """map 新增 hostgroup,测试用例包括：新增成功/新增失败：map 不存在/新增 hg 已存在于该 map 中/新增 hg 不存在 json 文件中"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        # 成功增加
        assert self.map.add_hg('test_map1', ['test_hg1']) is None
        # 1.map 不存在
        with patch('builtins.print') as terminal_print:
            self.map.add_hg('map0', ['test_hg1'])
            terminal_print.assert_called_with('Fail！Can\'t find map0')
        # 2.hg 已存在 map 中
        with patch('builtins.print') as terminal_print:
            self.map.add_hg('test_map1', ['test_hg'])
            terminal_print.assert_called_with('test_hg already exists in test_map1')
        # 3.hg 不存在 json 文件中
        with patch('builtins.print') as terminal_print:
            self.map.add_hg('test_map1', ['test_hg0'])
            terminal_print.assert_called_with('test_hg0 does not exist in the configuration file and cannot be added')

    # map modify -dg -a 调用
    # 1.map 是否存在
    # 2. dg 是否已存在在 map 中/ dg 是否存在 json 文件中
    def test_add_dg(self, monkeypatch):
        """map 新增 diskgroup,测试用例包括：新增成功/新增失败：map 不存在/新增 dg 已存在于该 map 中/新增 dg 不存在 json 文件中"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        # 成功增加
        assert self.map.add_dg('test_map2', ['test_dg1']) is None
        # 1.map 不存在
        with patch('builtins.print') as terminal_print:
            self.map.add_dg('map0', ['test_dg1'])
            terminal_print.assert_called_with('Fail！Can\'t find map0')
        # 2.dg 已存在 map 中
        with patch('builtins.print') as terminal_print:
            self.map.add_dg('test_map2', ['test_dg'])
            terminal_print.assert_called_with('test_dg already exists in test_map2')
        # 3.dg 不存在 json 文件中
        with patch('builtins.print') as terminal_print:
            self.map.add_dg('test_map2', ['test_dg0'])
            terminal_print.assert_called_with('test_dg0 does not exist in the configuration file and cannot be added')

    # map modify -hg -r 调用
    # 1.map 是否存在
    # 2.hg 是否存在于该 map 中
    def test_remove_hg(self, monkeypatch):
        """map 移除 hostgroup,测试用例包括：移除成功/移除失败：map 不存在/移除 hg 不存在于该 map 中/移除 map 中部分 hg/移除 map 的 hg 最后一位成员"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        # 1.map 不存在
        with patch('builtins.print') as terminal_print:
            self.map.remove_hg('map0', ['test_hg1'])
            terminal_print.assert_called_with('Fail！Can\'t find map0')
        with patch('builtins.print') as terminal_print:
            self.map.remove_hg('test_map1', ['test_hg0'])
            terminal_print.assert_called_with('test_hg0 does not exist in test_map1 and cannot be removed')
        # 成功移除
        # 移除 map 中 HostGroup 的某些 hg 值，该 map 不会被删除
        self.map.remove_hg('test_map1', ['test_hg'])
        list_hg = self.map.show('test_map1')[0][1]
        assert list_hg == 'test_hg1'
        # 移除 map 中 HostGroup 的全部 hg 值，该 map 被删除
        with patch('builtins.print') as terminal_print:
            self.map.remove_hg('test_map1', ['test_hg1'])
            terminal_print.assert_called_with('test_map1 deleted')

    @pytest.fixture()
    def handle_data(self, monkeypatch):
        # 数据处理
        yield
        monkeypatch.setattr('builtins.input', lambda: "y")
        self.map.delete_map('test_map')
        self.hostg.delete('test_hg')
        self.hostg.delete('test_hg1')
        self.diskg.delete('test_dg1')
        self.diskg.delete('test_dg')
        self.host.delete('test_host')
        self.host.delete('test_host1')

    # map modify -dg -r 调用
    # 1.map 是否存在
    # 2.dg 是否存在于该 map 中
    def test_remove_dg(self, monkeypatch,handle_data):
        """map 移除 diskgroup,测试用例包括：移除成功/移除失败：map 不存在/移除 dg 不存在于该 map 中/移除 map 中部分 dg/移除 map 的 dg 最后一位成员"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        # 1.map 不存在
        with patch('builtins.print') as terminal_print:
            self.map.remove_dg('map0', ['test_dg1'])
            terminal_print.assert_called_with('Fail！Can\'t find map0')
        with patch('builtins.print') as terminal_print:
            self.map.remove_dg('test_map2', ['test_dg0'])
            terminal_print.assert_called_with('test_dg0 does not exist in test_map2 and cannot be removed')
        # 成功移除
        # 移除 map 中 HostGroup 的某些 dg 值，该 map 不会被删除
        self.map.remove_dg('test_map2', ['test_dg'])
        list_dg = self.map.show('test_map2')[0][2]
        assert list_dg == 'test_dg1'
        # 移除 map 中 HostGroup 的全部 dg 值，该 map 被删除
        with patch('builtins.print') as terminal_print:
            self.map.remove_dg('test_map2', ['test_dg1'])
            terminal_print.assert_called_with('test_map2 deleted')

    # # 获取 map 并返回，map 为空返回 {},不为空返回非空字典
    # def test_get_all_map(self):
    #     # map 不为空
    #     assert self.map.create('test_map3', ['test_hg1'], ['test_dg', 'test_dg1'])
    #     assert self.map.get_all_map()
    #     # map 为空
    #     # self.map.delete_map('test_map1')
    #     # self.map.delete_map('test_map2')
    #     self.map.delete_map('test_map3')
    #     time.sleep(1)
    #     assert self.map.get_all_map() == {}

    # 该函数被其他函数调用 create_iSCSILogicalUnit


@pytest.mark.portal
class TestPortal:
    # 注意测试用例 IP 不能是本机 ip 10.201.3.76
    def setup_class(self):
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        self.portal = iscsi.Portal()
        # print(self.portal.js.read_json())
        self.portal.create('vip_test1', '10.203.1.211')

    def teardown_class(self):
        print()
        # 以防删除不成功再次删除
        # self.portal.delete('vip_test1')

    # @pytest.mark.dependency(scope='class')
    def test_create(self):
        """创建portal，测试用例包括：(名字不合规范/ip不合规范/port超出范围/netmark超出范围[已测试其校验函数])portal已存在/ip已被使用"""
        with patch('builtins.print') as terminal_print:
            self.portal.create('$%^vip_test1', '10.203.1.215', 3260, 24)
            terminal_print.assert_called_with('$%^vip_test1 naming does not conform to the specification')
        with patch('builtins.print') as terminal_print:
            self.portal.create('vip_test0', '10.203.1...34211', 3260, 24)
            terminal_print.assert_called_with('10.203.1...34211 does not meet specifications')
        with patch('builtins.print') as terminal_print:
            self.portal.create('vip_test0', '10.203.1.215', 65555, 24)
            terminal_print.assert_called_with('65555 does not meet specifications(Range：3260-65535)')
        with patch('builtins.print') as terminal_print:
            self.portal.create('vip_test0', '10.203.1.215', 3260, 40)
            terminal_print.assert_called_with('40 does not meet specifications(Range：1-32)')
        with patch('builtins.print') as terminal_print:
            self.portal.create('vip_test1', '10.203.1.215', 3260, 24)
            terminal_print.assert_called_with('vip_test1 already exists, please use another name')
        with patch('builtins.print') as terminal_print:
            self.portal.create('vip_pytest2', '10.203.1.211')
            terminal_print.assert_called_with('10.203.1.211 is already in use, please use another IP')
        with patch('builtins.print') as terminal_print:
            self.portal.create('vip_pytest2', '10.203.1.213')
        terminal_print.assert_called_with('Create vip_pytest2 successfully')
        # self.portal.delete('vip_pytest')

    # @pytest.mark.dependency(depends=["TestPortal::test_create"])
    def test_modify(self, monkeypatch):
        """修改 portal,测试用例包括：portal不存在/ip格式不正确/port范围不正确/修改内容一致/portal已配置了target/portal没有配置target/只修改ip/port/netmask"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest0', '10.203.1.212', 3260, 24)
            terminal_print.assert_called_with('Fail！Can\'t find vip_pytest0')
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest2', '10.203.1.75', 3260, 24)
            terminal_print.assert_called_with('10.203.1.75 is already in use, please use another IP')
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest2', '10.203.1.212...', 3260, 24)
            terminal_print.assert_called_with('10.203.1.212... does not meet specifications')
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest2', '10.203.1.212', 3200, 24)
            terminal_print.assert_called_with('3200 does not meet specifications(Range：3260-65535)')
        # 修改内容与原来一致,若输入原来 ip 地址会提示该 ip 地址被使用（ps：三个参数全部为空时，portal_cmds模块会有特殊处理）
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest2', None, 3260, 24)
            terminal_print.assert_called_with('The parameters are the same, no need to modify')
        # 只修改 ip
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest2', '10.203.1.214', None, None)
            terminal_print.assert_called_with('Modify vip_pytest2 successfully')
        # 只修改 port
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest2', None, 3261, None)
            terminal_print.assert_called_with('Modify vip_pytest2 successfully')
        # 只修改 netmark
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest2', None, None, 22)
            terminal_print.assert_called_with('Modify vip_pytest2 successfully')
        # 修改的portal已配置了target，修改portblk的时候注意命名是否能找到
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest', '10.203.1.205', 3260, 24)
            # terminal_print.assert_called_with('Modify target_test successfully')
            terminal_print.assert_called_with('Modify vip_pytest successfully')
        # 修改的portal没有配置target
        with patch('builtins.print') as terminal_print:
            self.portal.modify('vip_pytest2', '10.203.1.213', 3260, 24)
            terminal_print.assert_called_with('Modify vip_pytest2 successfully')

        self.portal.modify('vip_pytest', '10.203.1.75', 3260, 24)
        self.portal.delete('vip_pytest2')

    def test__check_status(self):
        """检查 portal 创建的 status，测试用例包括：portal状态正常/portal状态异常"""
        with patch('builtins.print') as terminal_print:
            assert self.portal._check_status('vip_pytest') == 'OK'
            terminal_print.assert_called_with('Create vip_pytest successfully')
        # vip_pytest0 已删除的情况下
        with patch('builtins.print') as terminal_print:
            self.portal._check_status('vip_pytest0')
            terminal_print.assert_called_with('Failed to create vip_pytest0, please check')

    # @pytest.mark.dependency(depends=["TestPortal::test_create"])
    def test_delete(self, monkeypatch):
        """删除portal，测试用例包括：portal不存在/删除已配置target的portal，删除失败/删除成功"""
        monkeypatch.setattr('builtins.input', lambda: "y")
        with patch('builtins.print') as terminal_print:
            self.portal.delete('vip_pytest0')
        terminal_print.assert_called_with('Fail！Can\'t find vip_pytest0')
        with patch('builtins.print') as terminal_print:
            self.portal.delete('vip_test1')
        terminal_print.assert_called_with('Delete vip_test1 successfully')
        with patch('builtins.print') as terminal_print:
            self.portal.delete('vip_pytest')
        terminal_print.assert_called_with('In use：t_test. Can not delete')

    def test_show(self):
        """展示全部 portal"""
        # print(self.portal.show())
        assert len(self.portal.show()) >= 1

    # 格式要求：必须以字母开头，只能包含字母、数字、下划线_
    def test__check_name(self):
        """检查 portal_name，测试用例包括：不以字母开头/包含其他字符/包含中文字符/正确命名"""
        assert self.portal._check_name('sgfbfuhf')
        assert not self.portal._check_name('_sgfbfuhf')
        assert not self.portal._check_name('7_sgfbfuhf')
        assert not self.portal._check_name('sgfb*f$uhf')
        assert not self.portal._check_name('sgfbf你uhf')

    def test__check_ip(self):
        """检查 ip 格式，测试用例包括：包含其他字符/格式不正确/正确命名"""
        assert not self.portal._check_IP('10.11.11..11')
        assert not self.portal._check_IP('.10.11.11.11')
        assert not self.portal._check_IP('10.11.11.ss')
        assert self.portal._check_IP('10.11.11.10')

    def test__check_port(self):
        """检查 port 范围，测试用例包括：大于3620/等于3260/小于3260/非int"""
        assert self.portal._check_port(3260)
        assert not self.portal._check_port(3259)
        assert self.portal._check_port(3261)
        assert self.portal._check_port(65535)
        assert not self.portal._check_port(65536)
        assert not self.portal._check_port('6s55')

    def test__check_netmask(self):
        """检查 port 范围，测试用例包括：小于0/等于0/小于32/等于32/大于32/非int"""
        assert not self.portal._check_netmask(-1)
        assert not self.portal._check_netmask(0)
        assert self.portal._check_netmask(32)
        assert self.portal._check_netmask(31)
        assert not self.portal._check_netmask(33)
        assert not self.portal._check_netmask('3s')


@pytest.mark.target
class TestTarget:
    def setup_class(self):
        # subprocess.run('crm cof primitive pytest_portal_1 IPaddr2 params ip=10.203.1.184 cidr_netmask=24', shell=True)

        subprocess.run('python3 vtel.py iscsi portal c pytest_portal_1 -ip 10.203.1.184', shell=True)
        time.sleep(5)
        subprocess.run('python3 vtel.py iscsi portal c pytest_portal_2 -ip 10.203.1.185', shell=True)
        time.sleep(5)
        subprocess.run('crm cof primitive pytm_target_1 iSCSITarget params iqn="iqn.2020-02.com.example:pymtest1" implementation=lio-t portals="10.203.1.184:3260" op start timeout=50 stop timeout=40 op monitor interval=15 timeout=40 meta target-role=Stopped', shell=True)
        subprocess.run('crm cof colocation col_pytm_target_1_pytest_portal_1 inf: pytm_target_1 pytest_portal_1', shell=True)
        subprocess.run('crm cof order or_pytm_target_1_pytest_portal_1 pytest_portal_1 pytm_target_1', shell=True)
        subprocess.run('crm res start pytm_target_1', shell=True)
        subprocess.run(
            'crm cof primitive pytm_target_2 iSCSITarget params iqn="iqn.2020-02.com.example:pymtest2" implementation=lio-t portals="10.203.1.184:3260" op start timeout=50 stop timeout=40 op monitor interval=15 timeout=40 meta target-role=Stopped',
            shell=True)
        subprocess.run('crm cof colocation col_pytm_target_2_pytest_portal_1 inf: pytm_target_2 pytest_portal_1',
                       shell=True)
        subprocess.run('crm cof order or_pytm_target_2_pytest_portal_1 pytest_portal_1 pytm_target_2', shell=True)
        subprocess.run('crm res start pytm_target_2', shell=True)
        time.sleep(5)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        time.sleep(3)
        #环境中要先有一个pytest_res的DRBD资源(Disk)
        self.target = iscsi.Target()
        self.target.js.json_data = self.target.js.read_json()
        path = self.target.js.json_data['Disk']['pytest_res']
        lunid = int(path[-4:]) - 1000
        create_ilu_cmd = f'crm conf primitive pytest_res iSCSILogicalUnit params ' \
              f'target_iqn="iqn.2020-02.com.example:pymtest2" ' \
              f'implementation=lio-t ' \
              f'lun={lunid} ' \
              f'path={path} ' \
              f'allowed_initiators="iqn.2020-02.com.example:host1" ' \
              f'op start timeout=40 interval=0 ' \
              f'op stop timeout=40 interval=0 ' \
              f'op monitor timeout=40 interval=15 ' \
              f'meta target-role=Stopped'
        subprocess.run(create_ilu_cmd, shell=True)
        subprocess.run('crm cof colocation col_pytest_res inf: pytest_res pytm_target_2', shell=True)
        subprocess.run('crm cof order or_pytest_res pytm_target_2 pytest_res', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        time.sleep(3)
        self.target.js.json_data = self.target.js.read_json()

    def teardown_class(self):
        subprocess.run('crm res stop pytest_res', shell=True)
        time.sleep(3)
        subprocess.run('crm conf del pytest_res', shell=True)
        time.sleep(3)
        subprocess.run('crm res stop pytm_target_1', shell=True)
        # time.sleep(1)
        # subprocess.run('crm res ref', shell=True)
        time.sleep(3)
        subprocess.run('crm conf del pytm_target_1', shell=True)
        time.sleep(3)
        subprocess.run('crm res stop pytm_target_2', shell=True)
        # time.sleep(1)
        # subprocess.run('crm res ref', shell=True)
        time.sleep(3)
        subprocess.run('crm conf del pytm_target_2', shell=True)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        time.sleep(3)
        subprocess.run('crm res stop pytest_portal_1', shell=True)
        # time.sleep(1)
        # subprocess.run('crm res ref', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi portal d pytest_portal_1', shell=True)
        time.sleep(2)
        subprocess.run('crm res stop pytest_portal_2', shell=True)
        # subprocess.run('crm res ref', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi portal d pytest_portal_2', shell=True)

    def test__get_all_targetIqn(self):
        assert 'iqn.2020-02.com.example:pymtest1' in self.target._get_all_targetIqn()

    def test_create(self):

        with patch('builtins.print') as terminal_print:
            self.target.create('@pytc_target_1', 'iqn.2020-02.com.example:pytarget1', 'pytest_portal_1')
            terminal_print.assert_called_with('Wrong name:@pytc_target_1. It must start with a letter and consist of letters, numbers, and "_" ')

        with patch('builtins.print') as terminal_print:
            self.target.create('pytc_target_1', 'iqn.2020-02.com.example:pytarget_1', 'pytest_portal_1')
            terminal_print.assert_called_with('Wrong iqn：iqn.2020-02.com.example:pytarget_1. Please enter the correct iqn.')

        with patch('builtins.print') as terminal_print:
            self.target.create('pytm_target_1', 'iqn.2020-02.com.example:pytarget11', 'pytest_portal_1')
            terminal_print.assert_called_with('This name is already in use, please use another name')

        with patch('builtins.print') as terminal_print:
            self.target.create('pytc_target_1', 'iqn.2020-02.com.example:pytarget1', 'pytest_portal_1a')
            terminal_print.assert_called_with('pytest_portal_1a does not exist, please use the existing portal')

        with patch('builtins.print') as terminal_print:
            self.target.create('pytc_target_1', 'iqn.2020-02.com.example:pymtest1', 'pytest_portal_1')
            terminal_print.assert_called_with('The iqn:"iqn.2020-02.com.example:pymtest1" has been used')

        with patch('builtins.print') as terminal_print:
            self.target.create('pytc_target_1', 'iqn.2020-02.com.example:pytest1', 'pytest_portal_1')
            terminal_print.assert_called_with('Create pytc_target_1 successfully')
        subprocess.run('crm res stop pytc_target_1', shell=True)
        time.sleep(3)
        # subprocess.run('crm res ref', shell=True)
        # time.sleep(3)
        subprocess.run('crm conf del pytc_target_1', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        time.sleep(3)
        self.target.js.json_data = self.target.js.read_json()

    def test_modify(self, mocker):
        with patch('builtins.print') as terminal_print:
            self.target.modify('pytarget_233', 'iqn.2020-02.com.example:pytarget2', 'pytest_portal_2')
            terminal_print.assert_called_with("Fail！Can't find pytarget_233")
        with patch('builtins.print') as terminal_print:
            self.target.modify('pytm_target_1', 'iqn.2020-02.com.example:pytarget_2', 'pytest_portal_2')
            terminal_print.assert_called_with('Wrong iqn：iqn.2020-02.com.example:pytarget_2. Please enter the correct iqn.')
        with patch('builtins.print') as terminal_print:
            self.target.modify('pytm_target_1', 'iqn.2020-02.com.example:pymtest1', 'pytest_portal_2')
            terminal_print.assert_called_with('The iqn:"iqn.2020-02.com.example:pymtest1" has been used')
        with patch('builtins.print') as terminal_print:
            self.target.modify('pytm_target_1', 'iqn.2020-02.com.example:pytarget2', 'pytest_portal_1')
            #Create colocation:col_pytm_target_1_ successfully
            terminal_print.assert_called_with('Same as the portal used, please specify another one')
        with patch('builtins.print') as terminal_print:
            self.target.modify('pytm_target_1', 'iqn.2020-02.com.example:pytarget2', 'pytest_portal_2a')
            terminal_print.assert_called_with("Fail！Can't find pytest_portal_2a")
        with patch('builtins.print') as terminal_print:
            self.target.modify('pytm_target_1', 'iqn.2020-02.com.example:pytarget3', 'pytest_portal_2')
            terminal_print.assert_called_with('Modify pytm_target_1 successfully')
        with patch('builtins.print') as terminal_print:
            self.target.modify('pytm_target_1', 'iqn.2020-02.com.example:pymtest1', 'pytest_portal_1')
            terminal_print.assert_called_with('Modify pytm_target_1 successfully')
        subprocess.run('crm res start pytm_target_1', shell=True)
        mocker.patch.object(sundry, 'get_answer', return_value="no")
        # with patch('builtins.print') as terminal_print:
        #     self.target.modify('pytm_target_2', 'iqn.2020-02.com.example:pymtest4', 'pytest_portal_2')
        #     terminal_print.assert_called_with('Modify canceled')
        with pytest.raises(SystemExit) as exsinfo:
            self.target.modify('pytm_target_2', 'iqn.2020-02.com.example:pymtest4', 'pytest_portal_2')
        assert exsinfo.type == SystemExit
        subprocess.run('crm res start pytm_target_1', shell=True)

    def test_delete(self):
        subprocess.run(
            'crm cof primitive pytd_target iSCSITarget params iqn="iqn.2020-02.com.example:pydtest1" implementation=lio-t portals="10.203.1.184:3260" op start timeout=50 stop timeout=40 op monitor interval=15 timeout=40 meta target-role=Stopped',
            shell=True)
        subprocess.run('crm cof colocation col_pytd_target_pytest_portal_1 inf: pytd_target pytest_portal_1',
                       shell=True)
        subprocess.run('crm cof order or_pytd_target_pytest_portal_1 pytest_portal_1 pytd_target', shell=True)
        subprocess.run('crm res start pytd_target', shell=True)
        time.sleep(5)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        time.sleep(3)
        self.target.js.json_data = self.target.js.read_json()
        with patch('builtins.print') as terminal_print:
            self.target.delete('pytd_target1')
            terminal_print.assert_called_with("Fail！Can't find pytd_target1")
        with patch('builtins.print') as terminal_print:
            self.target.delete('pytd_target')
            terminal_print.assert_called_with('Delete target:pytd_target successfully')
        with patch('builtins.print') as terminal_print:
            self.target.delete('pytm_target_2')
            terminal_print.assert_called_with('In use：pytest_res. Can not delete')
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        time.sleep(3)
        self.target.js.json_data = self.target.js.read_json()

    def test_show(self):
        assert ['pytm_target_1', 'iqn.2020-02.com.example:pymtest1', 'pytest_portal_1', 'Started', ''] in self.target.show()

    def test_start(self, mocker):
        with patch('builtins.print') as terminal_print:
            self.target.start('pytm_target_1s')
            terminal_print.assert_called_with('pytm_target_1s does not exist')
        with patch('builtins.print') as terminal_print:
            self.target.start('pytm_target_1')
            terminal_print.assert_called_with('pytm_target_1 is in STARTED state')
        subprocess.run('crm res stop pytm_target_1', shell=True)
        time.sleep(2)
        with patch('builtins.print') as terminal_print:
            self.target.start('pytm_target_1')
            terminal_print.assert_called_with('pytm_target_1 has been started')
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="FAIL")
        with patch('builtins.print') as terminal_print:
            self.target.stop('pytm_target_1')
            terminal_print.assert_called_with('pytm_target_1 A is in FAILED state')
        subprocess.run('crm res start pytm_target_1', shell=True)

    def test_stop(self,mocker):
        with patch('builtins.print') as terminal_print:
            self.target.stop('pytm_target_1s')
            terminal_print.assert_called_with('pytm_target_1s does not exist')
        with patch('builtins.print') as terminal_print:
            self.target.stop('pytm_target_1')
            terminal_print.assert_called_with('pytm_target_1 has been stopped')
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="Stopped")
        mocker.patch.object(sundry, 'get_answer', return_value="no")
        with pytest.raises(SystemExit) as exsinfo:
            self.target.stop('pytm_target_1')
        assert exsinfo.type == SystemExit
        # with patch('builtins.print') as terminal_print:
        #     self.target.stop('pytm_target_1')
        #     terminal_print.assert_called_with('pytm_target_1 has been stopped')
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="FAIL")
        with patch('builtins.print') as terminal_print:
            self.target.stop('pytm_target_1')
            terminal_print.assert_called_with('pytm_target_1 A is in FAILED state')
        subprocess.run('crm res start pytm_target_1', shell=True)

    def test_check_name(self):
        assert self.target._check_name('sgfbfu_hf')
        assert self.target._check_name('a_1sss_')
        assert not self.target._check_name('_sgfbfuhf')
        assert not self.target._check_name('7_sgfbfuhf')
        assert not self.target._check_name('sgfb*f$uhf')
        assert not self.target._check_name('sssバージョン番号无语a')

    def test_check_iqn(self):
        assert self.target._check_iqn("iqn.9999-20.com.vmware.iscsi")
        assert self.target._check_iqn("iqn.0000-00.com.vmware.iscsi")
        assert self.target._check_iqn("iqn.2222-11.com.vmware:1")
        assert self.target._check_iqn("iqn.1998-01.com.vmware.iscsi:name1")
        assert self.target._check_iqn("iqn.2001-04.com.example:storage:diskarrays-sn-a86753091")
        assert self.target._check_iqn("iqn.2001-04.com.example.ddd-23-tt:storage.tape1.sys1.xyz")
        assert not self.target._check_iqn("iqnn.9999-20.com.vmware.iscsi")
        assert not self.target._check_iqn("iqn.999-20.com.vmware.iscsi")
        assert not self.target._check_iqn("iqn.9999-2.com.vmware.iscsi")
        assert not self.target._check_iqn("iqn.9999_20.com.vmware.iscsi")
        assert not self.target._check_iqn("iqn.0000_21.com.vmware.iscsi")
        assert not self.target._check_iqn("iqn.0000_21.com.vmware.Iscsi")
        assert not self.target._check_iqn("iqn.0000_21.com.vmware.iscsi:name_1")

    def test_check_status(self,mocker):
        #模拟返回的资源状态（实际环境比较难获取到各种不同状态）
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="Started")
        assert self.target._check_status("xx") is "OK"
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="Stopped")
        mocker.patch.object(crm.CRMConfig, 'get_failed_actions', return_value=True)
        assert self.target._check_status("xx") is "OTHER_ERROR"
        mocker.patch.object(crm.CRMConfig, 'get_failed_actions', return_value=False)
        assert self.target._check_status("xx") is "UNKNOWN_ERROR"
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="FAILED")
        assert self.target._check_status("xx") is "FAIL"

@pytest.mark.ilu
class TestLogicalUnit:
    def setup_class(self):
        subprocess.run('python3 vtel.py stor r c res_pylun -s 4m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py stor r c res_pylun1 -s 4m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py stor r c res_pylun2 -s 4m -a -num 1', shell=True)
        subprocess.run('python3 vtel.py stor r c res_pylun3 -s 4m -a -num 1', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi h c pylun_host1 iqn.2020-04.feixitek.com:pylun01', shell=True)
        subprocess.run('python3 vtel.py iscsi h c pylun_host2 iqn.2020-04.feixitek.com:pylun02', shell=True)
        subprocess.run('python3 vtel.py iscsi h c pylun_host3 iqn.2020-04.feixitek.com:pylun03', shell=True)
        subprocess.run('python3 vtel.py iscsi pt c pylun_portal_1 -ip 10.203.1.184', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi tg c pylun_target_1 -iqn iqn.2020-02.com.example:pyilu1 -portal pylun_portal_1', shell=True)
        time.sleep(3)
        self.ilu = iscsi.LogicalUnit()
        self.ilu.js.json_data = self.ilu.js.read_json()
        self.path = self.ilu.js.json_data['Disk']['res_pylun1']
        self.lunid = int(self.path[-4:]) - 1000
        create_ilu_cmd = f'crm conf primitive lun_res_pylun1 iSCSILogicalUnit params ' \
              f'target_iqn="iqn.2020-02.com.example:pyilu1" ' \
              f'implementation=lio-t ' \
              f'lun={self.lunid} ' \
              f'path={self.path} ' \
              f'allowed_initiators="iqn.2020-04.feixitek.com:pylun01" ' \
              f'op start timeout=40 interval=0 ' \
              f'op stop timeout=40 interval=0 ' \
              f'op monitor timeout=40 interval=15 ' \
              f'meta target-role=Stopped'
        subprocess.run(create_ilu_cmd, shell=True)
        subprocess.run('crm cof colocation col_lun_res_pylun1 inf: lun_res_pylun1 pylun_target_1', shell=True)
        subprocess.run('crm cof order or_lun_res_pylun1 pylun_target_1 lun_res_pylun1', shell=True)
        subprocess.run('crm res start lun_res_pylun1', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)

    def teardown_class(self):
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        subprocess.run('crm res stop lun_res_pylun1', shell=True)
        time.sleep(2)
        subprocess.run('crm conf del lun_res_pylun1', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py iscsi sync', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py stor r d res_pylun -y', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py stor r d res_pylun1 -y', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py stor r d res_pylun2 -y', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py stor r d res_pylun3 -y', shell=True)
        time.sleep(2)
        subprocess.run('python3 vtel.py iscsi d s', shell=True)
        time.sleep(1)
        subprocess.run('python3 vtel.py iscsi tg d pylun_target_1', shell=True)
        time.sleep(3)
        subprocess.run('python3 vtel.py iscsi pt d pylun_portal_1', shell=True)
        #手动删host
        # subprocess.run('python3 vtel.py iscsi h d pylun_host1', shell=True)
        # subprocess.run('python3 vtel.py iscsi h d pylun_host2', shell=True)
        # subprocess.run('python3 vtel.py iscsi h d pylun_host3', shell=True)

    def test__get_all_drbd_inuse(self):
        self.ilu.js.json_data = self.ilu.js.read_json()
        assert self.ilu._get_all_drbdInuse()

    def test_create(self, mocker):
        with patch('builtins.print') as terminal_print:
            self.ilu.create('pylun_target_1', 'disk_12kk', ['pylun_host1'])
            terminal_print.assert_called_with("Fail！Can't find disk_12kk")
        with patch('builtins.print') as terminal_print:
            self.ilu.create('pylun_target_1', 'res_pylun1', ['pylun_host1'])
            terminal_print.assert_called_with('The disk "res_pylun1" has been used')
        with patch('builtins.print') as terminal_print:
            self.ilu.create('pylun_target_110', 'res_pylun', ['pylun_host1'])
            terminal_print.assert_called_with("Fail！Can't find pylun_target_110")
        with patch('builtins.print') as terminal_print:
            self.ilu.create('pylun_target_1', 'res_pylun', ['pylun_host10010'])
            terminal_print.assert_called_with("Fail! Can't find pylun_host10010.Please give the true name.")
        with patch('builtins.print') as terminal_print:
            self.ilu.create('pylun_target_1', 'res_pylun', ['pylun_host2'])
            terminal_print.assert_called_with("Create lun_res_pylun successfully")
        self.ilu.js.json_data = self.ilu.js.read_json()
        mocker.patch.object(sundry, 'get_answer', return_value="yes")
        self.ilu.delete('lun_res_pylun')

    def test_modify(self):
        assert self.ilu.modify() is None

    def test_delete(self, mocker):
        self.ilu.create('pylun_target_1', 'res_pylun2', ['pylun_host2'])
        self.ilu.js.json_data = self.ilu.js.read_json()
        mocker.patch.object(sundry, 'get_answer', return_value="yes")
        with patch('builtins.print') as terminal_print:
            self.ilu.delete('lun_res_pylun2')
            terminal_print.assert_called_with("Delete lun_res_pylun2 successfully")
        with patch('builtins.print') as terminal_print:
            self.ilu.delete('lun_res_pylun2')
            terminal_print.assert_called_with("Fail！Can't find lun_res_pylun2")
        mocker.patch.object(sundry, 'get_answer', return_value="no")
        with pytest.raises(SystemExit) as exsinfo:
            self.ilu.delete('lun_res_pylun1')
        assert exsinfo.type == SystemExit

    def test_show(self):
        assert ['lun_res_pylun1', str(self.lunid),'pylun_target_1', self.path, 'iqn.2020-04.feixitek.com:pylun01(pylun_host1)', 'Started'] in self.ilu.show()

    def test_add(self, mocker):
        self.ilu.create('pylun_target_1', 'res_pylun3', ['pylun_host2'])
        self.ilu.js.json_data = self.ilu.js.read_json()
        with patch('builtins.print') as terminal_print:
            self.ilu.add("45lun_res_pylun3", ['pylun_host1'])
            terminal_print.assert_called_with("Fail！Can't find 45lun_res_pylun3")
        with patch('builtins.print') as terminal_print:
            self.ilu.add("lun_res_pylun3", ['pylun_host2'])
            terminal_print.assert_called_with('pylun_host2 is already on the "allowed initiators"')
        with patch('builtins.print') as terminal_print:
            self.ilu.add("lun_res_pylun3", ['45pylun_host2'])
            terminal_print.assert_called_with("Fail！Can't find 45pylun_host2")
        with patch('builtins.print') as terminal_print:
            self.ilu.add("lun_res_pylun3", ['pylun_host1'])
            terminal_print.assert_called_with("Modify the allowed initiators of lun_res_pylun3 successfully")
        mocker.patch.object(sundry, 'get_answer', return_value="yes")
        self.ilu.delete('lun_res_pylun3')
        time.sleep(2)
        self.ilu.js.json_data = self.ilu.js.read_json()

    def test_remove(self, mocker):
        self.ilu.create('pylun_target_1', 'res_pylun3', ['pylun_host1','pylun_host2'])
        time.sleep(1)
        self.ilu.js.json_data = self.ilu.js.read_json()
        with patch('builtins.print') as terminal_print:
            self.ilu.remove("45lun_res_pylun3", ['pylun_host1'])
            terminal_print.assert_called_with("Fail！Can't find 45lun_res_pylun3")
        with patch('builtins.print') as terminal_print:
            self.ilu.remove("lun_res_pylun3", ['45pylun_host1'])
            terminal_print.assert_called_with("Fail！Can't find 45pylun_host1")
        with patch('builtins.print') as terminal_print:
            self.ilu.remove("lun_res_pylun3", ['pylun_host3'])
            terminal_print.assert_called_with('pylun_host3 is not in the "allowed initiators"')
        with patch('builtins.print') as terminal_print:
            self.ilu.remove("lun_res_pylun3", ['pylun_host1','pylun_host2'])
            terminal_print.assert_called_with("Please keep at least one initiators")
        with patch('builtins.print') as terminal_print:
            self.ilu.remove("lun_res_pylun3", ['pylun_host1'])
            terminal_print.assert_called_with("Modify the allowed initiators of lun_res_pylun3 successfully")
        mocker.patch.object(sundry, 'get_answer', return_value="yes")
        self.ilu.delete('lun_res_pylun3')
        time.sleep(2)
        self.ilu.js.json_data = self.ilu.js.read_json()

    def test_start(self, mocker):
        self.ilu.create('pylun_target_1', 'res_pylun3', ['pylun_host2'])
        time.sleep(1)
        self.ilu.js.json_data = self.ilu.js.read_json()
        with patch('builtins.print') as terminal_print:
            self.ilu.start("45lun_res_pylun3")
            terminal_print.assert_called_with("45lun_res_pylun3 does not exist")
        with patch('builtins.print') as terminal_print:
            self.ilu.start("lun_res_pylun3")
            terminal_print.assert_called_with("lun_res_pylun3 is in STARTED state")
        subprocess.run('crm res stop lun_res_pylun3', shell=True)
        time.sleep(2)
        with patch('builtins.print') as terminal_print:
            self.ilu.start("lun_res_pylun3")
            terminal_print.assert_called_with("lun_res_pylun3 has been started")
        mocker.patch.object(sundry, 'get_answer', return_value="yes")
        self.ilu.delete('lun_res_pylun3')
        time.sleep(2)
        self.ilu.js.json_data = self.ilu.js.read_json()
        # 模拟FAILED状态
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="FAILED")
        with patch('builtins.print') as terminal_print:
            self.ilu.start("lun_res_pylun1")
            terminal_print.assert_called_with("lun_res_pylun1 A is in FAILED state")

    def test_stop(self, mocker):
        self.ilu.create('pylun_target_1', 'res_pylun3', ['pylun_host2'])
        time.sleep(1)
        self.ilu.js.json_data = self.ilu.js.read_json()
        with patch('builtins.print') as terminal_print:
            self.ilu.stop("45lun_res_pylun3")
            terminal_print.assert_called_with("45lun_res_pylun3 does not exist")
        with patch('builtins.print') as terminal_print:
            self.ilu.stop("lun_res_pylun3")
            terminal_print.assert_called_with("lun_res_pylun3 has been stopped")
        with patch('builtins.print') as terminal_print:
            self.ilu.stop("lun_res_pylun3")
            terminal_print.assert_called_with("lun_res_pylun3 has been stopped")
        mocker.patch.object(sundry, 'get_answer', return_value="yes")
        self.ilu.delete('lun_res_pylun3')
        time.sleep(2)
        self.ilu.js.json_data = self.ilu.js.read_json()
        # 模拟资源状态
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="FAILED")
        with patch('builtins.print') as terminal_print:
            self.ilu.stop("lun_res_pylun1")
            terminal_print.assert_called_with("lun_res_pylun1 A is in FAILED state")
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="Stopped")
        mocker.patch.object(sundry, 'get_answer', return_value="no")
        with pytest.raises(SystemExit) as exsinfo:
            self.ilu.stop("lun_res_pylun1")
        assert exsinfo.type == SystemExit

    def test__get_path(self):
        assert '/dev/drbd' in self.ilu._get_path("res_pylun1")

    def test__get_target_iqn(self):
        assert self.ilu._get_target_iqn('pylun_target_1') == 'iqn.2020-02.com.example:pyilu1'

    def test__get_initiator_iqns(self):
        assert self.ilu._get_initiator_iqns(['pylun_host1', 'pylun_host2']) == ['iqn.2020-04.feixitek.com:pylun01',
                                                                            'iqn.2020-04.feixitek.com:pylun02']

    def test__get_host_data_for_show(self):
        assert self.ilu._get_host_data_for_show(['iqn.2020-04.feixitek.com:pylun01']) == 'iqn.2020-04.feixitek.com:pylun01(pylun_host1)'

    def test__check_status(self, mocker):
        # 模拟返回的资源状态（实际环境比较难获取到各种不同状态）
        # mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="Started")
        assert self.ilu._check_status("lun_res_pylun1") is "OK"
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="Stopped")
        mocker.patch.object(crm.CRMConfig, 'get_failed_actions', return_value=True)
        assert self.ilu._check_status("lun_res_pylun1") is "OTHER_ERROR"
        mocker.patch.object(crm.CRMConfig, 'get_failed_actions', return_value=False)
        assert self.ilu._check_status("lun_res_pylun1") is "UNKNOWN_ERROR"
        mocker.patch.object(crm.CRMConfig, 'get_crm_res_status', return_value="FAILED")
        assert self.ilu._check_status("lun_res_pylun1") is "FAIL"