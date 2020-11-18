import pickle
import execute as ex
import sundry as sd
import consts


class DiskGroupCommands():

    def __init__(self):
        self.logger = consts.glo_log()

    def setup_commands(self, parser):
        """
        Add commands for the diskgroup management:create,delete,show
        """
        # dg:diskgroup
        dg_parser = parser.add_parser(
            'diskgroup', aliases=['dg'], help='diskgroup operation')
        self.dg_parser = dg_parser

        dg_subp = dg_parser.add_subparsers(dest='diskgroup')

        """
        Create DiskGroup
        """
        p_create_dg = dg_subp.add_parser(
            'create',
            aliases='c',
            help='diskgroup create [diskgroup_name] [disk_name1] [disk_name2] ...')

        # add arguments of diskgroup create
        p_create_dg.add_argument(
            'diskgroup',
            action='store',
            help='diskgroup_name')
        p_create_dg.add_argument(
            'disk',
            action='store',
            help='disk_name',
            nargs='+')

        self.p_create_dg = p_create_dg
        p_create_dg.set_defaults(func=self.create)

        """
        Show DiskGroup
        """
        p_show_dg = dg_subp.add_parser(
            'show',
            aliases='s',
            help='diskgroup show / diskgroup show [diskgroup_name]')

        # add arguments of diskgroup show
        p_show_dg.add_argument(
            'diskgroup',
            action='store',
            help='diskgroup show [diskgroup_name]',
            nargs='?',
            default='all')

        p_show_dg.set_defaults(func=self.show)

        """
        Delete DiskGroup
        """
        # add arguments of diskgroup delete
        P_delete_dg = dg_subp.add_parser(
            'delete', aliases='d', help='diskgroup delete [diskgroup_name]')

        P_delete_dg.add_argument(
            'diskgroup',
            action='store',
            help='diskgroup_name',
            default=None)

        P_delete_dg.set_defaults(func=self.delete)

        dg_parser.set_defaults(func=self.print_dg_help)


        """
        Modify HostGroup
        """
        p_modify_dg = dg_subp.add_parser(
            'modify',
            aliases='m',
            help='diskgroup modify [hostgroup_name] [-a disk_name1] [-d disk_name2] ...')


        p_modify_dg.add_argument(
            'diskgroup',
            help='diskgroup_name')

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
        diskgroup.create_diskgroup(args.diskgroup, args.disk)

    @sd.deco_record_exception
    def show(self, args):
        diskgroup = ex.DiskGroup()
        if args.diskgroup == 'all' or args.diskgroup is None:
            diskgroup.show_all_diskgroup()
        else:
            diskgroup.show_spe_diskgroup(args.diskgroup)

    @sd.deco_record_exception
    def delete(self, args):
        diskgroup = ex.DiskGroup()
        diskgroup.delete_diskgroup(args.diskgroup)


    def modify(self, args):
        diskgroup = ex.DiskGroup()
        if args.add:
            diskgroup.add_disk(args.diskgroup,args.add)
        if args.remove:
            diskgroup.remove_disk(args.diskgroup,args.remove)


    def print_dg_help(self, *args):
        self.dg_parser.print_help()
