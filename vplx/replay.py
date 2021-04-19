import re
import os
import sqlite3
import threading
import prettytable
import traceback
from tempfile import NamedTemporaryFile
from io import StringIO
import consts

# LOG_PATH = '/var/log/vtel/'
LOG_PATH = "../vplx/"
LOG_FILE_NAME = 'cli.log'
OUTPUT_FILE = False


def _is_file_exist(strfile):
    # 检查文件是否存在
    return os.path.isfile(strfile)


def _get_log_files(base_log_file):
    list_file = []
    all_file = (os.listdir(LOG_PATH))
    for file in all_file:
        if base_log_file in file:
            list_file.append(file)
    list_file.sort(reverse=True)
    return list_file


def _read_log_files():
    all_data = ''
    if not _is_file_exist(LOG_PATH+LOG_FILE_NAME):
        print('no log file')
        return
    for file in _get_log_files(LOG_FILE_NAME):
        f = open('./' + file)
        data = f.read()
        all_data+=data
        f.close()
    return all_data

def _get_log_data():
    re_ = re.compile(r'\[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?\]?)\]\|',
                     re.DOTALL)
    all_log_data = _read_log_files()
    all_data = re_.findall(all_log_data)
    return all_data





class LogDB():
    _instance_lock = threading.Lock()
    transaction_id = ''
    oprt_id = ''
    id_pointer = 0


    def __init__(self):
        if not hasattr(self, 'con'):
            self.con = sqlite3.connect("logDB.db", check_same_thread=False)
            self.cur = self.con.cursor()
            self._drop_table()
            self._create_table()
            self._insert_log_data()


    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            with LogDB._instance_lock:
                if not hasattr(cls, '_instance'):
                    LogDB._instance = super().__new__(cls)

                    # LogDB._instance.con = sqlite3.connect("logDB.db", check_same_thread=False)
                    # LogDB._instance.cur = LogDB._instance.con.cursor()
                    # LogDB._instance._create_table()
                    # LogDB._instance._drop_table()

        return LogDB._instance

    def insert_data(self, data):
        insert_sql = '''
        insert into logtable
        (
            time,
            transaction_id,
            username,
            type1,
            type2,
            describe1,
            describe2,
            data
            )
        values(?,?,?,?,?,?,?,?)
        '''
        self.cur.execute(insert_sql, data)

    def _create_table(self):
        create_table_sql = '''
        create table if not exists logtable(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time DATE(30),
            transaction_id varchar(20),
            username varchar(20),
            type1 TEXT,
            type2 TEXT,
            describe1 TEXT,
            describe2 TEXT,
            data TEXT
            );'''
        self.cur.execute(create_table_sql)
        self.con.commit()

    def _drop_table(self):
        drop_table_sql = "DROP TABLE if exists logtable"
        self.cur.execute(drop_table_sql)
        self.con.commit()

    def _insert_log_data(self):
        all_data = _get_log_data()
        for data in all_data:
            self.insert_data(data)
        self.con.commit()

    # 获取表单行数据的通用方法
    def sql_fetch_one(self, sql):
        self.cur.execute(sql)
        data_set = self.cur.fetchone()
        if data_set:
            if len(data_set) == 1:
                return data_set[0]
            else:
                return data_set
        else:
            return data_set

    # 获取表全部数据的通用方法
    def sql_fetch_all(self, sql):
        cur = self.cur
        cur.execute(sql)
        date_set = cur.fetchall()
        return list(date_set)


    def get_cmd_via_tid(self):
        sql = f"SELECT data FROM logtable WHERE describe1 = 'cmd_input' and transaction_id = '{LogDB.transaction_id}'"
        result = self.sql_fetch_one(sql)
        if result:
            result = eval(result)
            return {'tid':self.transaction_id, 'valid':result['valid'],'cmd':result['cmd']}


    def get_cmd_via_time(self, start_time, end_time):
        sql = f"SELECT transaction_id,data FROM logtable WHERE describe1 = 'cmd_input' and time >= '{start_time}' and time <= '{end_time}'"
        all_data = self.sql_fetch_all(sql)
        result_list = []
        for i in all_data:
            tid, user_input = i
            user_input = eval(user_input)
            dict_one = {'tid':tid, 'valid':user_input['valid'], 'cmd':user_input['cmd']}
            result_list.append(dict_one)
        return result_list

    # 需要修改
    def get_all_cmd(self):
        sql = "SELECT transaction_id,data FROM logtable WHERE describe1 = 'cmd_input'"
        all_data = self.sql_fetch_all(sql)
        result_list = []
        for i in all_data:
            tid, user_input = i
            user_input = eval(user_input)
            dict_one = {'tid':tid, 'valid':user_input['valid'], 'cmd':user_input['cmd']}
            result_list.append(dict_one)
        return result_list


    def get_id(self, string):
        sql = f"SELECT time,id,data FROM logtable WHERE describe1 = '{string}' and type2 = 'STR' and id > {LogDB.id_pointer} and transaction_id = '{LogDB.transaction_id}'"
        result = self.sql_fetch_one(sql)
        if result:
            time,db_id,oprt_id = result
            LogDB.id_pointer = db_id
            LogDB.oprt_id = oprt_id
            return {'time':time,'db_id':db_id,'oprt_id':oprt_id}
        else:
            return {'time':'','db_id':'','oprt_id':''}


    def get_oprt_result(self):
        sql = f"SELECT time,data FROM logtable WHERE type1 = 'DATA' and describe2 = '{LogDB.oprt_id}'"
        # sql = f"SELECT time,data FROM logtable WHERE type1 = 'DATA' and type2 = 'cmd' and describe2 = '{oprt_id}'"
        if self.oprt_id:
            result = self.sql_fetch_one(sql)
            if result:
                time, data = self.sql_fetch_one(sql)
                return {'time': time, 'result': data}
            else:
                return {'time':'','result':''}
        else:
            return {'time': '', 'result': ''}


    def get_anwser(self):
        sql = f"SELECT time,data FROM logtable WHERE transaction_id = '{self.transaction_id}' and describe2 = 'confirm deletion'"
        result = self.sql_fetch_one(sql)
        if result:
            return result
        else:
            return ('','')

    def get_cmd_output(self):
        sql = f"SELECT time,id,data FROM logtable WHERE describe2 = 'output' and type1 = 'INFO' and transaction_id = '{self.transaction_id}' and id > {self.id_pointer}"
        result = self.sql_fetch_one(sql)
        if result:
            time,db_id,output = result
            return {'time':time,'db_id':db_id,'output':output}
        else:
            return {'time':'','db_id':'','output':''}

    @staticmethod
    def reset_id():
        LogDB.transaction_id = ''
        LogDB.oprt_id = ''
        LogDB.id_pointer = 0




class Replay():
    """
    目前的replay模式，与argparser模块耦合，需要调用到argparser的解析器进行绑定函数的执行
    """
    switch = False
    mode = 'NORMAL'# or 'LITE'
    replay_data = []
    num = 1
    specific_data = {}
    replay_all = False

    def __init__(self):
        pass

    def print_(self,str):
        if Replay.replay_all:
            self.tempfile.write(f'{str}\n')
        else:
            print(str)


    def make_table(self,title,list_data):
        list_header = ["Time", "Operation", "Output/Return Value"]
        table = prettytable.PrettyTable()
        table.title = title
        table.field_names = list_header
        table.align['Output/Return Value'] = 'l'
        table.max_width = 60
        if list_data:
            for i in list_data:
                table.add_row(i)
        return table

    def replay_lite(self):
        answer = ''
        while answer != 'exit':
            print('<LITE MODE>Enter numbers to show specific data, enter "exit" to exit the LITE mode：')
            answer = input()
            if answer.isdecimal():
                answer = int(answer)
                if answer < Replay.num and answer != 0:
                    print(Replay.specific_data[answer])
                else:
                    print('Please enter the correct serial number')
            else:
                if answer != 'exit':
                    print('Please enter the correct serial number')


    def replay_single(self,parser,dict_cmd):
        if not dict_cmd:
            self.print_('There is no command to replay')
            return

        LogDB.transaction_id = dict_cmd['tid']
        if dict_cmd['valid'] == '0':
            replay_args = parser.parse_args(dict_cmd['cmd'].split())
            try:
                replay_args.func(replay_args)
            except consts.ReplayExit:
                self.print_('The transaction replay ends')
            except Exception:
                self.print_(str(traceback.format_exc()))
            finally:
                title = f"transaction: {dict_cmd['tid']}  command: {dict_cmd['cmd']}"
                table = self.make_table(title,self.replay_data)
                self.print_(str(table))
                if self.mode == 'LITE':
                    self.replay_lite()
                from iscsi_json import JsonOperation
                JsonOperation().json_data = None
        else:
            self.print_(f"Command error: {dict_cmd['cmd']} , and cannot be executed")


    def replay_execute(self,parser,transaction_id=None,start_time=None, end_time=None):
        logdb = LogDB()
        if transaction_id:
            LogDB.transaction_id = transaction_id
            cmd = logdb.get_cmd_via_tid()
            print(f'transaction num : 1')
            self.replay_single(parser,cmd)
            return
        elif start_time and end_time:
            cmds = logdb.get_cmd_via_time(start_time, end_time)
        else:
            cmds = logdb.get_all_cmd()

        if not cmds:
            print('There is no command to replay')
            return

        number_list = [str(i) for i in list(range(1, len(cmds) + 1))]

        print(f'transaction num : {len(cmds)}')
        for i in range(len(cmds)):
            print(f"{i + 1:<3} Transaction ID: {cmds[i]['tid']:<12} CMD: {cmds[i]['cmd']}")

        answer = ''
        while answer != 'exit':
            print(f'<{Replay.mode} MODE>Please enter the number to execute replay, or "all", enter "exit" to exit：')
            answer = input()
            if answer in number_list:
                cmd = cmds[int(answer) - 1]
                self.replay_single(parser,cmd)
                LogDB.reset_id()
                self.reset_data()
            elif answer == 'ls':
                print(f'transaction num : {len(cmds)}')
                for i in range(len(cmds)):
                    print(f"{i + 1:<3} Transaction ID: {cmds[i]['tid']:<12} CMD: {cmds[i]['cmd']}")
                continue
            elif answer == '-l' or answer == 'lite':
                Replay.mode = 'LITE'
                print('Switched to LITE mode, please continue')
                continue
            elif answer == '-n'or answer == 'normal':
                Replay.mode = 'NORMAL'
                print('Switched to NORMAL mode, please continue')
                continue
            elif answer == 'all':
                self.tempfile = NamedTemporaryFile(mode="w+", dir=r"../vplx/")
                Replay.replay_all = True
                Replay.mode = 'NORMAL'
                for cmd in cmds:
                    self.print_('\nNext Transaction：')
                    self.replay_single(parser,cmd)
                    LogDB.reset_id()
                    self.reset_data()
                self.tempfile.seek(0)
                os.system(f'less -im {self.tempfile.name}')
            elif answer != 'exit':
                print('Number error')



    def collapse_data(self):
        # 折叠数据
        pass



    @staticmethod
    def reset_data():
        Replay.replay_data = []
        Replay.num = 1
        Replay.specific_data = {}




