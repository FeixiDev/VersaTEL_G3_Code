import argparse
import pickle
import sys
import re
import traceback
import sundry as sd
import execute as ex
import consts


class usage():
    resource = '''
    resource(r) {create(c)/modify(m)/delete(d)/show(s)}'''

    resource_create = '''
    resource(r) create(c) RESOURCE -s SIZE -n NODE[NODE...] -sp STORAGEPOOL[STORAGEPOOL...]
                          RESOURCE -s SIZE -a -num NUM
                          RESOURCE -diskless -n NODE[NODE...]
                          RESOURCE -am -n NODE[NODE...] -sp STORAGEPOOL[STORAGEPOOL...]
                          RESOURCE -am -a -num NUM'''

    resource_delete = '''
    resource(r) delete(d) RESOURCE [-n NODE]'''

    # 待完善
    resource_modify = '''
    resource(r) modify(m) RESOURCE ...'''

    resource_show = '''
    resource(r) show(s) [RESOURCE]'''


# 多节点创建resource时，storapoo多于node的异常类
class NodeAndSPNumError(Exception):
    pass


class InvalidSizeError(Exception):
    pass


class ResourceCommands():
    def __init__(self):
        self.logger = consts.glo_log()

    def setup_commands(self, parser):
        """
        Add commands for the node management:create,modify,delete,show
        """

        res_parser = parser.add_parser(
            'resource',
            aliases='r',
            help='Management operations for storagepool',
            usage=usage.resource)
        res_subp = res_parser.add_subparsers(dest='subargs_res')
        self.res_parser = res_parser

        """
        Create LINSTOR Resource
        """
        p_create_res = res_subp.add_parser('create',
                                           aliases='c',
                                           help='Create the resource',
                                           usage=usage.resource_create)
        self.p_create_res = p_create_res

        # add the parameters needed to create the resource
        p_create_res.add_argument(
            'resource',
            metavar='RESOURCE',
            action='store',
            help='Name of the resource')
        p_create_res.add_argument(
            '-s',
            dest='size',
            action='store',
            help=' Size of the resource.In addition to creating diskless resource, you must enter SIZE.'
            'Valid units: B, K, kB, KiB, M, MB,MiB, G, GB, GiB, T, TB, TiB, P, PB, PiB.\nThe default unit is GB.')

        # Add a parameter group that automatically creates a resource
        group_auto = p_create_res.add_argument_group(title='auto create')
        group_auto.add_argument(
            '-a',
            dest='auto',
            action='store_true',
            default=False,
            help='Auto create method Automatic create')
        group_auto.add_argument(
            '-num',
            dest='num',
            action='store',
            help='Number of nodes specified by auto creation method',
            type=int)

        # Add a parameter group that automatically creates a resource
        group_manual = p_create_res.add_argument_group(title='manual create')
        group_manual.add_argument(
            '-n',
            dest='node',
            action='store',
            nargs='+',
            help='Name of the node to deploy the resource')
        group_manual.add_argument(
            '-sp',
            dest='storagepool',
            nargs='+',
            help='Storage pool name to use.')

        # Add parameter groups for adding resource mirrors
        group_manual_diskless = p_create_res.add_argument_group(
            title='diskless create')
        group_manual_diskless.add_argument(
            '-diskless',
            action='store_true',
            default=False,
            dest='diskless',
            help='Will add a diskless resource on all non replica nodes.')

        # Add parameter groups for adding resource mirrors
        group_add_mirror = p_create_res.add_argument_group(
            title='add mirror way')
        group_add_mirror.add_argument(
            '-am',
            action='store_true',
            default=False,
            dest='add_mirror',
            help='Add mirror member base on specify node to specify resource.')

        p_create_res.set_defaults(func=self.create)

        """
        Modify LINSTOR Resource
        """
        #p_modify_res = res_subp.add_parser('modify', aliases='m', help='Modify the resource',usage=usage.resource_modify)
        pass

        """
        Delete LINSTOR Resource
        """
        p_delete_res = res_subp.add_parser(
            'delete',
            aliases='d',
            help='Delete the resource',
            usage=usage.resource_delete)
        self.p_delete_res = p_delete_res
        p_delete_res.add_argument(
            'resource',
            metavar='RESOURCE',
            action='store',
            help='Name of the resource to delete')
        p_delete_res.add_argument(
            '-n',
            dest='node',
            action='store',
            help='The name of the node. In this way, the cluster retains the attribute of the resource, including its name and size.')
        p_delete_res.add_argument(
            '-y',
            dest='yes',
            action='store_true',
            help='Skip to confirm selection',
            default=False)

        p_delete_res.set_defaults(func=self.delete)

        """
        Show LINSTOR Resource
        """
        p_show_res = res_subp.add_parser(
            'show',
            aliases='s',
            help='Displays the resource view',
            usage=usage.resource_show)
        self.p_show_res = p_show_res
        p_show_res.add_argument(
            'resource',
            metavar='RESOURCE',
            help='Print information about the resource in LINSTOR cluster',
            action='store',
            nargs='?')
        p_show_res.add_argument(
            '--no-color',
            dest='nocolor',
            help='Do not use colors in output.',
            action='store_true',
            default=False)

        p_show_res.set_defaults(func=self.show)

        res_parser.set_defaults(func=self.print_resource_help)

    @staticmethod
    def is_args_correct(node, storagepool):
        if len(node) < len(storagepool):
            raise NodeAndSPNumError('指定的storagepool数量应少于node数量')
        elif len(node) > len(storagepool) > 1:
            raise NodeAndSPNumError(
                'The number of Node and Storage pool do not meet the requirements')

    @staticmethod
    def is_vail_size(size):
        re_size = re.compile('^[1-9][0-9]*([KkMmGgTtPpB](iB|B)?)$')
        if not re_size.match(size):
            raise InvalidSizeError('Invalid Size')

    @sd.deco_record_exception
    def create(self, args):
        """
        Create a LINSTOR resource. There are three types of creation based on different parameters:
        Automatically create resource,
        Create resources by specifying nodes and storage pools,
        create diskless resource,
        add mirror on other nodes

        :param args: Namespace that has been parsed for CLI
        """
        res = ex.Resource()

        """对应创建模式必需输入的参数和禁止输入的参数"""
        # Parameters required for automatic resource creation
        list_auto_required = [args.auto, args.num]
        # Automatically create input parameters for resource prohibition
        list_auto_forbid = [
            args.node,
            args.storagepool,
            args.diskless,
            args.add_mirror]
        # Specify the node and storage pool to create resources require input
        # parameters
        list_manual_required = [args.node, args.storagepool]
        # Specify the input parameters for node and storage pool creation
        # resource prohibition
        list_manual_forbid = [
            args.auto,
            args.num,
            args.diskless,
            args.add_mirror]
        # Create diskless resource prohibited input parameters
        list_diskless_forbid = [
            args.auto,
            args.num,
            args.storagepool,
            args.add_mirror]

        if args.size:
            # judge size
            try:
                self.is_vail_size(args.size)
            except InvalidSizeError:
                print('%s is not a valid size!' % args.size)
                sys.exit()
            # 自动创建条件判断，符合则执行
            if all(list_auto_required) and not any(list_auto_forbid):
                res.create_res_auto(args.resource, args.size, args.num)
            # 手动创建条件判断，符合则执行
            elif all(list_manual_required) and not any(list_manual_forbid):
                try:
                    self.is_args_correct(args.node, args.storagepool)
                except NodeAndSPNumError:
                    print('The number of nodes does not meet the requirements')
                    self.logger.write_to_log(
                        'DATA', 'debug', 'exception', '', str(traceback.format_exc()))
                    sys.exit()
                else:
                    res.create_res_manual(
                        args.resource, args.size, args.node, args.storagepool)
            else:
                # self.logger.add_log(username, 'cli_user_input', transaction_id, path, 'ARGPARSE_ERROR', cmd)
                self.p_create_res.print_help()

        elif args.diskless:
            # 创建resource的diskless资源条件判断，符合则执行
            if args.node and not any(list_diskless_forbid):
                res.create_res_diskless(args.node, args.resource)
            else:
                self.p_create_res.print_help()

        elif args.add_mirror:
            # 手动添加mirror条件判断，符合则执行
            if all([args.node, args.storagepool]) and not any(
                    [args.auto, args.num]):
                try:
                    self.is_args_correct(args.node, args.storagepool)
                    res.add_mirror_manual(
                        args.resource, args.node, args.storagepool)
                except NodeAndSPNumError:
                    print('The number of nodes does not meet the requirements')
                    self.logger.write_to_log(
                        'DATA', 'debug', 'exception', '', str(traceback.format_exc()))
                    sys.exit()
                # else:
                #     self.p_create_res.print_help()
            # 自动添加mirror条件判断，符合则执行
            elif all([args.auto, args.num]) and not any([args.node, args.storagepool]):
                res.add_mirror_auto(args.resource, args.num)
            else:
                self.p_create_res.print_help()

        else:
            self.p_create_res.print_help()

    @sd.deco_record_exception
    @sd.deco_comfirm_del('resource')
    def delete(self, args):
        res = ex.Resource()
        if args.node:
            res.delete_resource_des(args.node, args.resource)
        elif not args.node:
            res.delete_resource_all(args.resource)

    @sd.deco_record_exception
    def show(self, args):
        res = ex.Resource()
        if args.nocolor:
            if args.resource:
                res.show_one_res(args.resource, no_color='yes')
            else:
                res.show_all_res(no_color='yes')
        else:
            if args.resource:
                res.show_one_res(args.resource)
            else:
                res.show_all_res()

    def print_resource_help(self, *args):
        self.res_parser.print_help()
