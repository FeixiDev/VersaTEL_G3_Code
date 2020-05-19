# coding:utf-8
import argparse
import sys
import re
import pickle
from functools import wraps
import execute_sys_command as esc
import argparse_init as ai
import linstordb
import iscsi_json as ij
import sundry
import log

_logger = log.Log()
_collector = log.Collector()



def comfirm_del(type):
    """
    Decorator providing confirmation of deletion function.
    :param func: Function to delete linstor resource
    """
    def decorate(func):
        @wraps(func)
        def wrapper(*args):
            cli_args = args[0]
            if cli_args.yes:
                func(*args)
            else:
                print('Are you sure you want to delete this %s? If yes, enter \'y/yes\''%type)
                answer = input()
                if answer in ['y', 'yes']:
                    func(*args)
                else:
                    print('Delete canceled')
        return wrapper
    return decorate


# 多节点创建resource时，storapoo多于node的异常类
class NodeLessThanSPError(Exception):
    pass


class InvalidSizeError(Exception):
    pass


class Vtel():
    """
    Analysis and judgment of parsers vtel, stor, iscsi
    """
    def __init__(self):
        self.cmd = ai.Commands()
        self.vtel = self.cmd.vtel
        self.args = self.vtel.parse_args()

    def vtel_judge(self):
        if self.args.subargs_vtel == 'stor':
            stor = Stor(self.args,self.cmd)
            stor.parse()
        elif self.args.subargs_vtel == 'iscsi':
            iscsi = Iscsi(self.args,self.cmd)
            iscsi.parse()
        else:
            self.vtel.print_help()


class Stor():
    """
    Analysis of subcommand stor and judgment of parameters.
    """
    def __init__(self,args,cmd):
        self.args = args
        self.cmd = cmd

    def node(self):
        # 对输入参数的判断（node的下一个参数）
        args = self.args
        parser = self.cmd

        if args.subargs_node in ['create', 'c']:
            Node.create(args, parser)
        elif args.subargs_node in ['modify', 'm']:
            Node.modify(args)
        elif args.subargs_node in ['delete', 'd']:
            Node.delete(args)
        elif args.subargs_node in ['show', 's']:
            Node.node_show(args)
        else:
            self.cmd.node.print_help()

    def resource(self):
        args = self.args
        parser = self.cmd

        if args.subargs_res in ['create', 'c']:
            Res.create(args,parser)
        elif args.subargs_res in ['modify', 'm']:
            Res.modify(args)
        elif args.subargs_res in ['delete', 'd']:
            Res.delete(args)
        elif args.subargs_res in ['show', 's']:
            Res.show(args)
        else:
            self.cmd.resource.print_help()

    def storagepool(self):
        args = self.args
        parser = self.cmd
        if args.subargs_sp in ['create', 'c']:
            SP.create(args,parser)
        elif args.subargs_sp in ['modify', 'm']:
            SP.modify()
        elif args.subargs_sp in ['delete', 'd']:
            SP.delete(args)
        elif args.subargs_sp in ['show', 's']:
            SP.show(args)
        else:
            self.cmd.storagepool.print_help()

    def parse(self):
        args = self.args
        if args.subargs_vtel == 'stor':
            if args.subargs_stor in ['node', 'n']:
                self.node()
            elif args.subargs_stor in ['resource', 'r']:
                self.resource()
            elif args.subargs_stor in ['storagepool', 'sp']:
                self.storagepool()
            elif args.subargs_stor in ['snap', 'sn']:
                pass

            elif args.gui:
                db = linstordb.LINSTORDB()
                data = pickle.dumps(db.data_base_dump)
                sundry.send_via_socket(data)
            else:
                self.cmd.stor.print_help()


class Node():
    @classmethod
    def create(cls,args,parser):
        parser_create = parser.node_create
        if args.gui:
            data = pickle.dumps(esc.stor.create_node(args.node, args.ip, args.nodetype))
            sundry.socket_send_result(data)

        elif args.node and args.nodetype and args.ip:
            esc.stor.create_node(args.node, args.ip, args.nodetype)
        else:
            parser_create.print_help()

    @classmethod
    def modify(cls,args):
        pass


    @staticmethod
    @comfirm_del
    def delete(args):
        esc.stor.delete_node(args.node)


    @classmethod
    def node_show(cls,args):
        tb = linstordb.OutputData()
        if args.nocolor:
            tb.show_node_one(args.node) if args.node else tb.node_all()
        else:
            tb.show_node_one_color(args.node) if args.node else tb.node_all_color()


#resource
class Res():
    # 指定node和storagepool数量的规范判断，符合则继续执行
    @staticmethod
    def is_args_correct(node,storagepool):
        if len(node) < len(storagepool):
            raise NodeLessThanSPError('指定的storagepool数量应少于node数量')

    @staticmethod
    def is_vail_size(size):
        re_size = re.compile('^[1-9][0-9]*([KkMmGgTtPpB](iB|B)?)$')
        if not re_size.match(size):
            raise InvalidSizeError('Invalid Size')


    @classmethod
    def create(cls,args,parser):
        """
        Create a LINSTOR resource. There are three types of creation based on different parameters:
        Automatically create resource,
        Create resources by specifying nodes and storage pools,
        create diskless resource,
        add mirror on other nodes

        :param args: Namespace that has been parsed for CLI
        :param parser: The instantiated object of Commands, used to call the parser in the Commands class.

        """
        #Create a resource parser for printing help instructions
        parser_create = parser.res_create

        """对应创建模式必需输入的参数和禁止输入的参数"""
        # Parameters required for automatic resource creation
        list_auto_required = [args.auto, args.num]
        # Automatically create input parameters for resource prohibition
        list_auto_forbid = [args.node, args.storagepool, args.diskless,args.add_mirror]
        #Specify the node and storage pool to create resources require input parameters
        list_manual_required = [args.node, args.storagepool]
        #Specify the input parameters for node and storage pool creation resource prohibition
        list_manual_forbid = [args.auto, args.num, args.diskless,args.add_mirror]
        #Create diskless resource prohibited input parameters
        list_diskless_forbid = [args.auto, args.num, args.storagepool,args.add_mirror]

        if args.size:
            #judge size
            try:
                cls.is_vail_size(args.size)
                cls.is_vail_size(args.size)
            except InvalidSizeError:
                print('%s is not a valid size!' % args.size)
                sys.exit(0)
            #自动创建条件判断，符合则执行
            if all(list_auto_required) and not any(list_auto_forbid):
                _logger.InputLogger.debug('create resource')
                esc.stor.create_res_auto(args.resource, args.size, args.num)
            #手动创建条件判断，符合则执行
            elif all(list_manual_required) and not any(list_manual_forbid):
                try:
                    cls.is_args_correct(args.node,args.storagepool)
                    esc.stor.create_res_manual(args.resource, args.size, args.node, args.storagepool)
                except NodeLessThanSPError:
                    print('The number of nodes does not meet the requirements')
                    sys.exit(0)
            else:
                parser_create.print_help()


        elif args.diskless:
            # 创建resource的diskless资源条件判断，符合则执行
            if args.node and not any(list_diskless_forbid):
                esc.stor.create_res_diskless(args.node, args.resource)
            else:
                parser_create.print_help()

        elif args.add_mirror:
            #手动添加mirror条件判断，符合则执行
            if all([args.node,args.storagepool]) and not any([args.auto, args.num]):
                if Res.is_args_correct():
                    esc.stor.add_mirror_manual(args.resource,args.node,args.storagepool)
                else:
                    parser_create.print_help()
            #自动添加mirror条件判断，符合则执行
            elif all([args.auto,args.num]) and not any([args.node,args.storagepool]):
                esc.stor.add_mirror_auto(args.resource,args.num)
            else:
                parser_create.print_help()

        else:
            parser_create.print_help()

    # resource修改功能，未开发
    @classmethod
    def modify(cls,args):
        pass


    # resource删除判断
    @staticmethod
    @comfirm_del
    def delete(args):
        if args.node:
            esc.stor.delete_resource_des(args.node, args.resource)
        elif not args.node:
            esc.stor.delete_resource_all(args.resource)


    @classmethod
    def show(cls,args):
        tb = linstordb.OutputData()
        if args.nocolor:
            tb.show_res_one(args.resource) if args.resource else tb.res_all()
        else:
            if args.resource:
                #%(asctime)s - [%(username)s] - [%(type)s] - [%(describe1)s] - [%(describe2)s] - [%(cmd)s]
                _logger.InputLogger.debug('resource show', extra={'username': _collector.get_username(),'type':'usercli','describe1':'','describe2':'','cmd':'stor r s'})
                tb.show_res_one_color(args.resource)
            else:
                _logger.InputLogger.debug('resource show', extra={'username': _collector.get_username()})
                tb.res_all_color()


#storage pool
class SP():
    def __init__(self):
        pass

    @classmethod
    def create(cls,args,parser):
        parser_create = parser.sp_create

        if args.storagepool and args.node:
            if args.lvm:
                if args.gui:
                    data = pickle.dumps(esc.stor.create_storagepool_lvm(args.node, args.storagepool, args.lvm))
                    sundry.send_via_socket(data)
                else:
                    esc.stor.create_storagepool_lvm(args.node, args.storagepool, args.lvm)
            elif args.tlv:
                if args.gui:
                    data = pickle.dumps(esc.stor.create_storagepool_thinlv(args.node, args.storagepool, args.tlv))
                    sundry.send_via_socket(data)
                else:
                    esc.stor.create_storagepool_thinlv(args.node, args.storagepool, args.tlv)
            else:
                parser_create.print_help()
        else:
            parser_create.print_help()

    @classmethod
    def modify(cls):
        pass

    @staticmethod
    @comfirm_del('storagepool')
    def delete(args):
        esc.stor.delete_storagepool(args.node, args.storagepool)


    @classmethod
    def show(cls,args):
        tb = linstordb.OutputData()
        if args.nocolor:
            tb.show_sp_one(args.storagepool) if args.storagepool else tb.sp_all()
        else:
            tb.show_sp_one_color(args.storagepool) if args.storagepool else tb.sp_all_color()


class Snap():
    def __init__(self):
        pass

    def snap_create(self):
        pass

    def snap_delete(self):
        pass


class Iscsi():
    def __init__(self, args, cmd):
        self.args = args
        self.cmd = cmd

    # iscsi 总命令判断
    def parse(self):
        js = ij.JSON_OPERATION()
        args = self.args
        if args.iscsi in ['host', 'h']:
            self.host(args, js)
        elif args.iscsi in ['disk', 'd']:
            self.disk(args, js)
        elif args.iscsi in ['hostgroup', 'hg']:
            self.hostgroup(args, js)
        elif args.iscsi in ['diskgroup', 'dg']:
            self.diskgroup(args, js)
        elif args.iscsi in ['map', 'm']:
            self.map(args, js)
        elif args.iscsi in ['show', 's']:
            self.show(args, js)
        else:
            print("iscsi (choose from 'host', 'disk', 'hg', 'dg', 'map')")
            self.cmd.iscsi.print_help()

    # iscsi host
    def host(self, args, js):
        # host判断
        if args.host in ['create', 'c']:
            if args.gui == 'gui':
                data = pickle.dumps(Host.host_create(args, js))
                sundry.send_via_socket(data)
            else:
                Host.host_create(args, js)
        elif args.host in ['show', 's']:
            Host.host_show(args, js)
        elif args.host in ['delete', 'd']:
            Host.host_delete(args, js)
        else:
            print("iscsi host (choose from 'create', 'show', 'delete')")
            self.cmd.host.print_help()

    # iscsi disk
    def disk(self, args, js):
        # disk判断
        if args.disk in ['show', 's']:
            Disk.disk_show(args, js)
        else:
            print("iscsi disk (choose from 'show')")
            self.cmd.disk.print_help()

    # iscsi hostgroup
    def hostgroup(self, args, js):
        # hostgroup判断
        if args.hostgroup in ['create', 'c']:
            if args.gui == 'gui':
                data = pickle.dumps(Hostgroup.hostgroup_create(args, js))
                sundry.send_via_socket(data)
            else:
                Hostgroup.hostgroup_create(args, js)
        elif args.hostgroup in ['show', 's']:
            Hostgroup.hostgroup_show(args, js)
        elif args.hostgroup in ['delete', 'd']:
            Hostgroup.hostgroup_delete(args, js)
        else:
            print("iscsi hostgroup (choose from 'create', 'show', 'delete')")
            self.cmd.hostgroup.print_help()

    # iscsi diskgroup
    def diskgroup(self, args, js):
        # diskgroup判断
        if args.diskgroup in ['create', 'c']:
            if args.gui == 'gui':
                data = pickle.dumps(Diskgroup.create(args, js))
                sundry.send_via_socket(data)
            else:
                Diskgroup.create(args, js)
        elif args.diskgroup in ['show', 's']:
            Diskgroup.show(args, js)
        elif args.diskgroup in ['delete', 'd']:
            Diskgroup.delete(args, js)
        else:
            print("iscsi diskgroup (choose from 'create', 'show', 'delete')")
            self.cmd.diskgroup.print_help()

    # iscsi map
    def map(self, args, js):
        # map判断
        if args.map in ['create', 'c']:
            if args.gui == 'gui':
                data = pickle.dumps(Map.create(args, js))
                sundry.send_via_socket(data)
            else:
                Map.create(args, js)
        elif args.map in ['show', 's']:
            Map.show(args, js)
        elif args.map in ['delete', 'd']:
            Map.delete(args, js)
        else:
            print("iscsi map (choose from 'create', 'show', 'delete')")
            self.cmd.map.print_help()

    # iscsi show
    def show(self, args, js):
        data = js.read_data_json()
        if args.json in ['json']:
            handle = sundry.send_via_socket()
            handle.send_result(data, js)
        else:
            print(data)


class Host():
    # host创建
    @classmethod
    def host_create(cls, args, js):
        print("Host name:", args.iqnname)
        print("iqn:", args.iqn)
        if js.check_key('Host', args.iqnname):
            print("Fail! The Host " + args.iqnname + " already existed.")
            return False
        else:
            js.creat_data("Host", args.iqnname, args.iqn)
            print("Create success!")
            return True

    # host查询
    @classmethod
    def host_show(cls, args, js):
        if args.show == 'all' or args.show == None:
            hosts = js.get_data("Host")
            print(" " + "{:<15}".format("Hostname") + "Iqn")
            print(" " + "{:<15}".format("---------------") + "---------------")
            for k in hosts:
                print(" " + "{:<15}".format(k) + hosts[k])
        else:
            if js.check_key('Host', args.show):
                print(args.show, ":", js.get_data('Host').get(args.show))
            else:
                print("Fail! Can't find " + args.show)
                return False
        return True

    # host删除
    @classmethod
    def host_delete(cls, args, js):
        print("Delete the host <", args.iqnname, "> ...")
        if js.check_key('Host', args.iqnname):
            if js.check_value('HostGroup', args.iqnname):
                print("Fail! The host in ... hostgroup, Please delete the hostgroup first.")
                return False
            else:
                js.delete_data('Host', args.iqnname)
                print("Delete success!")
                return True
        else:
            print("Fail! Can't find " + args.iqnname)
            return False


# iscsi disk
class Disk():
    # disk查询
    @classmethod
    def disk_show(cls, args, js):
        cd = esc.crm()
        data = cd.get_data_linstor()
        linstorlv = esc.linstor.refine_linstor(data)
        disks = {}
        for d in linstorlv:
            disks.update({d[1]: d[5]})
        js.up_data('Disk', disks)
        if args.show == 'all' or args.show == None:
            print(" " + "{:<15}".format("Diskname") + "Path")
            print(" " + "{:<15}".format("---------------") + "---------------")
            for k in disks:
                print(" " + "{:<15}".format(k) + disks[k])
        else:
            if js.check_key('Disk', args.show):
                print(args.show, ":", js.get_data('Disk').get(args.show))
            else:
                print("Fail! Can't find " + args.show)


# iscsi hostgroup
class Hostgroup():
    # hostgroup创建
    @classmethod
    def hostgroup_create(cls, args, js):
        print("Hostgroup name:", args.hostgroupname)
        print("Host name:", args.iqnname)
        if js.check_key('HostGroup', args.hostgroupname):
            print("Fail! The HostGroup " + args.hostgroupname + " already existed.")
            return False
        else:
            t = True
            for i in args.iqnname:
                if js.check_key('Host', i) == False:
                    t = False
                    print("Fail! Can't find " + i)
            if t:
                js.creat_data('HostGroup', args.hostgroupname, args.iqnname)
                print("Create success!")
                return True
            else:
                print("Fail! Please give the true name.")
                return False

    # hostgroup查询
    @classmethod
    def hostgroup_show(cls, args, js):
        if args.show == 'all' or args.show == None:
            print("Hostgroup:")
            hostgroups = js.get_data("HostGroup")
            for k in hostgroups:
                print(" " + "---------------")
                print(" " + k + ":")
                for v in hostgroups[k]:
                    print("     " + v)
        else:
            if js.check_key('HostGroup', args.show):
                print(args.show + ":")
                for k in js.get_data('HostGroup').get(args.show):
                    print(" " + k)
            else:
                print("Fail! Can't find " + args.show)

    # hostgroup删除
    @classmethod
    def hostgroup_delete(cls, args, js):
        print("Delete the hostgroup <", args.hostgroupname, "> ...")
        if js.check_key('HostGroup', args.hostgroupname):
            if js.check_value('Map', args.hostgroupname):
                print("Fail! The hostgroup already map,Please delete the map")
            else:
                js.delete_data('HostGroup', args.hostgroupname)
                print("Delete success!")
        else:
            print("Fail! Can't find " + args.hostgroupname)


# iscsi diskgroup
class Diskgroup():
    # diskgroup创建
    @classmethod
    def create(cls, args, js):
        print("Diskgroup name:", args.diskgroupname)
        print("Disk name:", args.diskname)
        if js.check_key('DiskGroup', args.diskgroupname):
            print("Fail! The DiskGroup " + args.diskgroupname + " already existed.")
            return False
        else:
            t = True
            for i in args.diskname:
                if js.check_key('Disk', i) == False:
                    t = False
                    print("Fail! Can't find " + i)
            if t:
                js.creat_data('DiskGroup', args.diskgroupname, args.diskname)
                print("Create success!")
                return True
            else:
                print("Fail! Please give the true name.")
                return False

    # diskgroup查询
    @classmethod
    def show(cls, args, js):
        if args.show == 'all' or args.show == None:
            print("Diskgroup:")
            diskgroups = js.get_data("DiskGroup")
            for k in diskgroups:
                print(" " + "---------------")
                print(" " + k + ":")
                for v in diskgroups[k]:
                    print("     " + v)
        else:
            if js.check_key('DiskGroup', args.show):
                print(args.show + ":")
                for k in js.get_data('DiskGroup').get(args.show):
                    print(" " + k)
            else:
                print("Fail! Can't find " + args.show)

    # diskgroup删除
    @classmethod
    def delete(cls, args, js):
        print("Delete the diskgroup <", args.diskgroupname, "> ...")
        if js.check_key('DiskGroup', args.diskgroupname):
            if js.check_value('Map', args.diskgroupname):
                print("Fail! The diskgroup already map,Please delete the map")
            else:
                js.delete_data('DiskGroup', args.diskgroupname)
                print("Delete success!")
        else:
            print("Fail! Can't find " + args.diskgroupname)


# iscsi map
class Map():
    obj_map = esc.iscsi_map()
    # map创建
    @classmethod
    def create(cls, args, js):
        print("Map name:", args.mapname)
        print("Hostgroup name:", args.hg)
        print("Diskgroup name:", args.dg)
        if js.check_key('Map', args.mapname):
            print("The Map \"" + args.mapname + "\" already existed.")
            return False
        elif js.check_key('HostGroup', args.hg) == False:
            print("Can't find " + args.hg)
            return False
        elif js.check_key('DiskGroup', args.dg) == False:
            print("Can't find " + args.dg)
            return False
        else:
            if js.check_value('Map', args.dg) == True:
                print("The diskgroup already map")
                return False
            else:
                crmdata = cls.obj_map.crm_up(js)
                if crmdata:
                    mapdata = cls.obj_map.map_data(js, crmdata, args.hg, args.dg)
                    if cls.obj_map.map_crm_c(mapdata):
                        js.creat_data('Map', args.mapname, [args.hg, args.dg])
                        print("Create success!")
                        return True
                    else:
                        return False
                else:
                    return False

    # map查询
    @classmethod
    def show(cls, args, js):
        crmdata = cls.obj_map.crm_up(js)
        if args.show == 'all' or args.show == None:
            print("Map:")
            maps = js.get_data("Map")
            for k in maps:
                print(" " + "---------------")
                print(" " + k + ":")
                for v in maps[k]:
                    print("     " + v)
        else:
            if js.check_key('Map', args.show):
                print(args.show + ":")
                maplist = js.get_data('Map').get(args.show)
                print(' ' + maplist[0] + ':')
                for i in js.get_data('HostGroup').get(maplist[0]):
                    print('     ' + i + ': ' + js.get_data('Host').get(i))
                print(' ' + maplist[1] + ':')
                for i in js.get_data('DiskGroup').get(maplist[1]):
                    print('     ' + i + ': ' + js.get_data('Disk').get(i))
            else:
                print("Fail! Can't find " + args.show)

    # map删除
    @classmethod
    def delete(cls, args, js):
        print("Delete the map <", args.mapname, ">...")
        if js.check_key('Map', args.mapname):
            print(js.get_data('Map').get(args.mapname), "will probably be affected ")
            resname = cls.obj_map.map_data_d(js, args.mapname)
            if cls.obj_map.map_crm_d(resname):
                js.delete_data('Map', args.mapname)
                print("Delete success!")
        else:
            print("Fail! Can't find " + args.mapname)




if __name__ == '__main__':
    obj_cli = Vtel()
    obj_cli.vtel_judge()
    # args = obj_cli.args
    # parser = obj_cli.cmd
    # args.func(args,parser)
