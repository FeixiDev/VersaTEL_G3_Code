import execute as ex
import sundry as sd
import execute.lvm_operation as lvm
import sys
import random


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
            help='Type: vg or thinpool',
            choices=['vg', 'thinpool'],
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
            help='Type: vg or thinpool',
            choices=['vg', 'thinpool'],
            required=True)
        p_delete_lvm.add_argument(
            '-dvg',
            '--delvg',
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
            help='Display the LVM information',
            usage=Usage.lvm_show)
        self.p_show_lvm = p_show_lvm
        p_show_lvm.add_argument(
            '-n',
            '--node',
            dest='node',
            action='store',
            help='Display LVM on this Node')
        p_show_lvm.add_argument(
            '-vg',
            dest='vg',
            action='store',
            help='VG name that you want to show')
        p_show_lvm.add_argument(
            '-d',
            '--device',
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
        if args.vg and args.device:
            print(f"Only show unused lvm device, message of {args.vg} will not display")
        for node in node_list:
            print()
            print('=' * 15, "Node:", node, '=' * 15)
            lvm_operation = lvm.ClusterLVM(node)
            if args.device:
                lvm_operation.show_unused_lvm_device()
            else:
                lvm_operation.show_vg(args.vg)

    @sd.deco_record_exception
    def create(self, args):
        lvm_operation = lvm.ClusterLVM(args.node)
        if args.type == "vg":
            if lvm_operation.check_vg_exit(args.name):
                if args.device:
                    if lvm_operation.check_pv_exit(args.device):
                        for pv in args.device:
                            lvm_operation.create_pv(pv)
                    else:
                        sys.exit()
                    lvm_operation.create_vg(args.name, args.device)
                else:
                    print("The following arguments are required: -d/--device DEVICE [DEVICE ...]")
            else:
                print(f"{args.name} is already exists.")
                sys.exit()
        if args.type == "thinpool":
            if args.vg:
                if not lvm_operation.check_vg_exit(args.vg):
                    if args.vg in lvm_operation.get_vg_via_thinpool(args.name):
                        print(f"{args.name} already exists in {args.vg}")
                        sys.exit()
                    else:
                        vg_name = args.vg
                        size = lvm_operation.check_and_get_size(args.vg, args.size, "vg")
                else:
                    print("Please select the available vg.")
                    sys.exit()
            elif args.device:
                if lvm_operation.check_pv_exit(args.device):
                    size = lvm_operation.check_and_get_size(args.device, args.size, "device")
                    for pv in args.device:
                        lvm_operation.create_pv(pv)
                    vg_name = f'vvg_{args.name}_{random.randint(0, 10)}'
                    if not lvm_operation.check_vg_exit(vg_name):
                        vg_name = f'vvg_{args.name}_{random.randint(0, 10)}{random.randint(0, 10)}'
                    lvm_operation.create_vg(vg_name, args.device)
                else:
                    print("Please select the available device.")
                    sys.exit()
            else:
                print("The following arguments are required:  -d DEVICE [DEVICE ...] / -vg VG")
                sys.exit()
            size = f"{size}M"
            lvm_operation.create_thinpool(args.name, size, vg_name)

    @sd.deco_record_exception
    def delete(self, args):
        lvm_operation = lvm.ClusterLVM(args.node)
        if args.type == "vg":
            lvm_operation.delete_vg(args.name)
        if args.type == "thinpool":
            lvm_operation.delete_thinpool(args.name, args.confirm)

    def print_lvm_help(self, *args):
        self.lvm_parser.print_help()