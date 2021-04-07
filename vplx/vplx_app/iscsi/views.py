# coding:utf-8

from flask import views
from vplx_app.iscsi import iscsi_blueprint
from vplx_app.iscsi import model
'''
@author: paul
@note: 路由,该路由会去调用model中的类，类名在view_fun中设置，和model类名需同步,as_view 值设定是唯一的
@bug: 未做路由参数处理，后续待优化
'''



'''
@note: iSCSI创建资源路由
'''
iscsi_blueprint.add_url_rule('/host/create', view_func=model.HostCreate.as_view('host_create'))
iscsi_blueprint.add_url_rule('/hg/create', view_func=model.HostGroupCreate.as_view('hostgroup_create'))
iscsi_blueprint.add_url_rule('/dg/create', view_func=model.DiskGroupCreate.as_view('diskgroup_create'))
iscsi_blueprint.add_url_rule('/map/create', view_func=model.MapCreate.as_view('map_create'))

'''
@note: iSCSI操作/数据
'''
iscsi_blueprint.add_url_rule('/host/show/oprt', view_func=model.OprtAllHost.as_view('oprt_all_host'))
iscsi_blueprint.add_url_rule('/host/show/data', view_func=model.AllHostResult.as_view('all_host_result'))
iscsi_blueprint.add_url_rule('/disk/show/oprt', view_func=model.OprtAllDisk.as_view('oprt_all_disk'))
iscsi_blueprint.add_url_rule('/disk/show/data', view_func=model.AllDiskResult.as_view('all_disk_result'))
iscsi_blueprint.add_url_rule('/hg/show/oprt', view_func=model.OprtAllHg.as_view('oprt_all_hg'))
iscsi_blueprint.add_url_rule('/hg/show/data', view_func=model.AllHgResult.as_view('all_hg_result'))
iscsi_blueprint.add_url_rule('/dg/show/oprt', view_func=model.OprtAllDg.as_view('oprt_all_dg'))
iscsi_blueprint.add_url_rule('/dg/show/data', view_func=model.AllDgResult.as_view('all_dg_result'))
iscsi_blueprint.add_url_rule('/map/show/oprt', view_func=model.OprtAllMap.as_view('oprt_all_map'))
iscsi_blueprint.add_url_rule('/map/show/data', view_func=model.AllMapResult.as_view('all_map_result'))



'''
@note: iSCSI操作/修改
'''
iscsi_blueprint.add_url_rule('/host/modify/check', view_func=model.CheckHostModify.as_view('host_modify_check'))
iscsi_blueprint.add_url_rule('/host/modify', view_func=model.HostModify.as_view('host_modify'))
iscsi_blueprint.add_url_rule('/hg/modify/check', view_func=model.CheckHgModify.as_view('hg_modify_check'))
iscsi_blueprint.add_url_rule('/hg/modify', view_func=model.HgModify.as_view('hg_modify'))
iscsi_blueprint.add_url_rule('/dg/modify/check', view_func=model.CheckDgModify.as_view('dg_modify_check'))
iscsi_blueprint.add_url_rule('/dg/modify', view_func=model.DgModify.as_view('dg_modify'))
iscsi_blueprint.add_url_rule('/map/modify/check', view_func=model.CheckMapModify.as_view('map_modify_check'))
iscsi_blueprint.add_url_rule('/map/modify', view_func=model.MapModify.as_view('map_modify'))

'''
@note: iSCSI 操作/删除
'''
iscsi_blueprint.add_url_rule('/all/delete/check', view_func=model.CheckAllDelete.as_view('all_delete_check'))
iscsi_blueprint.add_url_rule('/all/delete', view_func=model.AllDelete.as_view('all_delete'))
# iscsi_blueprint.add_url_rule('/hg/delete/check', view_func=model.CheckHgDelete.as_view('hg_delete_check'))
# iscsi_blueprint.add_url_rule('/hg/delete', view_func=model.HgDelete.as_view('hg_delete'))
# iscsi_blueprint.add_url_rule('/dg/delete/check', view_func=model.CheckDgDelete.as_view('dg_delete_check'))
# iscsi_blueprint.add_url_rule('/dg/delete', view_func=model.DgDelete.as_view('dg_delete'))
# iscsi_blueprint.add_url_rule('/map/delete/check', view_func=model.CheckMapDelete.as_view('map_delete_check'))
# iscsi_blueprint.add_url_rule('/map/delete', view_func=model.MapDelete.as_view('map_delete'))


