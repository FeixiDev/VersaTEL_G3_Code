import argparse
import sys
import os
import pickle

import linstordb
import log
import sundry
import iscsi_json
from commands import (
    NodeCommands,
    ResourceCommands,
    StoragePoolCommands,
    DiskCommands,
    DiskGroupCommands,
    HostCommands,
    HostGroupCommands,
    MapCommands
)

#-m:
class MyArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None):
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            msg = ('unrecognized arguments: %s')
            logger = log.Log()
            collocter = log.Collector()
            username = collocter.get_username()
            transaction_id = sundry.get_transaction_id()
            logger.add_log(username,'args_error',transaction_id,(' '.join(sys.argv)),'',(msg % ' '.join(argv)))
            self.error(msg % ' '.join(argv))
        return args


class VtelCLI(object):
    """
    Vtel command line client
    """


    def __init__(self):
        self._node_commands = NodeCommands()
        self._resource_commands = ResourceCommands()
        self._storagepool_commands = StoragePoolCommands()
        self._disk_commands = DiskCommands()
        self._diskgroup_commands = DiskGroupCommands()
        self._host_commands = HostCommands()
        self._hostgroup_commands = HostGroupCommands()
        self._map_commands = MapCommands()
        self._parser = self.setup_parser()

    def setup_parser(self):
        parser = MyArgumentParser(prog="vtel")
        """
        Set parser vtel sub-parser
        """
        #parser.add_argument('--version','-v',action='version',version='%(prog)s ' + VERSION + '; ')

        subp = parser.add_subparsers(title='subcommands',
                                     dest='subargs_vtel')

        parser_stor = subp.add_parser(
            'stor',
            help='Management operations for LINSTOR',
            add_help=False,
            formatter_class=argparse.RawTextHelpFormatter,
        )

        # add parameters to interact with the GUI
        parser_stor.add_argument(
            '-gui',
            dest='gui',
            action='store_true',
            help=argparse.SUPPRESS,
            default=False)

        parser_iscsi = subp.add_parser(
            'iscsi',
            help='Management operations for iSCSI',
            add_help=False)


        parser_iscsi.add_argument(
            '-gui',
            dest='gui',
            action='store_true',
            help=argparse.SUPPRESS,
            default=False)

        self.parser_stor = parser_stor
        self.parser_iscsi = parser_iscsi
        # Set the binding function of stor
        parser_stor.set_defaults(func=self.send_database)
        parser_iscsi.set_defaults(func=self.send_json)
        # Set the binding function of iscsi
        parser_iscsi.set_defaults(func=self.print_iscsi_help)

        subp_stor = parser_stor.add_subparsers(dest='subargs_stor')
        subp_iscsi = parser_iscsi.add_subparsers(dest='subargs_iscsi')

        # add all subcommands and argument
        self._node_commands.setup_commands(subp_stor)
        self._resource_commands.setup_commands(subp_stor)
        self._storagepool_commands.setup_commands(subp_stor)

        self._disk_commands.setup_commands(subp_iscsi)
        self._diskgroup_commands.setup_commands(subp_iscsi)
        self._host_commands.setup_commands(subp_iscsi)
        self._hostgroup_commands.setup_commands(subp_iscsi)
        self._map_commands.setup_commands(subp_iscsi)

        parser.set_defaults(func=parser.print_help)

        return parser

    # When using the parameter '-gui', send the database through the socket
    def send_database(self, args):
        if args.gui:
            db = linstordb.LINSTORDB()
            data = pickle.dumps(db.data_base_dump())
            sundry.send_via_socket(data)
        else:
            self.parser_stor.print_help()

    def send_json(self, args):
        js = iscsi_json.JSON_OPERATION()
        if args.json in ['json']:
            data = js.read_data_json()
            data_pickled = pickle.dumps(data)
            sundry.send_via_socket(data_pickled)
        else:
            self.parser_iscsi.print_help()

    def print_iscsi_help(self, args):
        self.parser_iscsi.print_help()


    def run(self):
        pass


    def parse(self):
        args = self._parser.parse_args()
        if args.subargs_vtel:
            args.func(args)
        else:
            self._parser.print_help()


def main():
    try:
        cmd = VtelCLI()
        cmd.parse()
    except KeyboardInterrupt:
        sys.stderr.write("\nClient exiting (received SIGINT)\n")


if __name__ == '__main__':
    main()
