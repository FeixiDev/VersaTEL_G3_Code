import argparse
import pickle
import sundry as sd
import execute as ex
import consts
from consts import ExitCode


class usage():
    # node部分使用手册
    node = '''
    node(n) {create(c)/modify(m)/delete(d)/show(s)}'''

    node_create = '''
    node(n) create(c) NODE -ip IP -nt NODETYPE'''

    node_delete = '''
    node(n) delete(d) NODE'''

    # 待完善
    node_modify = '''
    node(n) modify(m) NODE ...'''

    node_show = '''
    node(n) show(s) [NODE]'''


class NodeCommands():
    def __init__(self):
        self.logger = consts.glo_log()

    def setup_commands(self, parser):
        """
        Add commands for the node management:create,modify,delete,show
        """
        node_parser = parser.add_parser(
            'node',
            aliases='n',
            help='Management operations for node',
            usage=usage.node)

        self.node_parser = node_parser
        node_subp = node_parser.add_subparsers(dest='subargs_node')

        """
        Create LINSTOR Node
        """
        p_create_node = node_subp.add_parser(
            'create',
            aliases='c',
            help='Create the node',
            usage=usage.node_create)
        self.p_create_node = p_create_node
        # add the parameters needed to create the node
        p_create_node.add_argument(
            'node',
            metavar='NODE',
            action='store',
            help='Name of the new node, must match the nodes hostname')
        p_create_node.add_argument(
            '-ip',
            dest='ip',
            action='store',
            help='IP address of the new node, if not specified it will be resolved by the name.',
            required=True)
        p_create_node.add_argument(
            '-nt',
            dest='nodetype',
            action='store',
            help='node type: {Controller,Auxiliary,Combined,Satellite}',
            required=True)

        p_create_node.set_defaults(func=self.create)

        """
        Modify LINSTOR Node
        """
        pass

        """
        Delete LINSTOR Node
        """
        p_delete_node = node_subp.add_parser(
            'delete',
            aliases='d',
            help='Delete the node',
            usage=usage.node_delete)
        self.p_delete_node = p_delete_node
        p_delete_node.add_argument(
            'node',
            metavar='NODE',
            action='store',
            help=' Name of the node to remove')
        p_delete_node.add_argument(
            '-y',
            dest='yes',
            action='store_true',
            help='Skip to confirm selection',
            default=False)
        p_delete_node.set_defaults(func=self.delete)

        """
        Show LINSTOR Node
        """
        p_show_node = node_subp.add_parser(
            'show',
            aliases='s',
            help='Displays the node view',
            usage=usage.node_show)
        self.p_show_node = p_show_node
        p_show_node.add_argument(
            'node',
            metavar='NODE',
            help='Print information about the node in LINSTOR cluster',
            action='store',
            nargs='?',
            default=None)
        p_show_node.add_argument(
            '--no-color',
            dest='nocolor',
            help='Do not use colors in output.',
            action='store_true',
            default=False)
        p_show_node.set_defaults(func=self.show)

        node_parser.set_defaults(func=self.print_node_help)

    @sd.deco_record_exception
    def create(self, args):
        node = ex.Node()
        if args.node and args.nodetype and args.ip:
            node.create_node(args.node, args.ip, args.nodetype)
            return ExitCode.OK
        else:
            self.p_create_node.print_help()
            return ExitCode.ARGPARSE_ERROR

    @sd.deco_record_exception
    @sd.deco_comfirm_del('node')
    def delete(self, args):
        node = ex.Node()
        node.delete_node(args.node)

    @sd.deco_record_exception
    def show(self, args):
        node = ex.Node()
        if args.nocolor:
            if args.node:
                node.show_one_node(args.node, no_color='yes')
                return ExitCode.OK
            else:
                node.show_all_node(no_color='yes')
                return ExitCode.OK
        else:
            if args.node:
                node.show_one_node(args.node)
                return ExitCode.OK
            else:
                node.show_all_node()
                return ExitCode.OK

    def print_node_help(self, *args):
        self.node_parser.print_help()
