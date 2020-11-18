import pickle
import execute as ex
import sundry as sd
import consts


class HostCommands():
    def __init__(self):
        self.logger = consts.glo_log()

    def setup_commands(self, parser):
        """
        Add commands for the hosw management:create,delete,show
        """
        host_parser = parser.add_parser(
            'host', aliases='h', help='host operation')
        self.host_parser = host_parser
        host_subp = host_parser.add_subparsers(dest='host')

        """
        Create iSCSI Host
        """
        p_create_host = host_subp.add_parser(
            'create', aliases='c', help='host create [host_name] [host_iqn]')

        # add arguments of host create
        p_create_host.add_argument(
            'host', action='store', help='host_name')
        p_create_host.add_argument('iqn', action='store', help='host_iqn')

        p_create_host.set_defaults(func=self.create)

        """
        Delete iSCSI Host
        """
        p_delete_host = host_subp.add_parser(
            'delete', aliases='d', help='host delete [host_name]')

        # add arguments of host delete
        p_delete_host.add_argument(
            'host',
            action='store',
            help='host_name',
            default=None)

        p_delete_host.set_defaults(func=self.delete)

        """
        Show iSCSI Host
        """
        p_show_host = host_subp.add_parser(
            'show', aliases='s', help='host show / host show [host_name]')

        # add arguments of host show
        p_show_host.add_argument(
            'host',
            action='store',
            help='host show [host_name]',
            nargs='?',
            default='all')

        p_show_host.set_defaults(func=self.show)

        host_parser.set_defaults(func=self.print_host_help)


        """
        Modify iSCSI Host
        """
        p_modify_host = host_subp.add_parser(
            'modify', aliases='m', help='host modify / host modify [host_name]')

        # add arguments of host modify
        p_modify_host.add_argument(
            'host', action='store', help='host you want to modify')

        p_modify_host.add_argument(
            'iqn' , action='store', help='iqn you want to modify')

        p_modify_host.set_defaults(func=self.modify)



    @sd.deco_record_exception
    def create(self, args):
        host = ex.Host()
        host.create_host(args.host, args.iqn)

    @sd.deco_record_exception
    def show(self, args):
        host = ex.Host()
        if args.host == 'all' or args.host is None:
            host.show_all_host()
        else:
            host.show_spe_host(args.host)

    @sd.deco_record_exception
    def delete(self, args):
        host = ex.Host()
        host.delete_host(args.host)

    @sd.deco_record_exception
    def modify(self, args):
        host = ex.Host()
        host.modify_host(args.host,args.iqn)

    def print_host_help(self, *args):
        self.host_parser.print_help()
