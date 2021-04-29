import execute as ex
import sundry as s

class Usage():
    # target部分使用手册
    target = '''
    target {create(c)/modify(m)/delete(d)/show(s)/start/stop}'''

    target_create = '''
    target create(c) TARGET -iqn [IQN] -portal [PORTAL]'''

    target_delete = '''
    target delete(d) TARGET'''

    target_modify = '''
    target modify(m) TARGET -iqn [IQN] -portal [PORTAL]'''

    target_show = '''
    target show(s)'''

    target_start = '''
    target start'''

    target_stop = '''
    target stop'''




class TargetCommands():

    def __init__(self):
        pass

    def setup_commands(self, parser):
        """
        Add commands for the PORTAL management:create,delete,modify,show
        """
        target_parser = parser.add_parser(
            'target', aliases=['tg'], help='target operation',usage=Usage.target)
        self.target_parser = target_parser

        target_subp = target_parser.add_subparsers(dest='target')

        """
        Create Target
        """
        p_create_target = target_subp.add_parser(
            'create',
            aliases='c',
            help='Create the iSCSI Target',
            usage = Usage.target_create)

        # add arguments of target create
        p_create_target.add_argument(
            'target',
            action='store',
            help='Target Name')

        p_create_target.add_argument(
            '-iqn',
            action='store',
            required=True,
            dest='iqn',
            help='IQN'
        )

        p_create_target.add_argument(
            '-pt',
            '-portal',
            '--portal',
            dest='portal',
            required=True,
            action='store',
            help='Portal')

        self.p_create_target = p_create_target
        p_create_target.set_defaults(func=self.create)

        """
        Show Target
        """
        p_show_target = target_subp.add_parser(
            'show',
            aliases='s',
            help='Show the Target',
            usage=Usage.target_show)

        p_show_target.set_defaults(func=self.show)

        """
        Delete Target
        """
        # add arguments of target delete
        p_delete_target = target_subp.add_parser(
            'delete', aliases='d', help='Delete the Target',usage=Usage.target_delete)

        p_delete_target.add_argument(
            'target',
            action='store',
            help='target name')

        p_delete_target.set_defaults(func=self.delete)

        target_parser.set_defaults(func=self.print_target_help)


        """
        Modify Target
        """
        p_modify_target = target_subp.add_parser(
            'modify',
            aliases='m',
            help='Modify the Target',
            usage=Usage.target_modify)


        p_modify_target.add_argument(
            'target',
            help='target name')


        p_modify_target.add_argument(
            '-iqn',
            dest='iqn',
            action='store',
            help='IQN',
            metavar='IQN')

        p_modify_target.add_argument(
            '-pt',
            '-portal',
            '--portal',
            dest='portal',
            action='store',
            help='portal',
            metavar='PORTAL')

        p_modify_target.set_defaults(func=self.modify)


        """
        Start Target
        """
        p_start_target = target_subp.add_parser(
            'start',
            help='Start the Target',
            usage=Usage.target_start)

        p_start_target.add_argument(
            'target',
            help='target name')

        p_start_target.set_defaults(func=self.start)



        """
        Stop Target
        """
        p_stop_target = target_subp.add_parser(
            'stop',
            help='Stop the Target',
            usage=Usage.target_stop)

        p_stop_target.add_argument(
            'target',
            help='target name')


        p_stop_target.set_defaults(func=self.stop)



    @s.deco_record_exception
    def create(self, args):
        crm = ex.CRMData()
        crm.check()
        target = ex.Target()
        target.create(args.target,args.iqn,args.portal)


    @s.deco_record_exception
    def show(self, args):
        crm = ex.CRMData()
        crm.check()
        target = ex.Target()
        target.show()


    @s.deco_record_exception
    def delete(self, args):
        crm = ex.CRMData()
        crm.check()
        target = ex.Target()
        target.delete(args.target)


    @s.deco_record_exception
    def modify(self, args):
        crm = ex.CRMData()
        crm.check()
        target = ex.Target()
        target.modify(args.target,args.iqn,args.portal)


    def start(self,args):
        crm = ex.CRMData()
        crm.check()
        target = ex.Target()
        target.start(args.target)


    def stop(self,args):
        crm = ex.CRMData()
        crm.check()
        target = ex.Target()
        target.stop(args.target)


    def print_target_help(self, *args):
        self.target_parser.print_help()
