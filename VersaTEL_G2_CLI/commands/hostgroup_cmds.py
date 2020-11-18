import pickle
import execute as ex
import sundry as sd
import consts


class HostGroupCommands():

    def __init__(self):
        self.logger = consts.glo_log()

    def setup_commands(self, parser):
        """
        Add commands for the host group management:create,delete,show
        """
        # hg:hostgroup
        hg_parser = parser.add_parser(
            'hostgroup', aliases=['hg'], help='hostgroup operation')
        self.hg_parser = hg_parser
        hg_subp = hg_parser.add_subparsers(dest='hostgroup')

        """
        Create HostGroup
        """
        p_create_hg = hg_subp.add_parser(
            'create',
            aliases='c',
            help='hostgroup create [hostgroup_name] [host_name1] [host_name2] ...')

        p_create_hg.add_argument(
            'hostgroup',
            action='store',
            help='hostgroup_name')
        p_create_hg.add_argument(
            'host',
            action='store',
            help='host_name',
            nargs='+')

        # level4,arguments of hostgroup show
        p_create_hg.add_argument(
            'show',
            action='store',
            help='hostgroup show [hostgroup_name]',
            nargs='?',
            default='all')

        p_create_hg.set_defaults(func=self.create)

        """
        Show HostGroup
        """
        p_show_hg = hg_subp.add_parser(
            'show',
            aliases='s',
            help='hostgroup show / hostgroup show [hostgroup_name]')

        p_show_hg.add_argument(
            'hostgroup',
            action='store',
            help='hostgroup show [hostgroup_name]',
            nargs='?',
            default='all')

        p_show_hg.set_defaults(func=self.show)

        """
        Delete HostGroup
        """
        p_delete_hg = hg_subp.add_parser(
            'delete', aliases='d', help='hostgroup delete [hostgroup_name]')

        p_delete_hg.add_argument(
            'hostgroup',
            action='store',
            help='hostgroup_name',
            default=None)

        p_delete_hg.set_defaults(func=self.delete)


        """
        Modify HostGroup
        """
        p_modify_hg = hg_subp.add_parser(
            'modify',
            aliases='m',
            help='hostgroup modify [hostgroup_name] [-a host_name1] [-d host_name2] ...')


        p_modify_hg.add_argument(
            'hostgroup',
            help='hostgroup_name')

        p_modify_hg.add_argument(
            '-a',
            '--add',
            dest='add',
            action='store',
            help='host name',
            metavar='HOST',
            nargs='+')

        p_modify_hg.add_argument(
            '-r',
            '--remove',
            dest='remove',
            action='store',
            help='host name',
            metavar='HOST',
            nargs='+')

        p_modify_hg.set_defaults(func=self.modify)

        hg_parser.set_defaults(func=self.print_hg_help)


    @sd.deco_record_exception
    def create(self, args):
        hostgroup = ex.HostGroup()
        hostgroup.create_hostgroup(args.hostgroup, args.host)

    @sd.deco_record_exception
    def show(self, args):
        hostgroup = ex.HostGroup()
        if args.hostgroup == 'all' or args.hostgroup is None:
            hostgroup.show_all_hostgroup()
        else:
            hostgroup.show_spe_hostgroup(args.hostgroup)

    @sd.deco_record_exception
    def delete(self, args):
        hostgroup = ex.HostGroup()
        hostgroup.delete_hostgroup(args.hostgroup)


    @sd.deco_record_exception
    def modify(self, args):
        hostgroup = ex.HostGroup()
        if args.add:
            hostgroup.add_host(args.hostgroup,args.add)
        if args.remove:
            hostgroup.remove_host(args.hostgroup,args.remove)


    def print_hg_help(self, *args):
        self.hg_parser.print_help()
