import gevent
from gevent import monkey

# 协程相关的补丁
monkey.patch_time()


from execute import LinstorAPI


class Scheduler():
    """
    多协程调度linstor、crm模块
    """

    def __init__(self):
        pass



    def get_linstor_data(self):
        node_data = gevent.spawn(LinstorAPI().get_node)
        res_data = gevent.spawn(LinstorAPI().get_resource)
        sp_data = gevent.spawn(LinstorAPI().get_storagepool)
        gevent.joinall([node_data,res_data,sp_data])

        return {'node_data':node_data.value,'res_data':res_data.value,'sp_data':sp_data.value}


        # return ({'node_data': [{'Node': 'ubuntu', 'NodeType': 'COMBINED', 'Addresses': '10.203.1.155:3366 (PLAIN)', 'State': 'ONLINE'}, {'Node': 'vince2', 'NodeType': 'COMBINED', 'Addresses': '10.203.1.157:3366 (PLAIN)', 'State': 'ONLINE'}], 'res_data': [{'Node': 'ubuntu', 'Resource': 'res_a', 'StoragePool': 'pool_a', 'VolNr': '0', 'MinorNr': '1000', 'DeviceName': '/dev/drbd1000', 'Allocated': '12 MiB', 'InUse': 'Unused', 'State': 'UpToDate'}], 'sp_data': [{'StoragePool': 'DfltDisklessStorPool', 'Node': 'DfltDisklessStorPool', 'Driver': 'DISKLESS', 'PoolName': '', 'FreeCapacity': '', 'TotalCapacity': '', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'DfltDisklessStorPool', 'Node': 'DfltDisklessStorPool', 'Driver': 'DISKLESS', 'PoolName': '', 'FreeCapacity': '', 'TotalCapacity': '', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'pool_a', 'Node': 'pool_a', 'Driver': 'LVM', 'PoolName': 'drbdpool', 'FreeCapacity': '15.98 GiB', 'TotalCapacity': '16.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'pool_a', 'Node': 'pool_a', 'Driver': 'LVM', 'PoolName': 'drbdpool', 'FreeCapacity': '14.92 GiB', 'TotalCapacity': '16.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'pool_b', 'Node': 'pool_b', 'Driver': 'LVM', 'PoolName': 'drbdpool', 'FreeCapacity': '15.97 GiB', 'TotalCapacity': '16.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}, {'StoragePool': 'pool_sdc', 'Node': 'pool_sdc', 'Driver': 'LVM', 'PoolName': 'vgsdc', 'FreeCapacity': '15.00 GiB', 'TotalCapacity': '15.00 GiB', 'CanSnapshots': False, 'State': 'Ok'}]})



    def create_mul_conn(self):
        pass



    def create_rd(self):
        pass
