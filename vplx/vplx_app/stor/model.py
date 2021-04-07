# coding:utf-8
'''
Created on 2020/3/2
@author: Paul
@note: data
'''

from flask import Flask, jsonify, render_template, request, make_response, views
import process
from public import log
from execute import stor 


def cors_data(datadict):
    response = make_response(jsonify(datadict))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,HEAD,GET,POST'
    response.headers['Access-Control-Allow-Headers'] = 'x-requested-with'
    return response
 
 
def get_request_data():
    if request.method == 'GET':
        str_data = request.args.items()
        dict_data = dict(str_data)
        tid = dict_data['tid']
        # 记录除了tid之后接收到的数据
        logger = log.Log()
        logger.tid = tid
        return dict_data


RESOURCEDICT = None
def get_all_resource():
    global RESOURCEDICT
    pc = process.Process_data()
    RESOURCEDICT = pc.process_data_resource()
    return True


class OprtResource(views.MethodView):  

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('OPRT', 'ROUTE', '/resource/show/oprt', dict_data['ip'], '')
        if get_all_resource():
            logger.write_to_log('DATA', 'RETURN', 'OprtResource', 'result', '0')
            return cors_data("0")
        else:
            logger.write_to_log('DATA', 'RETURN', 'OprtResource', 'result', '1')
            return cors_data("1")


class ResourceResult(views.MethodView):  

    def get(self):
#         get_request_data()
#         logger = log.Log()
#         logger.write_to_log('DATA', 'ROUTE', '/resource/show/data', dict_data['ip'], '')
        if not RESOURCEDICT:
            get_all_resource()
#         logger.write_to_log('DATA', 'RETURN', 'ResourceResult', 'result', RESOURCEDICT)
        return cors_data(RESOURCEDICT)


NODEDICT = None
def get_all_node():
    global NODEDICT
    pc = process.Process_data()
    NODEDICT = pc.process_data_node()
    return True


class OprtNode(views.MethodView):  

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('OPRT', 'ROUTE', '/resource/show/oprt', dict_data['ip'], '')
        if get_all_node():
            logger.write_to_log('DATA', 'RETURN', 'OprtResource', 'result', '0')
            return cors_data("0")
        else:
            logger.write_to_log('DATA', 'RETURN', 'OprtResource', 'result', '1')
            return cors_data("1")


class NodeResult(views.MethodView):  

    def get(self):
#         get_request_data()
#         logger = consts.glo_log()
#         logger.write_to_log('DATA', 'ROUTE', '/resource/show/data', dict_data['ip'], '')
        if not NODEDICT:
            get_all_node()
#         logger.write_to_log('DATA', 'RETURN', 'ResourceResult', 'result', RESOURCEDICT)
        return cors_data(NODEDICT)
    
 
STORAGEPOOL = None

def get_all_storagepool():
    global STORAGEPOOL
    pc = process.Process_data()
    STORAGEPOOL = pc.process_data_stp()
    return True


class OprtStoragepool(views.MethodView):  

    def get(self):
        dict_data = get_request_data()
        logger = log.Log()
        logger.write_to_log('OPRT', 'ROUTE', '/storagepool/show/oprt', dict_data['ip'], '')
        if get_all_storagepool():
            logger.write_to_log('DATA', 'RETURN', 'OprtStoragepool', 'result', '0')
            return cors_data("0")
        else:
            logger.write_to_log('DATA', 'RETURN', 'OprtStoragepool', 'result', '1')
            return cors_data("1")


class StoragepoolResult(views.MethodView):  

    def get(self):
#         get_request_data()
#         logger = consts.glo_log()
#         logger.write_to_log('DATA', 'ROUTE', '/resource/show/data', dict_data['ip'], '')
        if not STORAGEPOOL:
            get_all_storagepool()
#         logger.write_to_log('DATA', 'RETURN', 'ResourceResult', 'result', RESOURCEDICT)
        return cors_data(STORAGEPOOL)

'''
@note: 删除model
'''


class ResourceD(views.MethodView):  

    def get(self):
        data = get_request_data()
        print(data)
        ResourceD_data = data["resource_data"]
        print(ResourceD_data)
        message = "删除成功"
        return cors_data(message)

     
class NodeD(views.MethodView):  

    def get(self):
        data = get_request_data()
        return

     
class StoragepoolD(views.MethodView):  

    def get(self):
        data = get_request_data()
     
        return 

'''
@note: 创建资源
'''


class SpCreate(views.MethodView):

    def get(self):
        data = get_request_data()
        sp_result = {}
        tid = data['tid']
        sp = eval(data['storagepool'])
        obj_sp = stor.StoragePool()
        if sp['type'] == 'lvm':
            print("22")
            sp_result = obj_sp.create_storagepool_lvm(sp['node_name'],sp['sp_name'],sp['volume'])
        elif sp['type'] == 'tlv':
            print("111")
            sp_result = obj_sp.create_storagepool_thinlv(sp['node_name'],sp['sp_name'],sp['volume'])
        return cors_data(sp_result)


class NodeCreate(views.MethodView):

    def get(self):
        data = get_request_data()
        print(data)
        tid = data['tid']
        node = eval(data['node'])
        obj_node = stor.Node()
        result = obj_node.create_node(node['node_name'],node['ip'],node['type'])
        return cors_data(result)
    
    
class ResourceCreate(views.MethodView):

    def get(self):
        print("----------------------")
        data = get_request_data()
        res_data = eval(data['resource'])
        print(data)
        type = data['type']
        res = res_data['res_name']
        # tid = data['tid']
        obj_res = stor.Resource()
        if type == 'normal_create':
            node = eval(data['node'])
            sp = eval(data['sp'])
            size = res_data['size'] + res_data['size_unit']
            result = obj_res.create_res_manual(res,size,node,sp)
        elif type == 'auto_create':
            print('auto_crete')
            size = res_data['size'] + res_data['size_unit']
            num = res_data['node_num']
            result = obj_res.create_res_auto(res,size,num)
        elif type == 'normal_add_mirror':
            node = eval(data['node'])
            sp = eval(data['sp'])
            result = obj_res.add_mirror_manual(res,node,sp)
        elif type == 'auto_add_mirror':
            # res, node, sp)
            num = res_data['node_num']
            result = obj_res.add_mirror_auto(res,num)
        elif type == 'diskless':
            node = res_data['node']
            result = obj_res.create_res_diskless(node,res)
        else:
            result = ''
#         obj_node.create_node()
        return cors_data(result)


'''
@note: 交互
'''
lvm = None
sp = None
node_create = None
node_num = None

class LINSTORView(views.MethodView):
    

    def get(self):
        global lvm
        global sp
        global node_create
        global node_num
        pc = process.Process_data()
        lvm = pc.get_option_lvm()
        sp = pc.get_option_sp()
        node_create = pc.get_option_node()
        
        print(node_create)
        node_num = pc.get_option_nodenum()
        return cors_data("success")



class lvmView(views.MethodView):
    def get(self):
        return cors_data(lvm)

sp2 = {'code': 0, 'msg': '', 'count': 1000, 
'data':
 [{'name': 'ubuntu', 'children': [{'name': 'DfltDisklessStorPool', 'node_name': 'ubuntu', 'value': 1,'parentId':1},
                                   {'name': 'pytest_sp1', 'node_name': 'ubuntu', 'value': 2,'parentId':1}]},
{'name': '1111', 'children': [{'name': 'DfltDisklessStorPool22', 'node_name': '1111', 'value': 3,'parentId':2},
                                   {'name': 'pytest_sp1222', 'node_name': '1111', 'value': 4,'parentId':2}]}]}

class spView(views.MethodView):  
    def get(self):
        print(sp)
        return cors_data(sp)
#         return cors_data(sp2)

    
    
class nodecreateView(views.MethodView):  

    def get(self):
        return cors_data(node_create)


class nodenumView(views.MethodView):  

    def get(self):
        return cors_data(node_num)

'''
@note: 修改model
'''

 
class LINSTORModify(views.MethodView):  

    def get(self):
        data = get_request_data()
        print(data)
        ResourceM_data = data["resource_data"]
        print(ResourceM_data)
        message = "修改成功"
        return cors_data(message)
