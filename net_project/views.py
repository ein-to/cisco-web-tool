from django.shortcuts import render
import sys
import time
import paramiko
import os
import cmd
import datetime
# Create your views here.
from ciscoconfparse import CiscoConfParse
import numpy as np
import pandas as pd
import re

def index(request):
    return render(request, 'net_project/index.html')

def backup(request):
    return render(request, 'net_project/backup_user_switch.html')


def backup_cisco(request):
    now = datetime.datetime.now()

    USER = 'some_user'
    PASSWORD = 'some_password'
    f = open('C:/venv1/Projects/net/cisco-list.txt')
    for ip in f.readlines():
        ip = ip.strip()
        filename_prefix ='C:/backup/net/' + ip

        if ip == '10.120.8.11':
            context = ['A','B','C','D','E']
            for i in context:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, username=USER, password=PASSWORD)
                chan = client.invoke_shell(height=999999999)
                time.sleep(2)
                chan.send('enable\n\n')
                time.sleep(1)
                chan.send('change context %s\n' % i)
                time.sleep(1)
                chan.send('terminal pager 0\n')
                time.sleep(1)
                filename = "%s_%s_%.2i%.2i%i.txt" % (filename_prefix,i,now.year,now.month,now.day)
                chan.send('sh run\n')
                time.sleep(5)
                output = chan.recv(999999999)
                ff = open(filename, 'a')
                ff.write(output.decode("utf-8"))
                ff.close()
                client.close()
                f.close()
        else:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=USER, password=PASSWORD)
            chan = client.invoke_shell(height=999999999)
            time.sleep(2)
            filename = "%s_%.2i%.2i%i.txt" % (filename_prefix,now.year,now.month,now.day)
            chan.send('sh run\n')
            time.sleep(5)
            output = chan.recv(999999999)
            ff = open(filename, 'a')
            ff.write(output.decode("utf-8"))
            ff.close()
            client.close()
            f.close()
    return render(request, 'net_project/backup_user_switch.html')

def find_mac_addr_template(request):
    return render(request, 'net_project/find_mac_addr_template.html')

def find_mac_addr(request):
    list_interface_usw1 = []
    list_interface_usw2 = []
    USER = 'some_user'
    PASSWORD = 'some_password'

    cisco = ['10.120.8.3','10.120.8.4']
    for c in cisco:
        mac = request.GET['mac_addr']
        ip = c.strip()
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=USER, password=PASSWORD)
        chan = client.invoke_shell(height=999999999)
        time.sleep(2)
        chan.send('sh run\n')
        time.sleep(3)
        output = chan.recv(999999999)
        filename_prefix ='C:/venv1/Projects/net/'
        filename = "%s%s.txt" % (filename_prefix, 'find_mac_addr')
        ff = open(filename, 'a')
        ff.write(output.decode("utf-8"))
        ff.close()
        parse = CiscoConfParse('C:/venv1/Projects/net/find_mac_addr.txt')
        for res in parse.find_objects_w_child(parentspec='^interface', childspec=mac):
            chan.send('conf t\n')
            time.sleep(1)
            chan.send('%s\n' % (res.text))
            time.sleep(1)
            chan.send('shutdown\n')
            time.sleep(1)
            chan.send('no switchport port-security mac-address sticky %s vlan access\n' % (mac))
            time.sleep(1)
            chan.send('no shutdown\n')
            time.sleep(1)
            chan.send('end\n')
            time.sleep(1)
            chan.send('wr mem\n')
            time.sleep(5)
            if c == '10.120.8.3':
                list_interface_usw1.append(res.text)
            if c == '10.120.8.4':
                list_interface_usw2.append(res.text)
        client.close()
        os.remove('C:/venv1/Projects/net/find_mac_addr.txt')
    return render(request, 'net_project/find_mac_addr.html', {'list_interface_usw1': list_interface_usw1,
                    'list_interface_usw2': list_interface_usw2, 'mac': mac})

def find_block_port(request):
    USER = 'some_user'
    PASSWORD = 'some_password'

    cisco = ['10.120.8.3','10.120.8.4']

    try:
        port = request.GET['port']
    except:
        port_sw1 = []
        port_sw2 = []
        for c in cisco:
            ip = c.strip()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=USER, password=PASSWORD)
            chan = client.invoke_shell(height=999999999)
            time.sleep(2)
            chan.send('sh int status\n')
            time.sleep(1)
            output = chan.recv(999999999)
            filename_prefix ='C:/venv1/Projects/net/'
            filename = "%s%s.txt" % (filename_prefix, 'find_block_port')
            ff = open(filename, 'a')
            ff.write(output.decode("utf-8"))
            ff.close()
            client.close()
        res = np.genfromtxt('find_block_port.txt', skip_header=4, skip_footer=2, invalid_raise = False, dtype='str')
        interface = res[:,0]
        vlan_column = res[:,3]
        i=0
        for v in vlan_column:
            if v == 'vl-err-dis':
                if i < 48:
                    port_sw1.append(interface[i])
                else:
                    port_sw2.append(interface[i])
            i=i+1

        if port_sw1:
            c = '10.120.8.3'
            del_and_unlock_interface(c, port_sw1)
        if port_sw2:
            c = '10.120.8.4'
            del_and_unlock_interface(c, port_sw2)
        os.remove('C:/venv1/Projects/net/find_block_port.txt')
    return render(request, 'net_project/find_block_port.html', {'port_sw1': port_sw1, 'port_sw2': port_sw2})

def del_and_unlock_interface(c, switch):
    text = 'vlan access'
    USER = 'some_user'
    PASSWORD = 'some_password'
    ip = c.strip()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=USER, password=PASSWORD)
    chan = client.invoke_shell(height=999999999)
    time.sleep(2)
    for interface in switch:
        chan.send('sh run int %s\n' % (interface))
        time.sleep(1)
        output = chan.recv(999999999)
        filename_prefix ='C:/venv1/Projects/net/'
        filename = "%s%s.txt" % (filename_prefix, 'interface')
        ff = open(filename, 'a')
        ff.write(output.decode("utf-8"))
        ff.close()
        parse = CiscoConfParse('C:/venv1/Projects/net/interface.txt')
        for intf in parse.find_objects_w_child(parentspec='^interface', childspec='vlan access'):
            for ch in intf.all_children:
                match = re.search(text, ch.text)
                if match:
                    chan.send('conf t\n')
                    time.sleep(1)
                    chan.send('int %s\n' % (interface))
                    time.sleep(1)
                    chan.send('sh\n')
                    time.sleep(1)
                    chan.send('no %s\n' % (ch.text))
                    time.sleep(1)
                    chan.send('no sh\n')
                    time.sleep(1)
                    chan.send('end\n')
                    time.sleep(1)
        os.remove('C:/venv1/Projects/net/interface.txt')
    client.close()
    pass

def find_block_port_template(request):
    return render(request, 'net_project/find_block_port_template.html')
