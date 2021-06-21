import execute as ex
import sundry as sd
import execute.lvm_operation as lvm
import sys


class Usage():
    # host部分使用手册
    lvm = '''
    lvm {create(c)/delete(d)/show(s)}'''

    lvm_create = '''
        lvm create(c) NAME -n NODE -t vg -d DEVICE [DEVICE...]
        lvm create(c) NAME -n NODE -t thinpool -d DEVICE [DEVICE...] -s SIZE
        lvm create(c) NAME -n NODE -t thinpool -vg VG -s SIZE'''

    lvm_delete = '''
        lvm delete(d) NAME -n NODE -t vg
        lvm delete(d) NAME -n NODE -t thinpool [-dvg]'''

    lvm_show = '''
        lvm show(s) [-n NODE] [-vg VG] [-d]'''


class LVMCommands():
    def __init__(self):
        pass

    def setup_commands(self, parser):
        """
        Add commands for the lvm management:create,delete,show
        """

        lvm_parser = parser.add_parser(
            'lvm',
            help='Management operations for LVM',
            usage=Usage.lvm)

        self.lvm_parser = lvm_parser
        lvm_subp = lvm_parser.add_subparsers(dest='subargs_lvm')

        """
        Create LINSTOR lvm
        """
        p_create_lvm = lvm_subp.add_parser(
            'create',
            aliases='c',
            help='Create the LVM',
            usage=Usage.lvm_create)
        self.p_create_lvm = p_create_lvm
        # add the parameters needed to create the lvm
        p_create_lvm.add_argument(
            'name',
            metavar='name',
            action='store',
            help='Name of the vg or thinpool')
        p_create_lvm.add_argument(
            '-s',
            '--size',
            dest='size',
            action='store',
            help='Size of thinpool')
        p_create_lvm.add_argument(
            '-n',
            '--node',
            dest='node',
            action='store',
            help='Create LVM on this Node',
            required=True)
        p_create_lvm.add_argument(
            '-d',
            '--device',
            dest='device',
            action='store',
            nargs='+',
            help='Device that you want to used')
        p_create_lvm.add_argument(
            '-vg',
            dest='vg',
            action='store',
            help='VG that you want to used')
        p_create_lvm.add_argument(
            '-t',
            '--type',
            dest='type',
            action='store',
            help='vg or thinpool',
            required=True)

        p_create_lvm.set_defaults(func=self.create)

        """
        Delete LINSTOR lvm
        """
        p_delete_lvm = lvm_subp.add_parser(
            'delete',
            aliases='d',
            help='Delete the LVM',
            usage=Usage.lvm_delete)
        self.p_delete_lvm = p_delete_lvm
        p_delete_lvm.add_argument(
            'name',
            metavar='name',
            action='store',
            help='Name of the vg or thinpool')
        p_delete_lvm.add_argument(
            '-n',
            '--node',
            dest='node',
            action='store',
            help='Delete LVM on this Node',
            required=True)
        p_delete_lvm.add_argument(
            '-t',
            '--type',
            dest='type',
            action='store',
            help='vg or thinpool',
            required=True)
        p_delete_lvm.add_argument(
            '-dvg',
            dest='confirm',
            action='store_true',
            help='Confirm to delete vg with deleting thinpool',
            default=False)
        p_delete_lvm.set_defaults(func=self.delete)

        """
        Show LINSTOR lvm
        """
        p_show_lvm = lvm_subp.add_parser(
            'show',
            aliases='s',
            help='Displays the LVM information',
            usage=Usage.lvm_show)
        self.p_show_lvm = p_show_lvm
        p_show_lvm.add_argument(
            '-n',
            '--node',
            dest='node',
            action='store',
            help='Show LVM on this Node')
        p_show_lvm.add_argument(
            '-vg',
            dest='vg',
            action='store',
            help='VG name that you want to show')
        p_show_lvm.add_argument(
            '-d',
            dest='device',
            action='store_true',
            help='Display Device',
            default=False)

        p_show_lvm.set_defaults(func=self.show)

        lvm_parser.set_defaults(func=self.print_lvm_help)

    @sd.deco_record_exception
    def show(self, args):
        node_list = []
        api = ex.linstor_api.LinstorAPI()
        if args.node:
            node_list.append(args.node)
        else:
            node_dict = api.get_node()
            for node in node_dict:
                node_list.append(node["Node"])
        for node in node_list:
            print('=' * 15, "Node:", node, '=' * 15)
            lvm_operation = lvm.ClusterLVM(node)
            if args.device:
                lvm_operation.show_unused_lvm_device()
            lvm_operation.show_vg(args.vg)

    @sd.deco_record_exception
    def create(self, args):
        lvm_operation = lvm.ClusterLVM(args.node)
        if args.type == "vg":
            for pv in args.device:
                lvm_operation.create_pv(pv)
            lvm_operation.create_vg(args.name, args.device)
        if args.type == "thinpool":
            if args.vg:
                vg_name = args.vg
            elif args.device:
                for pv in args.device:
                    lvm_operation.create_pv(pv)
                vg_name = f'vvg_{args.name}'
                lvm_operation.create_vg(vg_name, args.device)
            else:
                sys.exit()
            lvm_operation.create_thinpool(args.name, args.size, vg_name)

    @sd.deco_record_exception
    def delete(self, args):
        lvm_operation = lvm.ClusterLVM(args.node)
        if args.type == "vg":
            lvm_operation.delete_vg(args.name)
        if args.type == "thinpool":
            lvm_operation.delete_thinpool(args.name, args.confirm)
            # vg = lvm_operation.get_vg_via_thinpool(args.name)
            # if not lvm_operation.check_thinpool(vg[0], args.name):
            #     if lvm_operation.del_thinpool(vg[0], args.name):
            #         pv_dict = lvm_operation.get_pv_via_vg(vg[0])
            #         if args.comfirm:
            #             if lvm_operation.del_vg(vg[0]):
            #                 for pv in pv_dict.keys():
            #                     lvm_operation.del_pv(pv)
            # else:
            #     print(f"{args.name} is in Used")

    def print_lvm_help(self, *args):
        self.lvm_parser.print_help()
