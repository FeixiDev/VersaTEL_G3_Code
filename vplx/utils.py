import paramiko
import socket
import os
import subprocess


class SSHConn(object):

    def __init__(self, host, port=22, username=None, password=None, timeout=8):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None
        self.ssh_connect()

    def _connect(self):
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            # time.sleep(1)
            # objSSHClient.exec_command("\x003")
            self.SSHConnection = objSSHClient
        except:
            print(f"Failed to connect {self._host}")

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            print(f'Connect retry for {self._host}')
            self._connect()

    def exec_cmd(self, command):
        if self.SSHConnection:
            stdin, stdout, stderr = self.SSHConnection.exec_command(command)
            err = stderr.read()
            if len(err) > 0:
                err = err.decode() if isinstance(err, bytes) else err
                return {"st": False, "rt": err}
            data = stdout.read()
            if len(data) > 0:
                data = data.decode() if isinstance(data, bytes) else data
                return {"st": True, "rt": data}


# def get_host_ip():
#     """
#     查询本机ip地址
#     :return: ip
#     """
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(('8.8.8.8', 80))
#         ip = s.getsockname()[0]
#     finally:
#         s.close()
#
#     return ip


def get_hostname():
    """
    查询本机hostname
    :return:
    """
    # local_hostname = os.popen('hostname').read()
    local_hostname = os.popen('hostname').read().strip('\n')
    return local_hostname


def exec_cmd(cmd, conn=None):
    if conn:
        result = conn.exec_cmd(cmd)
        return result
    else:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if p.returncode == 0:
            result = p.stdout
            result = result.decode() if isinstance(result, bytes) else result
            return {"st": True, "rt": result}
        else:
            # print(f"  Failed to execute command: {cmd}")
            # print("  Error message:\n", p.stderr.decode())
            return {"st": False, "rt": p.stderr}
