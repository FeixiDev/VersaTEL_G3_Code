import execute as ex
import sundry as s

class Usage():
    # portal部分使用手册
    portal = '''
    portal {create(c)/modify(m)/delete(d)/show(s)}'''

    portal_create = '''
    portal create(c) PORTAL -ip IP -port [PORT] -netmask [NETMASK]'''

    portal_delete = '''
    portal delete(d) PORTAL'''

    portal_modify = '''
    portal modify(m) PORTAL -ip IP -port PORT -netmask [NETMASK]'''

    portal_show = '''
    portal show(s)'''


class PortalCommands():

    def __init__(self):
        pass

    def setup_commands(self, parser):
        """
        Add commands for the PORTAL management:create,delete,modify,show
        """
        portal_parser = parser.add_parser(
            'portal', aliases=['pt'], help='portal operation',usage=Usage.portal)
        self.portal_parser = portal_parser

        portal_subp = portal_parser.add_subparsers(dest='portal')

        """
        Create PORTAL
        """
        p_create_portal = portal_subp.add_parser(
            'create',
            aliases='c',
            help='Create the PORTAL',
            usage = Usage.portal_create)

        # add arguments of portal create
        p_create_portal.add_argument(
            'portal',
            action='store',
            help='PORTAL Name')

        p_create_portal.add_argument(
            '-ip',
            action='store',
            required=True,
            dest='ip',
            help='IP'
        )

        p_create_portal.add_argument(
            '-n',
            '-netmask',
            '--netmask',
            type=int,
            dest='netmask',
            action='store',
            default=24,
            help='Netmask：1-32.It default is 24.')

        p_create_portal.add_argument(
            '-p',
            '-port',
            '--port',
            type=int,
            action='store',
            dest='port',
            default=3260,
            help='Port：3260-65535.It default is 3260.')




        self.p_create_portal = p_create_portal
        p_create_portal.set_defaults(func=self.create)

        """
        Show PORTAL
        """
        p_show_portal = portal_subp.add_parser(
            'show',
            aliases='s',
            help='Show the PORTAL',
            usage=Usage.portal_show)

        p_show_portal.set_defaults(func=self.show)

        """
        Delete PORTAL
        """
        # add arguments of portal delete
        p_delete_portal = portal_subp.add_parser(
            'delete', aliases='d', help='Delete the PORTAL',usage=Usage.portal_delete)

        p_delete_portal.add_argument(
            'portal',
            action='store',
            help='portal name')

        p_delete_portal.set_defaults(func=self.delete)

        portal_parser.set_defaults(func=self.print_portal_help)


        """
        Modify PORTAL
        """
        p_modify_portal = portal_subp.add_parser(
            'modify',
            aliases='m',
            help='Modify the PORTAL',
            usage=Usage.portal_modify)


        p_modify_portal.add_argument(
            'portal',
            help='portal name')


        p_modify_portal.add_argument(
            '-ip',
            dest='ip',
            action='store',
            help='IP',
            metavar='IP')

        p_modify_portal.add_argument(
            '-p',
            '-port',
            '--port',
            type=int,
            dest='port',
            action='store',
            help='port',
            metavar='PORT')

        p_modify_portal.add_argument(
            '-n',
            '-netmask',
            '--netmask',
            type=int,
            dest='netmask',
            action='store',
            help='Netmask：1-32.')

        p_modify_portal.set_defaults(func=self.modify)


    @s.deco_record_exception
    def create(self, args):
        crm = ex.CRMData()
        crm.check()

        portal = ex.Portal()
        portal.create(args.portal,args.ip,args.port,args.netmask)


    @s.deco_record_exception
    def show(self, args):
        crm = ex.CRMData()
        crm.check()

        portal = ex.Portal()
        portal.show()


    @s.deco_record_exception
    def delete(self, args):
        crm = ex.CRMData()
        crm.check()

        portal = ex.Portal()
        portal.delete(args.portal)


    @s.deco_record_exception
    def modify(self, args):
        crm = ex.CRMData()
        crm.check()

        if any([args.ip,args.port,args.netmask]):
            portal = ex.Portal()
            portal.modify(args.portal,args.ip,args.port,args.netmask)
        else:
            s.prt_log('Please specify at least one data to be modified',1)


    def print_portal_help(self, *args):
        self.portal_parser.print_help()
