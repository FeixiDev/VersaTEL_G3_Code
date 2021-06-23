import argparse
import sys

import log
import sundry
import consts

from commands import (
    ReplayCommands,
    LVMCommands,
    NodeCommands,
    ResourceCommands,
    StoragePoolCommands,
    DiskCommands,
    DiskGroupCommands,
    HostCommands,
    HostGroupCommands,
    MapCommands,
    PortalCommands,
    TargetCommands,
    LogicalUnitCommands,
    SyncCommands
)




class MyArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None):
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            msg = ('unrecognized arguments: %s')
            self.error(msg % ' '.join(argv))
        return args

    def print_usage(self, file=None):
        logger = log.Log()
        cmd = ' '.join(sys.argv[1:])
        path = sundry.get_path()
        logger.write_to_log('DATA', 'INFO', 'cmd_input', path, {'valid':'1','cmd':cmd})
        logger.write_to_log('INFO', 'INFO', 'finish','', 'print usage')
        if file is None:
            file = sys.stdout
        self._print_message(self.format_usage(), file)

    def print_help(self, file=None):
        logger = log.Log()
        logger.write_to_log('INFO', 'INFO', 'finish','', 'print help')
        if file is None:
            file = sys.stdout
        self._print_message(self.format_help(), file)



class VtelCLI(object):
    """
    Vtel command line client
    """
    def __init__(self):
        self.parser = MyArgumentParser(prog="vtel")
        self.logger = log.Log()
        self._lvm_commands = LVMCommands()
        self._node_commands = NodeCommands()
        self._resource_commands = ResourceCommands()
        self._storagepool_commands = StoragePoolCommands()
        self._disk_commands = DiskCommands()
        self._diskgroup_commands = DiskGroupCommands()
        self._host_commands = HostCommands()
        self._hostgroup_commands = HostGroupCommands()
        self._map_commands = MapCommands()
        self._portal_commands = PortalCommands()
        self._target_commands = TargetCommands()
        self._logicalunit_commands = LogicalUnitCommands()
        self._sync_commands = SyncCommands()
        self._replay_commands = ReplayCommands(self.parser)
        self.setup_parser()


    def setup_parser(self):
        # parser = MyArgumentParser(prog="vtel")
        """
        Set parser vtel sub-parser
        """
        subp = self.parser.add_subparsers(metavar='',
                                     dest='subargs_vtel')


        self.parser.add_argument('-v',
                            '--version',
                            dest='version',
                            help='Show current version',
                            action='store_true')


        # parser_apply = subp.add_parser(
        #     'apply',
        #     help='Apply a configuration file',
        # )
        # parser_apply.add_argument(
        #     'file',
        #     help='Enter the name of the configuration file to be applied(yaml file)')



        parser_stor = subp.add_parser(
            'stor',
            help='Management operations for LINSTOR',
            add_help=True,
            formatter_class=argparse.RawTextHelpFormatter,
        )

        parser_iscsi = subp.add_parser(
            'iscsi',
            help='Management operations for iSCSI')

        self.parser_stor = parser_stor
        self.parser_iscsi = parser_iscsi

        subp_stor = parser_stor.add_subparsers(dest='subargs_stor',metavar='')
        subp_iscsi = parser_iscsi.add_subparsers(dest='subargs_iscsi',metavar='')

        parser_iscsi_show = subp_iscsi.add_parser('show',aliases=['s'],help='Show iSCSI resource information')
        parser_iscsi_show.add_argument('-n','--node', dest='node', help='Specify a node',nargs='+')
        parser_iscsi_show.add_argument('-t','--target', dest='target', help='Specify a target',nargs='+')
        parser_iscsi_show.add_argument('-i','--initiator', dest='initiator', help='Specify a initiators',nargs='+')
        parser_iscsi_show.set_defaults(func=self.iscsi_show)



        # add all subcommands and argument
        self._replay_commands.setup_commands(subp)

        self._lvm_commands.setup_commands(subp_stor)
        self._node_commands.setup_commands(subp_stor)
        self._resource_commands.setup_commands(subp_stor)
        self._storagepool_commands.setup_commands(subp_stor)

        self._disk_commands.setup_commands(subp_iscsi)
        self._diskgroup_commands.setup_commands(subp_iscsi)
        self._host_commands.setup_commands(subp_iscsi)
        self._hostgroup_commands.setup_commands(subp_iscsi)
        self._map_commands.setup_commands(subp_iscsi)
        self._portal_commands.setup_commands(subp_iscsi)
        self._target_commands.setup_commands(subp_iscsi)
        self._logicalunit_commands.setup_commands(subp_iscsi)

        self._sync_commands.setup_commands(subp_iscsi)

        parser_iscsi.set_defaults(func=self.print_iscsi_help)
        parser_stor.set_defaults(func=self.print_stor_help)
        self.parser.set_defaults(func=self.func_vtel)


    def func_vtel(self,args):
        if args.version:
            print(f'VersaTEL G2 {consts.VERSION}')
        else:
            self.parser.print_help()

    def print_iscsi_help(self, *args):
        self.parser_iscsi.print_help()

    def print_stor_help(self, *args):
        self.parser_stor.print_help()


    def parse(self): # 调用入口
        args = self.parser.parse_args()
        path = sundry.get_path()
        cmd = ' '.join(sys.argv[1:])
        if args.subargs_vtel:
            if args.subargs_vtel not in ['re', 'replay']:
                self.logger.write_to_log('DATA', 'INPUT', 'cmd_input', path, {'valid': '0', 'cmd': cmd})
        else:
            self.logger.write_to_log('DATA','INPUT','cmd_input', path, {'valid':'0','cmd':cmd})
        args.func(args)

    def iscsi_show(self,args):
        from execute import iscsi
        iscsi.ISCSI().show(args.node,args.target,args.initiator)



def main():
    try:
        cmd = VtelCLI()
        cmd.parse()
    except KeyboardInterrupt:
        sys.stderr.write("\nClient exiting (received SIGINT)\n")
    except PermissionError:
        sys.stderr.write("\nPermission denied (log file or other)\n")


if __name__ == '__main__':
    main()