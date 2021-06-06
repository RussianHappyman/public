import paramiko
import argparse
import getpass
import csv
import re
import subprocess
import logging
import socket
import time

from datetime import datetime
from tabulate import tabulate
from paramiko import AutoAddPolicy
from paramiko.ssh_exception import SSHException

import mylogger

prom_serv = []
psi_serv = []
changed_pass_serv = []
error_pass_serv = []

max_bytes=1000
short_pause=1
long_pause=5


parser = argparse.ArgumentParser(description='Username, filename, oldpass and new pass.')

parser.add_argument('-u', '--username', action='store', dest='username', default='noname', help='Loging username.')
parser.add_argument('-f', '--filename', action='store', dest='filename', default='noname', help='filename of CSV file with listed servers IP addresses.')
parser.add_argument('-t', '--temp', action='store', dest='temp_password', default=False, help='Temporary (old) password of user')
parser.add_argument('-p', '--pass', action='store', dest='password', default=False, help='Changed (new) password of user.')

args = parser.parse_args()

username = args.username
if username == 'noname':
    print("*" * 50)
    username = input('Please type your Username: ')
    print(f"If typed Username: {username} is not correct, please brake a script by typing: Ctrl + Z\nIf Username is correct, please continue.")
    print("*" * 50)

filename = args.filename
if filename == 'noname':
    filename = input('Enter CSV filename with listed servers IP addresses: ')
    print(f"If typed CSV filename: {filename} is not correct, please brake a script by typing: Ctrl + Z\nIf CSV filename is correct, please continue.")
    print("*" * 50)

temp_password = args.temp_password
if temp_password == False:
    while not temp_password:
        temp_password=getpass.getpass(f'Enter temp_password (current old password) for username {username}: ')
        if temp_password == "":
            print(f"You have entered no temporary password for {username}, please try again")
            print("*" * 50)
        elif len(temp_password) < 4:
            print(f"Temporary password of username {username} is too short, please try again.")
            print("*" * 50)
            temp_password = False
    print("*" * 50)

password = args.password
if password == False:
    while not password:
        password = getpass.getpass('Enter new password for username {}: '.format(username))
        reenter = getpass.getpass('For confirming enter again password for username {}: '.format(username))
        if password == "":
            password = False
            print("You have entered no new password for {}, please try again".format(username))
            print("*" * 50)
        elif len(password) < 10:
            password = False
            print("New password of username {} is too short, please try again.".format(username))
            print("*" * 50)
        elif password != reenter:
            password = False
            print("Passwords do not match...")
            print("*" * 50)
    print("*" * 50)


def loadCSVdata(fname):
    with open (fname, encoding="utf-8", errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            line = ';'.join(row)
            match_prom = re.search(r'(?P<dns>pdles-mvp\d+)\S+(?P<address>(10)\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3}))', line)
            if match_prom:
                ip = match_prom.group('address')
                prom_serv.append(ip)

            match_psi = re.search(r'(?P<dns>tdles-mvp\d+)\S+(?P<address>(10)\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3}))', line)
            if match_psi:
                ip = match_psi.group('address')
                psi_serv.append(ip)

        if prom_serv != []:
            return prom_serv
        if psi_serv != []:
            return psi_serv


def ping_ip(ip_addresses):
    global tuple_ip
    reachable_ip = []
    unreachable_ip = []

    start_msg = '===> {} Connection to: {}'
    received_msg = '<=== {} Received from:   {}'
    logger = mylogger.logger_init("ping_ip",'ping_ip.log')

    for ip in ip_addresses:
        reply = subprocess.run('ping -c 3 -n {ip}'.format(ip=ip), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if reply.returncode == 0:
            reachable_ip.append(ip)
            logging.info(start_msg.format(datetime.now().time(), ip))
        else:
            unreachable_ip.append(ip)
            logging.info(start_msg.format(datetime.now().time(), ip))
    tuple_ip = reachable_ip, unreachable_ip
    return tuple_ip


def print_ip_table(check_ip_tuple):
    a, b = ping_ip(check_ip_tuple)
    table = {"Reachable": a, "Unreachable": b}
    print("", "Attention! Please have a look on list of ICMP Reachable and Unreachable servers IP addresses", "Only for ICMP reachable servers temp_password (current old password) will be changed by script.", "",  sep="\n")
    print(tabulate(table, headers="keys"))
    input("Press Enter to continue...")


def main():
    out = loadCSVdata(filename)
    input("Press Enter to continue for ICMP reachability servers checking.")
    print("*"*50)
    print_ip_table(out)
    connect_ip, _ = tuple_ip
    for ip in connect_ip:
        while True:
            try:
                ssh=paramiko.SSHClient()
                ssh.set_missing_host_key_policy(AutoAddPolicy())
                ssh.connect(hostname=ip, port=22, username=username, password=temp_password, look_for_keys=False, allow_agent=False)
                with ssh.invoke_shell() as ssh:
                    ssh.settimeout(short_pause)
                    init_output = ssh.recv(max_bytes)
                    init_output = init_output.decode('utf-8')
                    regex1 = r"Last login: "
                    regex2 = r"\(current\) UNIX password: "
                    time.sleep(short_pause)
                    match1 = re.search(regex1,init_output)
                    match2 = re.search(regex2,init_output)
                    if match1:
                        if match2:
                            ssh.send(temp_password+'\n')
                            time.sleep(short_pause)
                            output = ssh.recv(max_bytes).decode('utf-8')
                            if output == "\r\nNew password: ":
                                ssh.send(password+'\n')
                                time.sleep(short_pause)
                                output = ssh.recv(max_bytes).decode('utf-8')
                                if output == "\r\nRetype new password: ":
                                    ssh.send(password+'\n')
                                    time.sleep(short_pause)
#                                    output = ssh.recv(max_bytes).decode('utf-8')
#                                    print(output)
                                    changed_pass_serv.append(ip)
                                    break
                        else:
                            print(f"Looks like for server {ip} password is changed. Please check server {ip} manually")
                            error_pass_serv.append(ip)
                            break
                    else:
                        error_pass_serv.append(ip)
                        print(f"Server {ip} have an unexpected output. Server needs to be check manually.")
                        break
            except socket.timeout:
                print("[-] {}: Timeout Exception!".format(ip))
                error_pass_serv.append(ip)
                break
            except paramiko.AuthenticationException:
                print("[-] {}: Authentication Exception!".format(ip))
                error_pass_serv.append(ip)
                break
            except paramiko.SSHException:
                print("[-] {}: SSH Exception!".format(ip))
                error_pass_serv.append(ip)
                break
            except EOFError:
                print("[-] {}: EOFError Exception!".format(ip))
                error_pass_serv.append(ip)
                break
            except OSError:
                print("[-] {}: OSError Exception!".format(ip))
                error_pass_serv.append(ip)
                break
            except paramiko.ssh_exception.NoValidConnectionsError:
                error_pass_serv.append(ip)
                print("[-] {}: NoValidConnectionsError!".format(ip))
                break
            except paramiko.ssh_exception.AuthenticationException:
                error_pass_serv.append(ip)
                print("[-] {}: AuthenticationException!".format(ip))
                break

            finally:
                ssh.close()

    print("!"*100)
    table = {"PASSWORD CHANGED FOR SERVERS:": changed_pass_serv, "Need to check manually:": error_pass_serv, "ICMP unreachable IP:": tuple_ip[1]}
    print(tabulate(table, headers="keys"))
    print("!"*100)


if __name__=='__main__':
    main()




