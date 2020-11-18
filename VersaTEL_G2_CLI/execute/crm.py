# coding=utf-8
import re
import time
import iscsi_json
import sundry as s
import subprocess

@s.deco_cmd('crm')
def execute_crm_cmd(cmd, timeout=60):
    """
    Execute the command cmd to return the content of the command output.
    If it times out, a TimeoutError exception will be thrown.
    cmd - Command to be executed
    timeout - The longest waiting time(unit:second)
    """
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    t_beginning = time.time()
    seconds_passed = 0
    output = None
    while True:
        if p.poll() is not None:
            break
        seconds_passed = time.time() - t_beginning
        if timeout and seconds_passed > timeout:
            p.terminate()
            raise TimeoutError(cmd, timeout)
        time.sleep(0.1)
    out, err = p.communicate()
    if len(out) > 0:
        out = out.decode()
        output = {'sts': 1, 'rst': out}
    elif len(err) > 0:
        err = err.decode()
        output = {'sts': 0, 'rst': err}
    elif out == b'':  # 需要再考虑一下 res stop 执行成功没有返回，stop失败也没有返回（无法判断stop成不成功）
        out = out.decode()
        output = {'sts': 1, 'rst': out}

    if output:
        return output
    else:
        s.handle_exception()

class CRMData():
    def __init__(self):
        self.crm_conf_data = self.get_crm_conf()


    def get_crm_conf(self):
        cmd = 'crm configure show'
        result = execute_crm_cmd(cmd)
        if result:
            return result['rst']
        else:
            s.handle_exception()

    def get_resource_data(self):
        # 用来匹配的原数据，allowed_initiators=""，有时有双引号，有时候没有，无法确定，然后多个iqn是怎么样的
        re_logical = re.compile(
            r'primitive (\w*) iSCSILogicalUnit \\\s\tparams\starget_iqn="([a-zA-Z0-9.:-]*)"\simplementation=lio-t\slun=(\d*)\spath="([a-zA-Z0-9/]*)"\sallowed_initiators="?([a-zA-Z0-9.: -]+)"?[\s\S.]*?meta target-role=(\w*)')
        result = s.re_findall(re_logical, self.crm_conf_data)
        return result

    def get_vip_data(self):
        re_vip = re.compile(
            r'primitive\s(\w*)\sIPaddr2\s\\\s*\w*\sip=([0-9.]*)\s\w*=(\d*)\s')
        result = s.re_findall(re_vip, self.crm_conf_data)
        return result

    def get_target_data(self):
        re_target = re.compile(
            r'primitive\s(\w*)\s\w*\s\\\s*params\siqn="([a-zA-Z0-9.:-]*)"\s[a-z=-]*\sportals="([0-9.]*):\d*"\s\\')
        result = s.re_findall(re_target, self.crm_conf_data)
        return result

    # 获取并更新crm信息
    def update_crm_conf(self):
        # crm_config_status = obj_crm.get_crm_data()
        if 'ERROR' in self.crm_conf_data:
            s.prt_log("Could not perform requested operations, are you root?",1)
        else:
            js = iscsi_json.JsonOperation()
            res = self.get_resource_data()
            vip = self.get_vip_data()
            target = self.get_target_data()
            js.update_crm_conf(res, vip, target)
            return True


class CRMConfig():
    def __init__(self):
        pass

    def create_crm_res(self, res, target_iqn, lunid, path, initiator):
        cmd = f'crm conf primitive {res} iSCSILogicalUnit params ' \
            f'target_iqn="{target_iqn}" ' \
            f'implementation=lio-t ' \
            f'lun={lunid} ' \
            f'path={path} ' \
            f'allowed_initiators="{initiator}" ' \
            f'op start timeout=40 interval=0 ' \
            f'op stop timeout=40 interval=0 ' \
            f'op monitor timeout=40 interval=15 ' \
            f'meta target-role=Stopped'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log("create iSCSILogicalUnit success",0)
            return True

    # 通过 crm st 获取resource状态
    def get_res_status(self, res):
        cmd = f'crm res list | grep {res}'
        result = execute_crm_cmd(cmd)
        if 'Started' in result['rst']:
            return True
        elif 'Stopped' in result['rst']:
            return False
        else:
            pass

    # 多次通过 crm st 检查resource状态，状态为started时返回True，检查5次都为stopped 则返回None
    def checkout_status_start(self, res):
        n = 0
        while n < 5:
            n += 1
            if self.get_res_status(res):
                s.prt_log(f'the resource {res} is Started', 0)
                return True
            else:
                time.sleep(1)
        s.prt_log(f'the resource {res} is Stopped', 1)

    # 多次通过 crm st 检查resource状态，状态为stop时返回True，检查5次都不为stopped 则返回None
    def checkout_status_stop(self, res):
        n = 0
        while n < 5:
            n += 1
            if self.get_res_status(res) == False:
                s.prt_log(f'the resource {res} is Stopped', 0)
                return True
            else:
                time.sleep(1)
        s.prt_log(f"the resource {res} can't Stopped", 1)

    # 停用res
    def stop_res(self, res):
        cmd = f'crm res stop {res}'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            return True
        else:
            s.prt_log("crm res stop fail",1)

    # 删除resource步骤
    def delete_res(self, res):
        if self.stop_res(res):
            if self.checkout_status_stop(res):
                if self.delete_conf_res(res):
                    return True
        s.prt_log(f"resource delete fail",1)

    # 创建resource相关配置
    def create_set(self, res, target):
        if self.create_col(res, target):
            if self.create_order(res, target):
                s.prt_log(f'create colocation:co_{res}, order:or_{res} success', 0)
                return True
            else:
                s.prt_log("create order fail", 1)
        else:
            s.prt_log("create colocation fail", 1)

    # 执行crm命令删除resource的配置
    def delete_conf_res(self, res):
        cmd = f'crm conf del {res}'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log(f"delete resource success: {res}", 0)
            return True
        else:
            output = result['rst']
            re_str = re.compile(rf'INFO: hanging colocation:co_{res} deleted\nINFO: hanging order:or_{res} deleted\n')
            if s.re_search(re_str, output):
                s.prt_log(f"delete colocation:co_{res}, order:or_{res} success", 0)
                return True
            else:
                s.prt_log(f"delete resource fail", 1)
                return False

    def create_col(self, res, target):
        cmd = f'crm conf colocation co_{res} inf: {res} {target}'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log("set coclocation success",0)
            return True

    def create_order(self, res, target):
        cmd = f'crm conf order or_{res} {target} {res}'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log("set order success",0)
            return True

    def start_res(self, res):
        cmd = f'crm res start {res}'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            return True

    # 刷新recourse状态，后续会用到
    def refresh(self):
        cmd = f'crm resource refresh'
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log("refresh",0)
            return True

    def change_initiator(self, res, iqns):
        iqns = ' '.join(iqns)
        cmd = f"crm config set {res}.allowed_initiators \"{iqns}\""
        result = execute_crm_cmd(cmd)
        if result['sts']:
            s.prt_log(f"Change {res} allowed_initiators success!",0)
            return True

