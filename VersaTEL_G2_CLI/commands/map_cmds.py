import pickle
import iscsi_json

import execute as ex
import sundry as sd
import consts


class MapCommands():

    def __init__(self):
        self.logger = consts.glo_log()

    def setup_commands(self, parser):
        """
        Add commands for the host group management:create,delete,show
        """
        map_parser = parser.add_parser(
            'map', aliases='m', help='map operation')
        map_subp = map_parser.add_subparsers(dest='map')
        self.map_parser = map_parser

        """
        Create map
        """
        p_create_map = map_subp.add_parser(
            'create',
            aliases='c',
            help='map create [map_name] -hg [hostgroup_name] -dg [diskgroup_name]')

        p_create_map.add_argument(
            'map', action='store', help='map_name')
        p_create_map.add_argument(
            '-hg', action='store', nargs='+', help='hostgroup_name')
        p_create_map.add_argument(
            '-dg', action='store', nargs='+', help='diskgroup_name')

        p_create_map.set_defaults(func=self.create)

        """
        Delete map
        """
        p_delete_map = map_subp.add_parser(
            'delete', aliases='d', help='map delete [map_name]')

        p_delete_map.add_argument(
            'map',
            action='store',
            help='map_name',
            default=None)

        p_delete_map.set_defaults(func=self.delete)

        """
        Show map
        """
        p_show_map = map_subp.add_parser(
            'show', aliases='s', help='map show / map show [map_name]')

        p_show_map.add_argument(
            'map',
            action='store',
            help='map show [map_name]',
            nargs='?',
            default='all')

        p_show_map.set_defaults(func=self.show)

        """
        Modify map
        """
        p_modify_map = map_subp.add_parser(
            'modify',
            aliases='m',
            help='map modify [hg] -a [hostgroup_name] -r [diskgroup_name]')

        p_modify_map.add_argument(
            'map',
            action='store',
            help='map_name')

        group = p_modify_map.add_mutually_exclusive_group()
        group.add_argument(
            '-hg',
            '--hostgroup',
            dest='hg',
            action='store_true',
            help='hg name'
        )

        group.add_argument(
            '-dg',
            '--diskgroup',
            dest='dg',
            action='store_true',
            help='dg name'
        )

        p_modify_map.add_argument(
            '-a',
            '--add',
            dest='add',
            action='store',
            help='host name',
            metavar='HOST|DISK',
            nargs='+')

        p_modify_map.add_argument(
            '-r',
            '--remove',
            dest='remove',
            action='store',
            help='host name',
            metavar='HOST|DISK',
            nargs='+')

        p_modify_map.set_defaults(func=self.modify)

        map_parser.set_defaults(func=self.print_map_help)

    @sd.deco_record_exception
    def create(self, args):
        map = ex.Map()
        map.create_map(args.map, args.hg, args.dg)

    @sd.deco_record_exception
    def show(self, args):
        map = ex.Map()
        if args.map == 'all' or args.map is None:
            map.show_all_map()
        else:
            map.show_spe_map(args.map)

    @sd.deco_record_exception
    def delete(self, args):
        map = ex.Map()
        map.delete_map(args.map)


    @sd.deco_record_exception
    def modify(self, args):
        map = ex.Map()

        if args.hg:
            if args.add:
                map.add_hg(args.map,args.add)

            if args.remove:
                map.remove_hg(args.map,args.remove)
        elif args.dg:
            if args.add:
                map.add_dg(args.map,args.add)

            if args.remove:
                map.remove_dg(args.map,args.remove)
        else:
            print('请执行一个要进行修改的资源类型-hg/-dg')


    def print_map_help(self, *args):
        self.map_parser.print_help()
