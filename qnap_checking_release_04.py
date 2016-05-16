#!/usr/bin/python                                                                              #
# -*- coding: utf-8 -*-                                                                        # 
# written by Evgeny Romanenko(https://www.upwork.com/o/profiles/users/_~011039ba47c60f2b5d/)   #
# aka FessAectan                                                                               # 
# Please feel free to contact me with any questions and issues within this scipt               #
################################################################################################

header = """
<html>
   <body>
    <p><font size="2" color="grey" face="Arial">This report has been generated via Python script that has been written by </br>
     Evgeny Romanenko(https://www.upwork.com/o/profiles/users/_~011039ba47c60f2b5d/).</br>
     Please feel free to contact me with any questions and issues with it.</br></font></p>
   </body>
</html>
"""

import glob, sys, socket, os, re, subprocess, getpass, smtplib, shutil, time
import datetime
from email.mime.text import MIMEText
from datetime import date

# LOG FILE NAME
log_file = 'QNap_check__' + datetime.datetime.now().strftime('%Y.%m.%d_%H.%M.%S') + '.log'

# VARIABLES
OStype = sys.platform # Mac OS ot Windows ?
ComputerName = socket.gethostname()
UserName = getpass.getuser()
PWD = os.getcwd()

# How many packets may be lost in percent
PLpercent = 20
# Network latency threshold in ms
Threshold = 10

ServerFileFlag = "QNapServerFileFlag"

Name2Check = "google.com" # for DNS resolution test
IP2Check = "8.8.8.8" # for Internet reachable
IPQNap = "192.168.10.7" # QNap IP address

# TEST FOLDER ON THE QNAP SERVER (in my invironment it is \\192.168.10.7\images)
TestSMBFolder = "images"


if OStype == "darwin":
    Path2SFSAF = '/tmp/' + ServerFileFlag # <--- Path to separate sile sync application folder
    LocalServerFileFlag = PWD + "/" + ServerFileFlag + "_" + ComputerName + "_" + UserName
    LocalSMBFolder = PWD + "/" + "QNapSMB"
    RPathSFF = LocalSMBFolder + "/" + ServerFileFlag
    LPathSFF = PWD + "/" + ServerFileFlag
    WorkStationFileFlag = PWD + "/" + "WorkStationFileFlag" + "_" + ComputerName + "_" + UserName
    Path4WFFF = LocalSMBFolder + "/" + "WorkStationFileFlag" + "_" + ComputerName + "_" + UserName
    SMBShare = "//" + IPQNap + "/" + TestSMBFolder + " "
    mountchecking = subprocess.check_output("/sbin/mount" + "|grep -q " + LocalSMBFolder + "||printf 1", shell=True)
    command2mount = "/sbin/mount " + "-t" + " smbfs " + SMBShare + LocalSMBFolder
    command2unmount = "/sbin/umount " + LocalSMBFolder
    DefaultGW = subprocess.check_output("netstat -nr|grep default|awk '{print $2}'|sed 's/^[ \t]*//'",stderr=subprocess.STDOUT,shell=True)

if OStype == "win32":
    Path2SFSAF = os.environ['USERPROFILE'] + "\\appdata\\local\\temp\\" + ServerFileFlag # <--- Path to separate sile sync application folder
    LocalServerFileFlag = PWD + "\\" + ServerFileFlag + "_" + ComputerName + "_" + UserName
    LocalSMBFolder = "j:\\"
    RPathSFF = LocalSMBFolder + ServerFileFlag
    LPathSFF = PWD + "\\" + ServerFileFlag
    WorkStationFileFlag = PWD + "\\" + "WorkStationFileFlag" + "_" + ComputerName + "_" + UserName
    Path4WFFF = LocalSMBFolder + "WorkStationFileFlag" + "_" + ComputerName + "_" + UserName
    SMBShare = "\\\\" + IPQNap + "\\" + TestSMBFolder + " "
    mountchecking = os.path.isdir("j:\\")
    if not mountchecking:
        mountchecking = 1
    command2mount = "net use j: " + SMBShare
    command2unmount = "net use /delete j: "
    import wmi
    wmi_obj = wmi.WMI()
    wmi_sql = "select IPAddress,DefaultIPGateway from Win32_NetworkAdapterConfiguration where IPEnabled=TRUE"
    wmi_out = wmi_obj.query( wmi_sql )
    for dev in wmi_out:
        DefaultGW = dev.DefaultIPGateway[0]

# DEFAULT GATEWAYS
# two sides, one is in 192.168.254.0/24 and another is in 192.168.10.0/24
# if default gateway on the laptop is in 192.168.254.1 - RemoteGW = default gateway on the remote side
if re.match('192.168.254.1',DefaultGW):
    RemoteGW = "192.168.10.1"

if re.match('192.168.10.1',DefaultGW):
    RemoteGW = "192.168.254.1"

# EMAIL SETTINGS
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "some_email@gmail.com"
SMTP_PASSWORD = "111"

EMAIL_TO = ["info@thecall.ru"]
EMAIL_FROM = "some_email@gmail.com"
EMAIL_SUBJECT = "Computername: " + socket.gethostname() + ". Username: " + UserName  + ". Status report on the: "

DATE_FORMAT = "%d/%m/%Y"
EMAIL_SPACE = ", "

# DO NOT EDIT BELOW #

def create_workstation_file():
    if os.path.exists(WorkStationFileFlag):
        os.remove(WorkStationFileFlag)
        fn = open(WorkStationFileFlag, 'a')
        fn.close()
    else:
        fn = open(WorkStationFileFlag, 'a')
        fn.close()

def NicsIPsRouting():
    if OStype == "darwin":
        NICs = subprocess.check_output("/sbin/ifconfig")
        DNS = subprocess.check_output("grep nameserver /etc/resolv.conf",stderr=subprocess.STDOUT,shell=True)
        ROUTINGT = subprocess.check_output("netstat -nr",stderr=subprocess.STDOUT,shell=True)
        DATA="\n\nDETAILED REPORT ABOUT:\n" + "NICs status: " + "\n" + NICs + "\n\n" + "Namservers: " + "\n" + DNS  + "\n\n" + "Routing: " + "\n" + ROUTINGT
    if OStype == "win32":
        NICs = subprocess.check_output("ipconfig /all")
        ROUTINGT = subprocess.check_output("route print",stderr=subprocess.STDOUT,shell=True)
        DATA="\n\nDETAILED REPORT ABOUT:\n" + "NICs status and nameservers:" + "\n" + NICs + "\n\n" + "Routing: " + "\n" + ROUTINGT
    return DATA


def write_to_file(file_to_write, message):
    fh = open(file_to_write, 'a')
    fh.write(message)
    fh.close()

def send_email(MSG, typeofdata):
    msg = MIMEText(MSG, typeofdata)
    msg['Subject'] = EMAIL_SUBJECT + " %s" % (date.today().strftime(DATE_FORMAT))
    msg['To'] = EMAIL_SPACE.join(EMAIL_TO)
    msg['From'] = EMAIL_FROM
    mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    mail.starttls()
    mail.login(SMTP_USERNAME, SMTP_PASSWORD)
    mail.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    mail.quit()

def dns_check(DomainName):
    try:
        socket.gethostbyname(DomainName)
        return 0
    except socket.gaierror:
        return 1


def ping_or_not_ping(ping_destination):
    if OStype == "darwin":
        response = os.system("ping -c 3 " + ping_destination)
    if OStype == "win32":
        response = os.system("ping -n 3 " + ping_destination)
    return response

def CheckPL(ipaddr,procent):
    print "\n\nPlease wait until I'll checking packets loss...\n"
    if OStype == "darwin":
        StPingReq = os.popen("ping -c 10 " + ipaddr)
        StProcent = re.compile(r"[\d]+\.[\d]+[%]")
    if OStype == "win32":
        StPingReq = os.popen("ping -n 10 " + ipaddr)
        StProcent = re.compile(r"[\d]+[%]")
    for line in StPingReq.readlines():
        StTotal = StProcent.search(line)
        if (StTotal != None):
            break
    if OStype == "darwin":
        result = re.sub('\.[\d]+%','',StTotal.group(0)) 
    if OStype == "win32":
        result = StTotal.group(0).replace('%','')
    if (int(result) >= procent):
        return 1
    else:
        return 0


def ping_latency(ipaddr, count, threshold):
    print "\n\nPlease wait until I'll checking netwotk latency...\n"
    StTotal = 0
    StPingReq = os.popen("ping -c " + str(count) + " " + ipaddr)
    if OStype == "win32":
        StPingReq = os.popen("ping -n " + str(count) + " " + ipaddr)
    for line in StPingReq.readlines():
        m = re.search('time=[\d].+[\d]+', line) 
        if OStype == "win32":
            m = re.search('time=[\d]+ms', line)
        if m != None:
            if OStype == "darwin":
                StTotal += int(re.sub('\.[\d]+','',m.group(0).replace('time=','')))
            if OStype == "win32":
                StTotal += int(re.sub('ms','',m.group(0).replace('time=','')))
    result = StTotal/count
    if (int(result) >= threshold):
        return 1
    else:
        return 0

def open_report():
    if OStype == "darwin":
        subprocess.call(['open', '-a', 'TextEdit', PWD + "/" + log_file])
    if OStype == "win32":
        subprocess.Popen("notepad.exe " + PWD + "\\" + log_file)
    sys.exit(0)


def smb_check():
    if OStype == "darwin":
        if not os.path.exists(LocalSMBFolder):
            os.makedirs(LocalSMBFolder)
    if mountchecking:
        retcode = subprocess.call(command2mount, shell=True)
        if not retcode:
            shutil.copyfile(RPathSFF, LPathSFF)
            shutil.copyfile(WorkStationFileFlag, Path4WFFF)
        time.sleep(1)
        subprocess.call(command2unmount, shell=True)
        return retcode
    else:
        time.sleep(1)
        subprocess.call(command2unmount, shell=True)
        retcode = subprocess.call(command2mount, shell=True)
        if not retcode:
            shutil.copyfile(RPathSFF, LPathSFF)
            shutil.copyfile(WorkStationFileFlag,Path4WFFF)
        return retcode

def compare_dates():
    write_to_file(log_file, "\nCompare ServerFlag file and its local copy:")
    if os.path.exists(LocalServerFileFlag) and os.path.exists(LPathSFF):
        if OStype == "darwin":
            file_in_sync_folder = datetime.datetime.fromtimestamp(int(os.path.getctime(Path2SFSAF))).strftime('%Y-%m-%d %H:%M:%S')
            file_on_QNap = datetime.datetime.fromtimestamp(int(os.path.getctime(LPathSFF))).strftime('%Y-%m-%d %H:%M:%S')
        if OStype == "win32":
            file_in_sync_folder = datetime.datetime.fromtimestamp(int(os.path.getmtime(Path2SFSAF))).strftime('%Y-%m-%d %H:%M:%S')
            file_on_QNap = datetime.datetime.fromtimestamp(int(os.path.getmtime(LPathSFF))).strftime('%Y-%m-%d %H:%M:%S')
        write_to_file(log_file, "\nCreation date of ServerFlagFile is " + file_on_QNap)
        write_to_file(log_file, "\nCreation date of local copy ServerFlagFile is " + file_in_sync_folder)
    else:
        if not os.path.exists(LPathSFF):
            write_to_file(log_file, "\nThere is nothing to compare, I don't have ServerFlagFile\n")
        if not os.path.exists(LocalServerFileFlag):
            write_to_file(log_file, "\nThere is nothing to compare, I don't have local copy of ServerFlagFile\n")
#    if os.path.exists(LPathSFF):
#        shutil.copy(LPathSFF, LocalServerFileFlag)
#        os.remove(LPathSFF)
#    else:
#        write_to_file(log_file, "\nThere is nothing to compare, I don't have local copy of ServerFlagFile\n")

def remove_old_logs():
    count = 0
    p = glob.glob(PWD + "/QNap_check__*")
    for i in p:
        os.remove(p[count])
        count += 1


def main():
    remove_old_logs()
    create_workstation_file()
    if ping_or_not_ping(DefaultGW):
        write_to_file(log_file, "GENERAL REPORT:\nDefault gateway " + DefaultGW + " isn't reachable - TEST FAILED" + '\n')
        write_to_file(log_file,"\n\nPLEASE CONTACT YOUR SYSTEM ADMINISTRATOR. I AM NOT ABLE TO DO ANYTHINK MORE" + "\n")
        open_report()
    else:
        write_to_file(log_file, "GENERAL REPORT:\nDefault gateway " + DefaultGW + " is reachable - TEST OK" + '\n')
        if dns_check(Name2Check):
            write_to_file(log_file,"\nI have some troubles with DNS(can't resolve " + Name2Check + ") - TEST FAILED "+ '\n')
        else:
            write_to_file(log_file,"\nDNS name resolution - TEST OK" + '\n')
            if ping_or_not_ping(RemoteGW):
                write_to_file(log_file, "\nRemote gateway IP " + RemoteGW + " isn't reachable - TEST FAILED" + '\n')
            else:
                write_to_file(log_file,'\nRemote gateway IP ' +  RemoteGW + " is reachable - TEST OK" + '\n')
        if ping_or_not_ping(IP2Check):
            write_to_file(log_file, "\nIP " + IP2Check + " isn't reachable - TEST FAILED" + "'\n'")
        if ping_or_not_ping(IPQNap):
            write_to_file(log_file, "\nQNap IP address " + IPQNap + " isn't reachable - TEST FAILED" + '\n')
            write_to_file(log_file,"\n\nPLEASE CONTACT YOUR SYSTEM ADMINISTRATOR. I AM NOT ABLE TO DO ANYTHINK MORE" + "\n")
        else:
            write_to_file(log_file, "\nQNap IP address " + IPQNap + " is reachable - TEST OK" + '\n')
            if CheckPL(IPQNap,PLpercent):
                write_to_file(log_file, "Packet loss to QNap IP address " + IPQNap + " more than " + str(PLpercent)  + "% - it can be a problem\n")
            if ping_latency(IPQNap, 10, Threshold):
                write_to_file(log_file, "Ping latency to QNap IP address " + IPQNap + " more than " + str(Threshold)  + " - it can be a problem\n")
            if smb_check():
                write_to_file(log_file, "\nProblem with mounting QNap SMB/CIFS shares from " + IPQNap + " - TEST FAILED" + '\n')
                write_to_file(log_file,"\n\nPLEASE CONTACT YOUR SYSTEM ADMINISTRATOR. I AM NOT ABLE TO DO ANYTHINK MORE" + "\n")
            else:
                write_to_file(log_file, "\nMount QNap SMB/CIFS shares from " + IPQNap + " - TEST OK" + '\n')
                compare_dates()

    f = open(log_file,'r')
    message = f.read() + NicsIPsRouting()
    message = message.replace('\n', '<br />')
    send_email(header + message, 'html')
    write_to_file(log_file, NicsIPsRouting())
    open_report()
 
if __name__ == "__main__":
    main()
