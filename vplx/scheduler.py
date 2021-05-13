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
        linstor_api = LinstorAPI()
        node_data = gevent.spawn(linstor_api.get_node)
        res_data = gevent.spawn(linstor_api.get_resource)
        sp_data = gevent.spawn(linstor_api.get_storagepool)
        gevent.joinall([node_data,res_data,sp_data])

        return {'node_data':node_data.value,'res_data':res_data.value,'sp_data':sp_data.value}


    def create_mul_conn(self):
        pass



    def create_rd(self):
        pass
