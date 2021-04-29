import execute as ex
import sundry as sd

class Usage():
    # host部分使用手册
    dg = '''
    diskgroup(dg) {create(c)/modify(m)/delete(d)/show(s)}'''

    dg_create = '''
    diskgroup(dg) create(c) DISKGROUP DISK[DISK...]'''

    dg_delete = '''
    diskgroup(dg) delete(d) DISKGROUP'''

    dg_modify = '''
    diskgroup(dg) modify(m) DISKGROUP DISK[DISK...]'''

    dg_show = '''
    diskgroup(dg) show(s) [DISKGROUP]'''


class DiskGroupCommands():

    def __init__(self):
        pass

    def setup_commands(self, parser):
        """
        Add commands for the diskgroup management:create,delete,show
        """
        # dg:diskgroup
        dg_parser = parser.add_parser(
            'diskgroup', aliases=['dg'], help='diskgroup operation',usage=Usage.dg)
        self.dg_parser = dg_parser

        dg_subp = dg_parser.add_subparsers(dest='diskgroup')

        """
        Create DiskGroup
        """
        p_create_dg = dg_subp.add_parser(
            'create',
            aliases='c',
            help='Create the DiskGroup',
            usage=Usage.dg_create
        )

        # add arguments of diskgroup create
        p_create_dg.add_argument(
            'diskgroup',
            action='store',
            help='diskgroup_name')
        p_create_dg.add_argument(
            'disk',
            action='store',
            help='disk name',
            nargs='+')

        self.p_create_dg = p_create_dg
        p_create_dg.set_defaults(func=self.create)

        """
        Show DiskGroup
        """
        p_show_dg = dg_subp.add_parser(
            'show',
            aliases='s',
            help='Show the DiskGroup',
            usage=Usage.dg_show)

        # add arguments of diskgroup show
        p_show_dg.add_argument(
            'diskgroup',
            action='store',
            help='diskgroup name',
            nargs='?',
            default='all')

        p_show_dg.set_defaults(func=self.show)

        """
        Delete DiskGroup
        """
        # add arguments of diskgroup delete
        P_delete_dg = dg_subp.add_parser(
            'delete', aliases='d', help='Delete the DiskGroup',usage=Usage.dg_delete)

        P_delete_dg.add_argument(
            'diskgroup',
            action='store',
            help='diskgroup_name',
            default=None)
        # P_delete_dg.add_argument(
        #     '-y',
        #     dest='yes',
        #     action='store_true',
        #     help='Skip to confirm selection',
        #     default=False)

        P_delete_dg.set_defaults(func=self.delete)

        dg_parser.set_defaults(func=self.print_dg_help)


        """
        Modify Disk Group
        """
        p_modify_dg = dg_subp.add_parser(
            'modify',
            aliases='m',
            help='Modify the DiskGroup',
            usage=Usage.dg_modify)


        p_modify_dg.add_argument(
            'diskgroup',
            help='diskgroup name')

        p_modify_dg.add_argument(
            '-a',
            '--add',
            dest='add',
            action='store',
            help='disk name',
            metavar='DISK',
            nargs='+')

        p_modify_dg.add_argument(
            '-r',
            '--remove',
            dest='remove',
            action='store',
            help='disk name',
            metavar='DISK',
            nargs='+')

        p_modify_dg.set_defaults(func=self.modify)


    @sd.deco_record_exception
    def create(self, args):
        diskgroup = ex.DiskGroup()
        diskgroup.create(args.diskgroup, args.disk)

    @sd.deco_record_exception
    def show(self, args):
        diskgroup = ex.DiskGroup()
        diskgroup.show(args.diskgroup)


    @sd.deco_record_exception
    def delete(self, args):
        diskgroup = ex.DiskGroup()
        diskgroup.delete(args.diskgroup)

    @sd.deco_record_exception
    def modify(self, args):
        diskgroup = ex.DiskGroup()
        if args.add:
            diskgroup.add_disk(args.diskgroup,args.add)
        if args.remove:
            diskgroup.remove_disk(args.diskgroup,args.remove)


    def print_dg_help(self, *args):
        self.dg_parser.print_help()
