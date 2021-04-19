import pytest
import sys
import os
import time

try:
    import linstor
except ImportError:
    print('没有安装linstor环境')
    sys.exit(1)


from execute.linstor_api import LinstorAPI





class TestLinstorAPI:


    @pytest.mark.skip
    def test_parse_size_str(self):
        # 1048576KB == 1GB
        assert LinstorAPI().parse_size_str('1G') == 1048576

        # size不为字符串
        with pytest.raises(SystemExit) as attrex:
            LinstorAPI().parse_size_str('asdkjsad')
        assert attrex.type == SystemExit

        # size单位异常
        with pytest.raises(SystemExit) as attrex:
            LinstorAPI().parse_size_str('10SDLJ')
        assert attrex.type == SystemExit


    @pytest.mark.skip
    def test_get_replies_state(self):
        # 正常存储池
        msg = LinstorAPI().get_linstorapi().storage_pool_list(['vince2'], ['pool_a'])[0]
        assert LinstorAPI().get_replies_state(msg.storage_pools[0].reports) == 'Ok'


        # 存储池warining
        msg = LinstorAPI().get_linstorapi().storage_pool_list(['ubuntu'],['pool_b'])[0]
        for storpool in msg.storage_pools:
            assert LinstorAPI().get_replies_state(storpool.reports) == 'Warning'

    @pytest.mark.skip
    def test_get_volume_state(self):
        """
        环境：
        ╭───────────────────────────────────────────────────────────────────────────────────────────────────╮
        ┊ Node   ┊ Resource ┊ StoragePool ┊ VolNr ┊ MinorNr ┊ DeviceName    ┊ Allocated ┊ InUse  ┊    State ┊
        ╞═══════════════════════════════════════════════════════════════════════════════════════════════════╡
        ┊ ubuntu ┊ res_a    ┊ pool_a      ┊     0 ┊    1000 ┊ /dev/drbd1000 ┊    12 MiB ┊        ┊  Unknown ┊
        ┊ vince2 ┊ res_b    ┊ pool_a      ┊     0 ┊    1010 ┊ /dev/drbd1010 ┊    12 MiB ┊ Unused ┊ UpToDate ┊
        ╰───────────────────────────────────────────────────────────────────────────────────────────────────╯

        """
        msg = LinstorAPI().get_linstorapi().volume_list(['ubuntu'],['pool_a'],['res_a'])[0]
        rsc_state_lkup = {x.node_name + x.name: x for x in msg.resource_states}
        for rsc in msg.resources:
            rsc_state = rsc_state_lkup.get(rsc.node_name + rsc.name)
            for vlm in rsc.volumes:
                # 正确的VolNr
                assert LinstorAPI().get_volume_state(rsc_state.volume_states,vlm.number)._rest_data is rsc_state.volume_states[0]._rest_data
                # 错误的VolNr
                assert LinstorAPI().get_volume_state(rsc_state.volume_states,1) is None

    @pytest.mark.skip
    def test_get_linstorapi(self):
        # 正常情况下
        assert LinstorAPI().get_linstorapi() is not None

        # 关闭linstor连接
        os.system('systemctl stop linstor-controller')
        time.sleep(2)

        # linstor未连接的情况下
        with pytest.raises(linstor.LinstorNetworkError) as neterr:
            LinstorAPI().get_linstorapi()
        assert neterr.type == linstor.LinstorNetworkError


        # 重连linstor服务
        os.system('systemctl restart linstor-controller')
        time.sleep(5)

    @pytest.mark.skip
    def test_get_node(self):
        """
        环境
        ╭────────────────────────────────────────────────────────╮
        ┊ Node   ┊ NodeType ┊ Addresses                 ┊ State  ┊
        ╞════════════════════════════════════════════════════════╡
        ┊ ubuntu ┊ COMBINED ┊ 10.203.1.155:3366 (PLAIN) ┊ Online ┊
        ┊ vince2 ┊ COMBINED ┊ 10.203.1.157:3366 (PLAIN) ┊ Online ┊
        ╰────────────────────────────────────────────────────────╯
        """
        # 正常环境下，生成环境数据
        data1 = [{'Node': 'ubuntu', 'NodeType': 'COMBINED', 'Addresses': '10.203.1.155:3366 (PLAIN)', 'State': 'ONLINE'}, {'Node': 'vince2', 'NodeType': 'COMBINED', 'Addresses': '10.203.1.157:3366 (PLAIN)', 'State': 'ONLINE'}]
        data2 = [{'Node': 'ubuntu', 'NodeType': 'COMBINED', 'Addresses': '10.203.1.155:3366 (PLAIN)', 'State': 'ONLINE'}]
        # 获取全部node数据
        assert LinstorAPI().get_node() == data1

        # 获取指定node数据
        assert LinstorAPI().get_node(['ubuntu']) == data2


        # linstor未连接的情况下
        # with pytest.raises(linstor.LinstorNetworkError) as neterr:
        #     LinstorAPI().get_node()
        # assert neterr.type == linstor.LinstorNetworkError



    def test_get_storagepool(self):
        """
        环境
        ╭───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
        ┊ StoragePool          ┊ Node   ┊ Driver   ┊ PoolName ┊ FreeCapacity ┊ TotalCapacity ┊ CanSnapshots ┊ State ┊
        ╞═══════════════════════════════════════════════════════════════════════════════════════════════════════════╡
        ┊ DfltDisklessStorPool ┊ ubuntu ┊ DISKLESS ┊          ┊              ┊               ┊ False        ┊ Ok    ┊
        ┊ DfltDisklessStorPool ┊ vince2 ┊ DISKLESS ┊          ┊              ┊               ┊ False        ┊ Ok    ┊
        ┊ pool_a               ┊ ubuntu ┊ LVM      ┊          ┊    15.98 GiB ┊     16.00 GiB ┊ False        ┊ Ok    ┊
        ┊ pool_a               ┊ vince2 ┊ LVM      ┊          ┊    14.92 GiB ┊     16.00 GiB ┊ False        ┊ Ok    ┊
        ┊ pool_b               ┊ ubuntu ┊ LVM      ┊          ┊    15.98 GiB ┊     16.00 GiB ┊ False        ┊ Ok    ┊
        ┊ pool_sdc             ┊ ubuntu ┊ LVM      ┊          ┊    15.00 GiB ┊     15.00 GiB ┊ False        ┊ Ok    ┊
        ╰───────────────────────────────────────────────────────────────────────────────────────────────────────────╯
        """

        # 该环境下对应的数据
        data1 = [{'StoragePool': 'DfltDisklessStorPool', 'Node': 'ubuntu', 'Driver': 'DISKLESS', 'PoolName': '', 'FreeCapacity': '', 'TotalCapacity': '', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'DfltDisklessStorPool', 'Node': 'vince2', 'Driver': 'DISKLESS', 'PoolName': '', 'FreeCapacity': '', 'TotalCapacity': '', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'pool_a', 'Node': 'ubuntu', 'Driver': 'LVM', 'PoolName': 'drbdpool', 'FreeCapacity': '15.98 GiB', 'TotalCapacity': '16.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'pool_a', 'Node': 'vince2', 'Driver': 'LVM', 'PoolName': 'drbdpool', 'FreeCapacity': '14.92 GiB', 'TotalCapacity': '16.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'pool_b', 'Node': 'ubuntu', 'Driver': 'LVM', 'PoolName': 'drbdpool', 'FreeCapacity': '15.98 GiB', 'TotalCapacity': '16.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'pool_sdc', 'Node': 'ubuntu', 'Driver': 'LVM', 'PoolName': 'vgsdc', 'FreeCapacity': '15.00 GiB', 'TotalCapacity': '15.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}]
        data2 = [{'StoragePool': 'pool_a', 'Node': 'ubuntu', 'Driver': 'LVM', 'PoolName': 'drbdpool', 'FreeCapacity': '15.98 GiB', 'TotalCapacity': '16.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}]
        # 获取全部数据
        assert LinstorAPI().get_storagepool() == data1

        # 获取特定数据
        assert LinstorAPI().get_storagepool(['ubuntu'],['pool_a']) == data2



    def test_get_resource(self,):
        """
        环境
        ╭───────────────────────────────────────────────────────────────────────────────────────────────────╮
        ┊ Node   ┊ Resource ┊ StoragePool ┊ VolNr ┊ MinorNr ┊ DeviceName    ┊ Allocated ┊ InUse  ┊    State ┊
        ╞═══════════════════════════════════════════════════════════════════════════════════════════════════╡
        ┊ ubuntu ┊ res_a    ┊ pool_a      ┊     0 ┊    1000 ┊ /dev/drbd1000 ┊    12 MiB ┊ Unused ┊ UpToDate ┊
        ┊ vince2 ┊ res_b    ┊ pool_a      ┊     0 ┊    1010 ┊ /dev/drbd1010 ┊    12 MiB ┊ Unused ┊ UpToDate ┊
        ╰───────────────────────────────────────────────────────────────────────────────────────────────────╯
        """
        # 该环境下对应的数据
        data1 = [{'Node': 'ubuntu', 'Resource': 'res_a', 'StoragePool': 'pool_a', 'VolNr': '0', 'MinorNr': '1000', 'DeviceName': '/dev/drbd1000', 'Allocated': '12 MiB', 'InUse': 'Unused', 'State': 'UpToDate'}, {'Node': 'vince2', 'Resource': 'res_b', 'StoragePool': 'pool_a', 'VolNr': '0', 'MinorNr': '1010', 'DeviceName': '/dev/drbd1010', 'Allocated': '12 MiB', 'InUse': 'Unused', 'State': 'UpToDate'}]
        data2 = [{'Node': 'ubuntu', 'Resource': 'res_a', 'StoragePool': 'pool_a', 'VolNr': '0', 'MinorNr': '1000', 'DeviceName': '/dev/drbd1000', 'Allocated': '12 MiB', 'InUse': 'Unused', 'State': 'UpToDate'}]


        # 获取全部数据
        assert LinstorAPI().get_resource() == data1
        # 获取特定数据
        assert LinstorAPI().get_resource(['ubuntu'],['pool_a'],['res_a'])













