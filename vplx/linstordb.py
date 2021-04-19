# coding:utf-8
import execute as ex
import sundry as s
import sqlite3

import datetime
import scheduler

class DataIsEmpty(Exception):
    pass


queries = {
    'SELECT': 'SELECT %s FROM %s WHERE %s',
    'SELECT_ALL': 'SELECT %s FROM %s',
    'SELECT_COUNT': 'SELECT COUNT(%s) FROM %s WHERE %s',
    'INSERT': 'INSERT INTO %s VALUES(%s)',
    'UPDATE': 'UPDATE %s SET %s WHERE %s',
    'DELETE': 'DELETE FROM %s where %s',
    'DELETE_ALL': 'DELETE FROM %s',
    'CREATE_TABLE': 'CREATE TABLE IF NOT EXISTS %s(%s)',
    'DROP_TABLE': 'DROP TABLE if exists %s'}


class Database():

    def __init__(self, data_file):
        self.db = sqlite3.connect(data_file, check_same_thread=False)
        self.data_file = data_file

    def free(self, cursor):
        cursor.close()

    # def write(self, query, values=None):
    #     cursor = self.db.cursor()
    #     if values is not None:
    #         cursor.execute(query, list(values))
    #     else:
    #         cursor.execute(query)
    #     self.db.commit()
    #     return cursor

    def read(self, query, values=None):
        cursor = self.db.cursor()
        if values is not None:
            cursor.execute(query, list(values))
        else:
            cursor.execute(query)
        return cursor

    def fet_all(self, cursor):
        return cursor.fetchall()

    def fet_one(self, cursor):
        return cursor.fetchone()

    def select(self, tables, *args, **kwargs):
        vals = ','.join([l for l in args])
        locs = ','.join(tables)
        conds = ' and '.join(['%s=?' % k for k in kwargs])
        subs = [kwargs[k] for k in kwargs]
        query = queries['SELECT'] % (vals, locs, conds)
        return self.read(query, subs)

    def select_all(self, tables, *args):
        vals = ','.join([l for l in args])
        locs = ','.join(tables)
        query = queries['SELECT_ALL'] % (vals, locs)
        return self.read(query)

    def select_count(self, tables, *args, **kwargs):
        vals = ','.join([l for l in args])
        locs = ','.join(tables)
        conds = ' and '.join(['%s=?' % k for k in kwargs])
        subs = [kwargs[k] for k in kwargs]
        query = queries['SELECT_COUNT'] % (vals, locs, conds)
        cursor = self.read(query, subs)
        return cursor.fetchone()[0]

    # def insert(self, table_name, *args):
    #     values = ','.join(['?' for l in args])
    #     query = queries['INSERT'] % (table_name, values)
    #     return self.write(query, args)

    # def update(self, table_name, set_args, **kwargs):
    #     updates = ','.join(['%s=?' % k for k in set_args])
    #     conds = ' and '.join(['%s=?' % k for k in kwargs])
    #     vals = [set_args[k] for k in set_args]
    #     subs = [kwargs[k] for k in kwargs]
    #     query = queries['UPDATE'] % (table_name, updates, conds)
    #     return self.write(query, vals + subs)
    #
    # def delete(self, table_name, **kwargs):
    #     conds = ' and '.join(['%s=?' % k for k in kwargs])
    #     subs = [kwargs[k] for k in kwargs]
    #     query = queries['DELETE'] % (table_name, conds)
    #     return self.write(query, subs)
    #
    # def delete_all(self, table_name):
    #     query = queries['DELETE_ALL'] % table_name
    #     return self.write(query)
    #
    #
    # def drop_table(self, table_name):
    #     query = queries['DROP_TABLE'] % table_name
    #     self.free(self.write(query))

    def disconnect(self):
        self.db.close()


class LinstorDB(Database):
    """
    Get the output of LINSTOR through the command, use regular expression to get and process it into a list,
    and insert it into the newly created memory database.
    """

    # 连接数据库,创建光标对象

    def __init__(self):
        super().__init__(':memory:')
        self.cur = self.db.cursor()
    def build_table(self, type='linstor'):
        # LINSTOR表
        crt_sptb_sql = '''
            create table if not exists storagepooltb(id integer primary key,
                StoragePool varchar(20),
                Node varchar(20),
                Driver varchar(20),
                PoolName varchar(20),
                FreeCapacity varchar(20),
                TotalCapacity varchar(20),
                SupportsSnapshots varchar(20),
                State varchar(20)
                );'''

        crt_rtb_sql = '''
            create table if not exists resourcetb(
                id integer primary key,
                Node varchar(20),
                Resource varchar(20),
                Storagepool varchar(20),
                VolumeNr varchar(20),
                MinorNr varchar(20),
                DeviceName varchar(20),
                Allocated varchar(20),
                InUse varchar(20),
                State varchar(20)
                );'''

        crt_ntb_sql = '''
            create table if not exists nodetb(
                id integer primary key,
                Node varchar(20),
                NodeType varchar(20),
                Addresses varchar(20),
                State varchar(20)
                );'''

        crt_vgtb_sql = '''
                create table if not exists vgtb(
                id integer primary key,
                VG varchar(20),
                VSize varchar(20),
                VFree varchar(20)
                );'''

        crt_thinlvtb_sql = '''
                create table if not exists thinlvtb(
                id integer primary key,
                LV varchar(20),
                VG varchar(20),
                LSize varchar(20)
                );'''

        self.cur.execute(crt_ntb_sql)
        self.cur.execute(crt_rtb_sql)
        self.cur.execute(crt_sptb_sql)
        if type == 'all':
            self.cur.execute(crt_vgtb_sql)
            self.cur.execute(crt_thinlvtb_sql)
            self.insert_lvm_data()
        self.insert_linstor_data()
        self.db.commit()

    def insert_lvm_data(self):
        insert_vgtb_sql = '''insert into vgtb(VG,VSize,VFree)values(?,?,?)'''

        insert_thinlvtb_sql = '''insert into thinlvtb(LV,VG,LSize)values(?,?,?)'''
        lvm = ex.LVM()
        vg = lvm.refine_vg()
        thinlv = lvm.refine_thinlv()
        self.insert_data(insert_vgtb_sql, vg, 'vgtb')
        self.insert_data(insert_thinlvtb_sql, thinlv, 'thinlvtb')

    def insert_linstor_data(self):
        insert_stb_sql = '''
            insert into storagepooltb
            (
                StoragePool,
                Node,
                Driver,
                PoolName,
                FreeCapacity,
                TotalCapacity,
                SupportsSnapshots,
                State
                )
            values(?,?,?,?,?,?,?,?)
            '''

        insert_rtb_sql = '''
            insert into resourcetb
            (
                Node,
                Resource,
                StoragePool,
                VolumeNr,
                MinorNr,
                DeviceName,
                Allocated,
                InUse,
                State
                )
            values(?,?,?,?,?,?,?,?,?)
            '''

        insert_ntb_sql = '''insert into nodetb(Node,NodeType,Addresses,State)values(?,?,?,?)'''


        # linstor = ex.Linstor()
        # node = linstor.get_linstor_data('linstor --no-color --no-utf8 n l')
        # res = linstor.get_linstor_data('linstor --no-color --no-utf8 r lv')
        # sp = linstor.get_linstor_data('linstor --no-color --no-utf8 sp l')
        # self.insert_data(insert_ntb_sql, node, 'nodetb')
        # self.insert_data(insert_rtb_sql, res, 'resourcetb')
        # self.insert_data(insert_stb_sql, sp, 'storagepooltb')

        data = scheduler.Scheduler().get_linstor_data()
        self.insert_data2(insert_ntb_sql, data['node_data'], 'nodetb')
        self.insert_data2(insert_rtb_sql, data['res_data'], 'resourcetb')
        self.insert_data2(insert_stb_sql, data['sp_data'], 'storagepooltb')





    @s.deco_db_insert
    def insert_data(self, sql, list_data, tablename):
        for i in range(len(list_data)):
            if not list_data[i]:
                s.prt_log('数据错误，无法插入数据表', 2)
            self.cur.execute(sql, list_data[i])


    @s.deco_db_insert
    def insert_data2(self, sql, list_data, tablename):
        for dict in list_data:
            list_data = [x for x in dict.values()]
            self.cur.execute(sql, list_data)




class CollectData(LinstorDB):
    """
    Provide a data interface to retrieve specific data in the LINSTOR database.
    """

    def __init__(self):
        super().__init__()
        self.build_table()

    # resource
    def _get_resource(self):
        res_used = []
        result = []

        res_all = self.fet_all(self.select_all(['resourcetb'], 'DISTINCT Resource', 'Allocated', 'DeviceName', 'InUse'))
        in_use = self.fet_all(
            self.select(['resourcetb'], 'DISTINCT Resource', 'Allocated', 'DeviceName', 'InUse', InUse='InUse'))

        for i in in_use:
            res_used.append(i[0])

        for res in res_all:
            if res[3] == 'InUse':
                result.append(res)
            if res[0] not in res_used and res[3] == 'Unused':
                result.append(res)
        return result

    def get_all_node(self):
        data_list = []
        node_data = self.fet_all(self.select_all(['nodetb'], 'Node', 'NodeType', 'Addresses', 'State'))
        for i in node_data:
            node, node_type, addr, status = i
            res_num = self.select_count(['resourcetb'], 'Resource', Node=node)
            sp_num = self.select_count(['storagepooltb'], 'Node', Node=node)
            list_one = [node, node_type, res_num, sp_num, addr, status]
            data_list.append(list_one)
        self.cur.close()
        return data_list

    # 置顶文字
    def get_node_info(self, node):
        n = self.fet_one(self.select(['nodetb'], 'Node', 'NodeType', 'Addresses', 'State', Node=node))
        if n:
            node, node_type, addr, status = n
            res_num = self.select_count(['resourcetb'], 'Resource', Node=node)
            sp_num = self.select_count(['storagepooltb'], 'Node', Node=node)
            list = [node, node_type, res_num, sp_num, addr, status]
            return tuple(list)
        else:
            return []

    def get_one_node(self, node):
        date_list = []
        res_data = self.fet_all(
            self.select(['resourcetb'], 'Resource', 'StoragePool', 'Allocated', 'DeviceName', 'InUse', 'State',
                        Node=node))
        for res_data_one in res_data:
            date_list.append(list(res_data_one))
        return date_list

    def get_sp_in_node(self, node):
        data_list = []
        sp_data = self.fet_all(
            self.select_all(['storagepooltb'], 'StoragePool', 'Node', 'Driver', 'PoolName', 'FreeCapacity',
                            'TotalCapacity', 'SupportsSnapshots', 'State'))
        for i in sp_data:
            sp_name, node_name, driver, pool_name, free_size, total_size, snapshots, status = i
            res_num = self.select_count(['resourcetb'], 'Resource', Node=node_name, StoragePool=sp_name)
            if node_name == node:
                list_one = [
                    sp_name,
                    node_name,
                    res_num,
                    driver,
                    pool_name,
                    free_size,
                    total_size,
                    snapshots,
                    status]
                data_list.append(list_one)
        self.cur.close()
        return data_list

    def get_all_res(self):
        data_list = []
        for i in self._get_resource():
            if i[1]:  # 过滤size为空的resource
                resource, size, device_name, used = i
                mirror_way = self.select_count(['resourcetb'], 'Resource', Resource=resource)
                list_one = [resource, mirror_way, size, device_name, used]
                data_list.append(list_one)
        self.cur.close()
        return data_list

    # 置顶文字
    def get_res_info(self, resource):
        list_one = []
        for i in self._get_resource():
            if i[0] == resource:
                if i[1]:
                    resource, size, device_name, used = i
                    mirror_way = self.select_count(['resourcetb'], 'Resource', Resource=resource)
                    list_one = [resource, mirror_way, size, device_name, used]
        return tuple(list_one)

    def get_one_res(self, resource):
        data_list = []
        res_data = self.fet_all(self.select(['resourcetb'], 'Node', 'StoragePool', 'InUse', 'State', Resource=resource))
        for res_one in res_data:
            node_name, sp_name, drbd_role, status = list(res_one)
            if drbd_role == u'InUse':
                drbd_role = u'primary'
            elif drbd_role == u'Unused':
                drbd_role = u'secondary'
            list_one = [node_name, sp_name, drbd_role, status]
            data_list.append(list_one)
        self.cur.close()
        return data_list

    def get_all_sp(self):
        date_list = []
        sp_data = self.fet_all(
            self.select_all(['storagepooltb'], 'StoragePool', 'Node', 'Driver', 'PoolName', 'FreeCapacity',
                            'TotalCapacity', 'SupportsSnapshots', 'State'))
        for i in sp_data:
            sp_name, node_name, driver, pool_name, free_size, total_size, snapshots, status = i
            res_num = self.select_count(['resourcetb'], 'Resource', Node=node_name, StoragePool=sp_name)
            list_one = [
                sp_name,
                node_name,
                res_num,
                driver,
                pool_name,
                free_size,
                total_size,
                snapshots,
                status]
            date_list.append(list_one)
        self.cur.close()
        return date_list

    def get_sp_info(self, sp):
        node_num = self.select_count(['storagepooltb'], 'Node', StoragePool=sp)
        node = self.fet_all(self.select(['storagepooltb'], 'Node', StoragePool=sp))
        if len(node) == 1:
            names = node[0][0]
        else:
            names = [n[0] for n in node]
        return (node_num, sp, names)

    def get_one_sp(self, sp):
        date_list = []
        res_data = self.select(['resourcetb'], 'Resource', 'Allocated', 'DeviceName', 'InUse', 'State', StoragePool=sp)
        for res in res_data:
            res_name, size, device_name, used, status = res
            list_one = [res_name, size, device_name, used, status]
            date_list.append(list_one)
        self.cur.close()
        return date_list
