#!/usr/bin/python
# -*- coding: utf-8 -*-
# written by FessAectan aka er (almost, ping_latency doesn't belong me ;) )
 
import sys, pexpect, time, datetime, os, re, paramiko
import smtplib
from email.mime.text import MIMEText
 
user = 'root'
secret_sc = '111'
secret_ns1 = '111'
 
i = datetime.datetime.now()
log_file = 'sc_ddg_check.' + i.strftime('%Y.%m.%d.%H.%M') + '.log'
CheckPL_Treshold = 0
 
 
def ConnectToSSH(ipaddr,port,commands,secret):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ipaddr, username=user, password=secret, port=port)
    time.sleep(1)
    stdin, stdout, stderr = client.exec_command(commands)
    data = stdout.read() + stderr.read()
    client.close()
    write_to_file(log_file,data + '\n')
 
 
def CreateFileFlag(FileFlag):
    os.popen("touch " + FileFlag)
 
def DeleteFileFlag(FileFlag):
    os.popen("rm " + FileFlag)
 
 
def sendemail(subj,msg):
    me = 'root@zabbix.example.com'
    you = 'admin@example.com'
    smtp_server = '127.0.0.1'
    msg = MIMEText(msg)
    msg['Subject'] = subj
    msg['From'] = me
    msg['To'] = you
    s = smtplib.SMTP(smtp_server)
    s.sendmail(me, [you], msg.as_string())
    s.quit()
 
def CheckPL(ipaddr,procent):
    global CheckPL_Treshold
    StPingReq = os.popen("ping " + ipaddr + " -c10")
    StProcent = re.compile(r"[\d]+[%]")
    for line in StPingReq.readlines():
      StTotal=StProcent.search(line)
      if (StTotal != None):
        break
    result = StTotal.group(0).replace('%','')
 
    if (int(result) >= procent):
        CheckPL_Treshold += 1
        if CheckPL_Treshold >=5:
            CheckPL_Treshold = 0
            return 1
    else:
        CheckPL_Treshold = 0
        return 0
 
def write_to_file(file_to_write, message):
    fh = open(file_to_write, 'a')
    fh.write(message)
    fh.close()
 
 
def ping_or_not_ping(ping_destination):
    response = os.system("ping -c 5 " + ping_destination)
    return response
 
 
def ping_latency(ping_destination):
    latency = 0
    interval = 3
    threshold = 300
    count = 0
    line = 'Ping Interval: ' + str(interval) + ', Destination: ' + ping_destination + ', Threshold to Log (msec): ' + str(threshold) + '\n'
 
    #write_to_file(log_file, line)
 
    ping_command = 'ping -i ' + str(interval) + ' ' + ping_destination
    print line
 
    child = pexpect.spawn(ping_command)
    child.timeout=1200
 
    while 1:
        line = child.readline()
        if not line:
            break
 
        if line.startswith('ping: unknown host'):
            print 'Unknown host: ' + ping_destination
            write_to_file(log_file, 'Unknown host: ' + ping_destination)
            break
        if count > 0:
            ping_time = float(line[line.find('time=') + 5:line.find(' ms')])
            line = time.strftime("%m/%d/%Y %H:%M:%S") + ": " + str(ping_time)
            print str(count) + ": " + line
            latency = latency + ping_time
            if ping_time > threshold:
                write_to_file(log_file, line + '\n')
        if count > 4:
            break
        count += 1
    return (latency / count)
 
def Check(ipaddr):
    timeout_of_sleep = 60
    result = ping_or_not_ping(ipaddr)
    if result == 0:
        if os.path.exists("NotPingedFlag"):
            write_to_file(log_file, i.strftime('%Y.%m.%d.%H:%M:%S') + ':' + '\n' + "DDG IP 192.168.10.10 alive" +'\n'  + "Change IP on ns1.example.com... " + '\n' + "Checking result:" + '\n')
            ConnectToSSH("10.10.1.4",4522,"""/root/sh/ifup.sh""", secret_sc)
            ConnectToSSH("ns1.example.com",22,"""/root/sh/change_serial_ips_sc2ddg_restart_named.sh""", secret_ns1)
            sendemail("""IP(example.com) DDG alive""","""I have sent command on ns1.example.com for switching  ru/com sites on IP DDG""")
            DeleteFileFlag("NotPingedFlag")
            timeout_of_sleep = 3600
            write_to_file(log_file,'\n' + "I'll sleep an hour..." + '\n')
        packetloss = CheckPL(ipaddr,30)
        if packetloss == 0:
            if os.path.exists("PacketLossFlag"):
                write_to_file(log_file, i.strftime('%Y.%m.%d.%H:%M:%S') + ':' + '\n' + "Packet loss to DDG IP 192.168.10.10 < 30%" +'\n' + "Change IP on ns1.example.com... " + '\n' + "Checking result:" + '\n')
                ConnectToSSH("10.10.1.4",4522,"""/root/sh/ifup.sh""", secret_sc)
                ConnectToSSH("ns1.example.com",22,"""/root/sh/change_serial_ips_sc2ddg_restart_named.sh""", secret_ns1)
                sendemail("""I don't see packet loss to IP(example.com) DDG""","""I've sent command on ns1.example.com for switching ru/com sites on IP DDG""")
                DeleteFileFlag("PacketLossFlag")
                timeout_of_sleep = 3600
                write_to_file(log_file,'\n' + "I'll sleep an hour..." + '\n')
            latency = ping_latency(ipaddr)
            if latency > 300:
                sendemail("""Delay with ping DDG IP(example.com) > 300""","""You have to decide what to do - switch DNS or NOT""")
        elif packetloss == 1:
            if os.path.exists("PacketLossFlag") == False:
                write_to_file(log_file, i.strftime('%Y.%m.%d.%H:%M:%S') + ':' + '\n' + "30%+ packet loss to DDG IP 192.168.10.10" +'\n' + "Change IP on ns1.example.com... " + '\n' + "Checking result:" + '\n')
                ConnectToSSH("10.10.1.4",4522,"""/root/sh/ifdown.sh""", secret_sc)
                ConnectToSSH("ns1.example.com",22,"""/root/sh/change_serial_ips_ddg2sc_restart_named.sh""", secret_ns1)
                sendemail("""30%+ packets to IP(example.com) DDG loss""","""I've sent command on ns1.example.com for switching ru/com sites on IP 10.10.1.x""")
                CreateFileFlag("PacketLossFlag")
                timeout_of_sleep = 3600
                write_to_file(log_file,'\n' + "I'll sleep an hour..." + '\n')
    elif result > 0:
        if os.path.exists("NotPingedFlag") == False:
            write_to_file(log_file, i.strftime('%Y.%m.%d.%H:%M:%S') + ':' + '\n' + "DDG IP 192.168.10.10 is not alive" +'\n'  + "Change IP on ns1.example.com...  " + '\n' + "Checking result:" + '\n')
            ConnectToSSH("10.10.1.4",4522,"""/root/sh/ifdown.sh""", secret_sc)
            ConnectToSSH("ns1.example.com",22,"""/root/sh/change_serial_ips_ddg2sc_restart_named.sh""", secret_ns1)
            sendemail("""IP(example.com) DDG is not alive""","""I've sent command on ns1.example.com for switching ru/com sites on IP 10.10.1.x""")
            CreateFileFlag("NotPingedFlag")
            timeout_of_sleep = 3600
            write_to_file(log_file,'\n' + "I'll sleep an hour..." + '\n')
    return timeout_of_sleep
 
 
def main():
    while True:
        timeout = Check('192.168.10.10')
        time.sleep(timeout)
 
if __name__ == "__main__":
    main()

