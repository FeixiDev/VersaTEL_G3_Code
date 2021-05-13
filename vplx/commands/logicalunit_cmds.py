import execute as ex
import sundry as s

class Usage():
    # logicalunit部分使用手册
    logicalunit = '''
    logicalunit(lun) {create(c)/modify(m)/delete(d)/show(s)/start/stop}'''

    logicalunit_create = '''
    logicalunit(lun) create(c) -target TARGET -disk DISK -host HOST[HOST...]'''

    logicalunit_delete = '''
    logicalunit(lun) delete(d) LOGICALUNIT'''

    logicalunit_add = '''
    logicalunit(lun) add(a) LOGICALUNIT host[HOST...]'''

    logicalunit_remove = '''
    logicalunit(lun) remove(r) LOGICALUNIT host[HOST...]'''

    logicalunit_show = '''
    logicalunit(lun) show(s)'''

    logicalunit_start = '''
    logicalunit(lun) start LOGICALUNIT'''

    logicalunit_stop = '''
    logicalunit(lun) stop LOGICALUNIT'''




class LogicalUnitCommands():

    def __init__(self):
        pass

    def setup_commands(self, parser):
        """
        Add commands for the PORTAL management:create,delete,modify,show
        """
        logicalunit_parser = parser.add_parser(
            'logicalunit', aliases=['lun'], help='logical unit operation',usage=Usage.logicalunit)
        self.logicalunit_parser = logicalunit_parser

        logicalunit_subp = logicalunit_parser.add_subparsers(dest='logicalunit')

        """
        Create LogicalUnit
        """
        p_create_logicalunit = logicalunit_subp.add_parser(
            'create',
            aliases='c',
            help='Create the iSCSI Logical Unit',
            usage = Usage.logicalunit_create)

        # add arguments of logicalunit create
        p_create_logicalunit.add_argument(
            '-tg',
            '-target',
            '--target',
            action='store',
            required=True,
            dest='target',
            help='Target'
        )

        p_create_logicalunit.add_argument(
            '-disk',
            '--disk',
            dest='disk',
            required=True,
            action='store',
            help='Disk')

        p_create_logicalunit.add_argument(
            '-host',
            '--host',
            dest='host',
            nargs='+',
            required=True,
            action='store',
            help='Host')

        self.p_create_logicalunit = p_create_logicalunit
        p_create_logicalunit.set_defaults(func=self.create)

        """
        Show Target
        """
        p_show_logicalunit = logicalunit_subp.add_parser(
            'show',
            aliases='s',
            help='Show the Logical Unit',
            usage=Usage.logicalunit_show)

        p_show_logicalunit.set_defaults(func=self.show)

        """
        Delete LogicalUnit
        """
        # add arguments of logicalunit delete
        p_delete_logicalunit = logicalunit_subp.add_parser(
            'delete', aliases='d', help='Delete the iSCSI Logical Unit',usage=Usage.logicalunit_delete)

        p_delete_logicalunit.add_argument(
            'logicalunit',
            action='store',
            help='Logical Unit Name')

        p_delete_logicalunit.set_defaults(func=self.delete)

        logicalunit_parser.set_defaults(func=self.print_logicalunit_help)


        """
        add initiator
        """
        p_add_initiators = logicalunit_subp.add_parser(
            'add',
            aliases='a',
            help='add the IQN',
            usage=Usage.logicalunit_add)


        p_add_initiators.add_argument(
            'logicalunit',
            help='logicalunit name')


        p_add_initiators.add_argument(
            'hosts',
            action='store',
            help='hosts',
            nargs='+')


        p_add_initiators.set_defaults(func=self.add)



        """
        remove initiator
        """
        p_remove_initiators = logicalunit_subp.add_parser(
            'remove',
            aliases='r',
            help='remove the IQN',
            usage=Usage.logicalunit_remove)


        p_remove_initiators.add_argument(
            'logicalunit',
            help='logicalunit name')


        p_remove_initiators.add_argument(
            'hosts',
            action='store',
            help='hosts',
            nargs='+',
            )

        p_remove_initiators.set_defaults(func=self.remove)

        """
        Start LogicalUnit
        """
        p_start_logicalunit = logicalunit_subp.add_parser(
            'start',
            help='Start the LogicalUnit',
            usage=Usage.logicalunit_start)

        p_start_logicalunit.add_argument(
            'logicalunit',
            help='logicalunit name')

        p_start_logicalunit.set_defaults(func=self.start)



        """
        Stop LogicalUnit
        """
        p_stop_logicalunit = logicalunit_subp.add_parser(
            'stop',
            help='Stop the LogicalUnit',
            usage=Usage.logicalunit_stop)

        p_stop_logicalunit.add_argument(
            'logicalunit',
            help='logicalunit name')


        p_stop_logicalunit.set_defaults(func=self.stop)



    @s.deco_record_exception
    def create(self, args):
        crm = ex.CRMData()
        crm.check()
        logicalunit = ex.LogicalUnit()
        logicalunit.create(args.target,args.disk,args.host)


    @s.deco_record_exception
    def show(self, args):
        crm = ex.CRMData()
        crm.check()
        logicalunit = ex.LogicalUnit()
        logicalunit.show()


    @s.deco_record_exception
    def delete(self, args):
        crm = ex.CRMData()
        crm.check()
        logicalunit = ex.LogicalUnit()
        logicalunit.delete(args.logicalunit)

    @s.deco_record_exception
    def add(self, args):
        crm = ex.CRMData()
        crm.check()
        logicalunit = ex.LogicalUnit()
        logicalunit.add(args.logicalunit,args.hosts)


    @s.deco_record_exception
    def remove(self, args):
        crm = ex.CRMData()
        crm.check()
        logicalunit = ex.LogicalUnit()
        logicalunit.remove(args.logicalunit, args.hosts)



    def start(self,args):
        crm = ex.CRMData()
        crm.check()
        logicalunit = ex.LogicalUnit()
        logicalunit.start(args.logicalunit)


    def stop(self,args):
        crm = ex.CRMData()
        crm.check()
        logicalunit = ex.LogicalUnit()
        logicalunit.stop(args.logicalunit)


    def print_logicalunit_help(self, *args):
        self.logicalunit_parser.print_help()
