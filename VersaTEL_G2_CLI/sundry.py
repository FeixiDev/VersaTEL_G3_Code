# coding:utf-8
import socket

# Connect to the socket server and transfer data, and finally close the
# connection.


def send_via_socket(data):
    ip = "127.0.0.1"
    port = 12144

    client = socket.socket()
    client.connect((ip, port))
    judge_conn = client.recv(8192).decode()
    print(judge_conn)
    client.send(b'database')
    client.recv(8192)
    client.sendall(data)
    client.recv(8192)
    client.send(b'exit')
    client.close()
