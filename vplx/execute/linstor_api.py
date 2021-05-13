import sys
import json
import re
import time

try:
    import linstor
except ImportError:
    print('没有安装linstor环境')
    sys.exit(1)






class LinstorClientError(Exception):
    """
    Linstor exception with a message and exit code information
    """
    def __init__(self, msg, exit_code):
        self._msg = msg
        self._exit_code = exit_code

    @property
    def exit_code(self):
        return self._exit_code

    @property
    def message(self):
        return self._msg

    def __str__(self):
        return "Error: {msg}".format(msg=self._msg)

    def __repr__(self):
        return "LinstorError('{msg}', {ec})".format(msg=self._msg, ec=self._exit_code)



class ExitCode(object):
    OK = 0
    UNKNOWN_ERROR = 1
    ARGPARSE_ERROR = 2
    OBJECT_NOT_FOUND = 3
    OPTION_NOT_SUPPORTED = 4
    ILLEGAL_STATE = 5
    CONNECTION_ERROR = 20
    CONNECTION_TIMEOUT = 21
    UNEXPECTED_REPLY = 22
    API_ERROR = 10
    NO_SATELLITE_CONNECTION = 11



class ArgumentError(Exception):
    def __init__(self, msg):
        self._msg = msg

    @property
    def message(self):
        return self._msg


class DefaultState(object):
    @property
    def name(self):
        return 'default'

    @property
    def prompt(self):
        return 'LINSTOR'

    @property
    def terminate_on_error(self):
        return False



# class StateService(object):
#     def __init__(self, linstor_cli):
#         self._linstor_cli = linstor_cli
#         self._current_state = []
#
#     def enter_state(self, state, verbose):
#         already_interactive = bool(self._current_state)
#         self._current_state.append(state)
#         if not already_interactive:
#             return self._linstor_cli.run_interactive(verbose)
#         return ExitCode.OK
#
#     def pop_state(self):
#         if self._current_state:
#             self._current_state.pop()
#
#     def clear_state(self):
#         self._current_state = []
#
#     def has_state(self):
#         return bool(self._current_state)
#
#     def get_state(self):
#         return self._current_state[-1] if self._current_state else DefaultState()



class LinstorAPI():
    LINSTOR_CONF = '/etc/linstor/linstor-client.conf'

    def __init__(self):
        # self._linstor = None
        self._linstor_completer = None
        self.get_linstorapi()

    @classmethod
    def parse_size_str(cls, size_str, default_unit="GiB"):
        if size_str is None:
            return None
        m = re.match(r'(\d+)(\D*)', size_str)

        size = 0
        try:
            size = int(m.group(1))
        except AttributeError:
            sys.stderr.write('Size is not a valid number\n')
            sys.exit(ExitCode.ARGPARSE_ERROR)

        unit_str = m.group(2)
        if unit_str == "":
            unit_str = default_unit
        try:
            _, unit = linstor.SizeCalc.UNITS_MAP[unit_str.lower()]
        except KeyError:
            sys.stderr.write('"%s" is not a valid unit!\n' % unit_str)
            sys.stderr.write('Valid units: %s\n' % linstor.SizeCalc.UNITS_LIST_STR)
            sys.exit(ExitCode.ARGPARSE_ERROR)

        _, unit = linstor.SizeCalc.UNITS_MAP[unit_str.lower()]

        if unit != linstor.SizeCalc.UNIT_KiB:
            size = linstor.SizeCalc.convert_round_up(size, unit,
                                             linstor.SizeCalc.UNIT_KiB)

        return size



    @classmethod
    def get_replies_state(cls, replies):
        """
        :param list[ApiCallResponse] replies:
        :return:
        :rtype: (str, int)
        """
        errors = 0
        warnings = 0
        for reply in replies:
            if reply.is_error():
                errors += 1
            if reply.is_warning():
                warnings += 1
        if errors:
            return "Error"
        elif warnings:
            return "Warning"

        return "Ok"

    @staticmethod
    def get_volume_state(volume_states, volume_nr):
        for volume_state in volume_states:
            if volume_state.number == volume_nr:
                return volume_state
        return None



    # @staticmethod
    # def _dump_data(data):
    #     """
    #     序列化数据，必须是列表
    #     """
    #     assert (isinstance(data,list))
    #     return json.dumps([x.data_v0 for x in data], indent=2)


    def get_linstorapi(self,**kwargs):
        # if self._linstor:
        #     return self._linstor

        if self._linstor_completer:
            return self._linstor_completer

        # TODO also read config overrides
        # servers = ['linstor://localhost']
        with open(LinstorAPI.LINSTOR_CONF) as f:
            data = f.read()
            contrl_list = re.findall('controllers=(.*)',data)[0]
        servers = linstor.MultiLinstor.controller_uri_list(contrl_list)
        if 'parsed_args' in kwargs:
            cliargs = kwargs['parsed_args']
            servers = linstor.MultiLinstor.controller_uri_list(cliargs.controllers)
        if not servers:
            return None

        for server in servers:
            try:
                self._linstor_completer = linstor.Linstor(server)
                self._linstor_completer.connect()
                break
            except linstor.LinstorNetworkError as le:
                pass

        return self._linstor_completer



    def get_node(self,node=None):
        msg = self._linstor_completer.node_list(node)[0]
        time.sleep(0)
        lst = []

        for node in msg.nodes:
            active_ip = ""
            for net_if in node.net_interfaces:
                if net_if.is_active and net_if.stlt_port:
                    active_ip = net_if.address + ":" + str(net_if.stlt_port) + " (" + net_if.stlt_encryption_type + ")"

            lst.append({'Node':node.name,
                        'NodeType':node.type,
                        'Addresses':active_ip,
                        'State':node.connection_status})
        return lst



    def get_storagepool(self,node=None,sp=None):
        """

        :param node: list,用于过滤
        :param sp: list,用于过滤
        :return:
        """
        msg = self._linstor_completer.storage_pool_list(node,sp)[0]
        time.sleep(0)
        lst = []
        errors = []
        for storpool in msg.storage_pools:
            driver_device = storpool.properties['StorDriver/StorPoolName'] if storpool.properties else ''
            free_capacity = ""
            total_capacity = ""
            if not storpool.is_diskless() and storpool.free_space is not None:
                free_capacity = linstor.SizeCalc.approximate_size_string(storpool.free_space.free_capacity)
                total_capacity = linstor.SizeCalc.approximate_size_string(storpool.free_space.total_capacity)


            state_str = self.get_replies_state(storpool.reports)
            lst.append({'StoragePool':storpool.name,
                        'Node':storpool.node_name,
                        'Driver':storpool.provider_kind,
                        'PoolName':driver_device,
                        'FreeCapacity':free_capacity,
                        'TotalCapacity':total_capacity,
                        'CanSnapshots':storpool.supports_snapshots(),
                        'State':state_str
                        })

            for error in storpool.reports:
                if error not in errors:
                    errors.append(error)

        if errors:
            pass
            # print(errors)

        return lst



    def get_resource(self,node=None,storagepool=None,resource=None):
        msg = self._linstor_completer.volume_list(node,storagepool,resource)[0]
        time.sleep(0)
        lst = []
        rsc_state_lkup = {x.node_name + x.name: x for x in msg.resource_states}

        for rsc in msg.resources:
            rsc_state = rsc_state_lkup.get(rsc.node_name + rsc.name)
            rsc_usage = ""
            if rsc_state and rsc_state.in_use is not None:
                if rsc_state.in_use:
                    rsc_usage = 'Inused'
                else:
                    rsc_usage = "Unused"

            for vlm in rsc.volumes:
                vlm_state = self.get_volume_state(
                    rsc_state.volume_states,
                    vlm.number
                ) if rsc_state else None

                vlm_drbd_data = vlm.drbd_data
                mirror_num = str(vlm_drbd_data.drbd_volume_definition.minor) if vlm_drbd_data else ""

                lst.append({'Node':rsc.node_name,
                            'Resource':rsc.name,
                            'StoragePool':vlm.storage_pool_name,
                            'VolNr':str(vlm.number),
                            'MinorNr':mirror_num,
                            'DeviceName':vlm.device_path,
                            'Allocated':linstor.SizeCalc.approximate_size_string(vlm.allocated_size) if vlm.allocated_size else "",
                            'InUse':rsc_usage,
                            'State':vlm_state.disk_state,
                            })
        return lst





    def create_rd(self,name):
        """

        :param name:
        :return: 返回的对象，属性ret_code为正整数，代表执行成功，负数代表执行失败
        """
        msg = self._linstor_completer.resource_dfn_create(name)[-1]
        result_code = 0 if msg.ret_code > 0 else 1
        output = msg.cause if msg.cause else msg.message
        return {'sts': result_code, 'rst':output}


    def create_vd(self,name,size_str):
        """

        :param name: resource denifition name
        :param size: str
        :return:
        """
        size_int_KB = LinstorAPI.parse_size_str(size_str)
        msg = self._linstor_completer.volume_dfn_create(name,size_int_KB)[-1]
        result_code = 0 if msg.ret_code > 0 else 1
        output = msg.cause if msg.cause else msg.message
        return {'sts': result_code, 'rst':output}

    def delete_rd(self,name):
        msg = self._linstor_completer.resource_dfn_delete(name)[-1]
        result_code = 0 if msg.ret_code > 0 else 1
        output = msg.cause if msg.cause else msg.message
        return {'sts': result_code, 'rst':output}


    def delete_vd(self,name):
        msg = self.get_linstorapi()
        result_code = 0 if msg.ret_code > 0 else 1
        output = msg.cause if msg.cause else msg.message
        return {'sts': result_code, 'rst':output}



    def create_resource(self,node,resource_definition,storage_pool=None,diskless=False):
        """
        单个resource的创建,
        :param node:
        :param resource_definition:
        :param storage_pool:
        :param diskless:
        :return:
        """
        # 创建diskless时才不用执行存储池，其他情况需要指定存储池
        # if not diskless:
        #     if not storage_pool:
        #         raise TypeError

        rscs = [
            linstor.ResourceData(
                node,
                resource_definition,
                diskless,
                storage_pool
            )
        ]

        msg = self._linstor_completer.resource_create(rscs=rscs)[-1]

        # msg_all = self._linstor_completer.resource_create(rscs=rscs)
        # print(msg_all)
        #
        # if len(msg_all) == 1:
        #     msg = msg_all[0]
        # else:
        #     msg = msg_all[-1]
        #     flag = f"Resource '{resource_definition}' on '{node}' ready"
        #     if msg.message != flag:
        #         return {'sts':1,'rst':'unknow'}

        result_code = 0 if msg.ret_code > 0 else 1
        output = msg.cause if msg.cause else msg.message
        return {'sts': result_code, 'rst':output}


    def delete_resource(self,node,resource):
        msg = self._linstor_completer.resource_delete(node, resource)[-1]
        # if msg_all[-1].is_success:
        #     print('111')
        #     msg = msg_all[-1]
        # else:
        #     msg = msg_all[0]

        result_code = 0 if msg.ret_code > 0 else 1
        output = msg.cause if msg.cause else msg.message
        return {'sts': result_code, 'rst':output}

        # for i in msg:
        #     print(i)
        # result_code = 0 if msg[0].ret_code > 0 else 1
        # output = msg[0].cause if msg[0].cause else msg[0].message
        # return {'sts': result_code, 'rst':output}


    def create_sp(self,name,node,driver,driver_pool):
        """

        :param name:storage pool name
        :param node:
        :param driver: LVM/LVM_THIN/DISKLESS
        :param driver_pool:VG/Thin LV
        :return:
        """

        try:
            msg = self._linstor_completer.storage_pool_create(
                node,
                name,
                driver,
                driver_pool
            )
        except linstor.LinstorError as e:
            raise ArgumentError(e.message)

        result_code = 0 if msg.ret_code > 0 else 1
        output = msg.cause if msg.cause else msg.message
        return {'sts': result_code, 'rst':output}



    def delete_sp(self,node_name, storage_pool_name):
        msg = self._linstor_completer.storage_pool_delete(
            node_name,
            storage_pool_name
        )[-1]

        result_code = 0 if msg.ret_code > 0 else 1
        output = msg.cause if msg.cause else msg.message
        return {'sts': result_code, 'rst':output}






    # def create_resource_all(self,list_node,resource_definition,storage_pool=None,diskless=False):
    #     """
    #     需要先创建rd，vd
    #     :param list_node:
    #     :param resource_definition:
    #     :param storage_pool:
    #     :param diskless:
    #     :return:
    #     """
    #     rscs = [
    #         linstor.ResourceData(
    #             node,
    #             resource_definition,
    #             diskless,
    #             storage_pool
    #         )
    #         for node in list_node
    #     ]
    #     msg = self._linstor_completer.resource_create(rscs=rscs)
    #
    #     for i in msg:
    #         result_code = 0 if i.ret_code > 0 else 1
    #         output = i.cause if i.cause else i.message
    #         print({'sts': result_code, 'rst':output})









#
# def run():
#     try:
#         linstor_ = LinstorAPI()
#         try:
#             print(linstor_.get_resource())
#             # print(linstor_.create_rd('res_b'))
#             # print(linstor_.create_vd('res_b','10M'))
#             # print(linstor_.create_resource('ubuntu','res_b'))
#             # print(linstor_.create_sp('pool_b','ubuntu','LVM','drbdpool'))
#             # print(linstor_.delete_sp('ubuntu','pool_b'))
#             # print(linstor_.delete_resource('ubuntu','res_b'))
#         except Exception as E:
#         # linstor_.delete_rd('res_l')
#             print(E)
#         finally:
#             import subprocess
#             # subprocess.run('linstor rd d res_a',shell=True)
#             # subprocess.run('linstor rd c res_a', shell=True)
#         # linstor_.get_storagepool()
#         #     linstor_.delete_resource(['ubuntu', 'vince2'], 'res_a')
#
#     except linstor.LinstorNetworkError as le:
#         print(le)






if __name__ == "__main__":
    # pass
    # run()
    pass