#
# ImportSystemConfigurationNetworkShareREDFISH. Python script using Redfish API to import server configuration profile from a network share. 
#
# 
#
# _author_ = Texas Roemer <Texas_Roemer@Dell.com>
# _version_ = 6.0
#
# Copyright (c) 2017, Dell, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

import requests, json, sys, re, time, warnings, argparse

from datetime import datetime

warnings.filterwarnings("ignore")

parser=argparse.ArgumentParser(description="Python script using Redfish API to import server configuration profile (SCP) from a supported network share")
parser.add_argument('-ip',help='iDRAC IP address', required=True)
parser.add_argument('-u', help='iDRAC username', required=True)
parser.add_argument('-p', help='iDRAC password', required=True)
parser.add_argument('script_examples',action="store_true",help='ImportSystemConfigurationNetworkShareREDFISH.py -ip 192.168.0.120 -u root -p calvin -t ALL --ipaddress 192.168.0.130 --sharetype NFS --sharename /nfs --filename SCP_export_R740, this example is going to import SCP file from NFS share and apply all attribute changes for all components. \nImportSystemConfigurationNetworkShareREDFISH.py -ip 192.168.0.120 -u root -p calvin -t BIOS --ipaddress 192.168.0.140 --sharetype CIFS --sharename cifs_share_vm --filename R740_scp_file -s Forced --username administrator --password password, this example is going to only apply BIOS changes from the SCP file on the CIFS share along with forcing a server power reboot.')
parser.add_argument('-st', help='Pass in \"y\" to get supported share types for your iDRAC firmware version', required=False)
parser.add_argument('--ipaddress', help='Pass in the IP address of the network share', required=False)
parser.add_argument('--sharetype', help='Pass in the share type of the network share. If needed, use argument -st to get supported values for your iDRAC firmware version', required=False)
parser.add_argument('--sharename', help='Pass in the network share share name', required=False)
parser.add_argument('--username', help='Pass in the CIFS username', required=False)
parser.add_argument('--password', help='Pass in the CIFS username pasword', required=False)
parser.add_argument('--workgroup', help='Pass in the workgroup of your CIFS network share. This argument is optional', required=False)
parser.add_argument('-t', help='Pass in Target value to import component attributes. You can pass in \"ALL" to import all component attributes or pass in a specific component to import only those attributes. Supported values are: ALL, System, BIOS, IDRAC, NIC, FC, LifecycleController, RAID.', required=False)
parser.add_argument('--filename', help='Pass in the filename of the SCP file which is on the network share you are using', required=False)
parser.add_argument('--ignorecertwarning', help='Supported values are Disabled and Enabled. This argument is only required if using HTTPS for share type. If you don\'t pass in this argument when using HTTPS, default iDRAC setting is Enabled', required=False)
parser.add_argument('-s', help='Pass in ShutdownType value. Supported values are Graceful, Forced and NoReboot. If you don\'t use this optional parameter, default value is Graceful. NOTE: If you pass in NoReboot value, configuration changes will not be applied until the next server manual reboot.', required=False)
parser.add_argument('-e', help='Pass in end HostPowerState value. Supported values are On and Off. If you don\'t use this optional parameter, default value is On', required=False)


args=vars(parser.parse_args())

idrac_ip=args["ip"]
idrac_username=args["u"]
idrac_password=args["p"]

def get_sharetypes():
    req = requests.get('https://%s/redfish/v1/Managers/iDRAC.Embedded.1' % (idrac_ip), auth=(idrac_username, idrac_password), verify=False)
    data = req.json()
    print("\n- ImportSystemConfiguration supported share types for iDRAC %s\n" % idrac_ip)
    if u'OemManager.v1_0_0#OemManager.ImportSystemConfiguration' in data[u'Actions'][u'Oem']:
        share_types = data[u'Actions'][u'Oem'][u'OemManager.v1_0_0#OemManager.ImportSystemConfiguration'][u'ShareParameters'][u'ShareType@Redfish.AllowableValues']
    else:
        share_types = data[u'Actions'][u'Oem'][u'OemManager.v1_1_0#OemManager.ImportSystemConfiguration'][u'ShareParameters'][u'ShareType@Redfish.AllowableValues']
    for i in share_types:
        if i == "LOCAL":
            pass
        else:
            print(i)
    
def import_server_configuration_profile():
    global job_id
    method = "ImportSystemConfiguration"
    url = 'https://%s/redfish/v1/Managers/iDRAC.Embedded.1/Actions/Oem/EID_674_Manager.ImportSystemConfiguration' % idrac_ip
    payload = {"ShareParameters":{"Target":args["t"]}}
    if args["s"]:
        payload["ShutdownType"] = args["s"]
    if args["e"]:
        payload["HostPowerState"] = args["e"]
    if args["ipaddress"]:
        payload["ShareParameters"]["IPAddress"] = args["ipaddress"]
    if args["sharetype"]:
        payload["ShareParameters"]["ShareType"] = args["sharetype"]
    if args["sharename"]:
        payload["ShareParameters"]["ShareName"] = args["sharename"]
    if args["filename"]:
        payload["ShareParameters"]["FileName"] = args["filename"]
    if args["username"]:
        payload["ShareParameters"]["UserName"] = args["username"]
    if args["password"]:
        payload["ShareParameters"]["Password"] = args["password"]
    if args["workgroup"]:
        payload["ShareParameters"]["Workgroup"] = args["workgroup"]
    if args["ignorecertwarning"]:
        payload["ShareParameters"]["IgnoreCertificateWarning"] = args["ignorecertwarning"]
    print("\n- WARNING, arguments and values for %s method\n" % method)
    for i in payload.items():
        if i[0] == "ShareParameters":
            for ii in i[1].items():
                if ii[0] == "Password":
                    print("Password: **********")
                else:
                    print("%s: %s" % (ii[0],ii[1]))
        else:
            print("%s: %s" % (i[0],i[1]))
    
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False, auth=(idrac_username,idrac_password))
    d=str(response.__dict__)

    try:
        z=re.search("JID_.+?,",d).group()
    except:
        print("\n- FAIL: detailed error message: {0}".format(response.__dict__['_content']))
        sys.exit()

    job_id=re.sub("[,']","",z)
    if response.status_code != 202:
        print("\n- FAIL, status code not 202\n, code is: %s" % response.status_code)   
        sys.exit()
    else:
        print("\n- Job ID \"%s\" successfully created for %s method\n" % (job_id, method)) 

    response_output=response.__dict__
    job_id=response_output["headers"]["Location"]
    job_id=re.search("JID_.+",job_id).group()


    
def loop_job_status():
    start_time=datetime.now()
    while True:
        req = requests.get('https://%s/redfish/v1/TaskService/Tasks/%s' % (idrac_ip, job_id), auth=(idrac_username, idrac_password), verify=False)
        statusCode = req.status_code
        data = req.json()
        current_time=(datetime.now()-start_time)
        if statusCode == 202 or statusCode == 200:
            pass
            time.sleep(3)
        else:
            print("Query job ID command failed, error code is: %s" % statusCode)
            sys.exit()
        if "failed" in data[u'Oem'][u'Dell'][u'Message'] or "completed with errors" in data[u'Oem'][u'Dell'][u'Message'] or "Not one" in data[u'Oem'][u'Dell'][u'Message'] or "not compliant" in data[u'Oem'][u'Dell'][u'Message'] or "Unable" in data[u'Oem'][u'Dell'][u'Message'] or "The system could not be shut down" in data[u'Oem'][u'Dell'][u'Message']:
            print("- FAIL, Job ID %s marked as %s but detected issue(s). See detailed job results below for more information on failure\n" % (job_id, data[u'Oem'][u'Dell'][u'JobState']))
            print("- Detailed job results for job ID %s\n" % job_id)
            for i in data['Oem']['Dell'].items():
                print("%s: %s" % (i[0], i[1]))
            print("\n- Config results for job ID %s\n" % job_id)
            for i in data['Messages']:
                for ii in i.items():
                    if ii[0] == "Oem":
                        print("-" * 80)
                        for iii in ii[1]['Dell'].items():
                            print("%s: %s" % (iii[0], iii[1]))
                    else:
                        pass
            sys.exit()
        elif "No reboot Server" in data[u'Oem'][u'Dell'][u'Message']:
            print("- PASS, job ID %s successfully marked completed. NoReboot value detected and config changes will not be applied until next manual server reboot\n" % job_id)
            print("\n- Detailed job results for job ID %s\n" % job_id)
            for i in data['Oem']['Dell'].items():
                print("%s: %s" % (i[0], i[1]))
            sys.exit()
        elif "Successfully imported" in data[u'Oem'][u'Dell'][u'Message'] or "completed with errors" in data[u'Oem'][u'Dell'][u'Message'] or "Successfully imported" in data[u'Oem'][u'Dell'][u'Message']:
            print("- PASS, job ID %s successfully marked completed\n" % job_id)
            print("- Detailed job results for job ID %s\n" % job_id)
            for i in data['Oem']['Dell'].items():
                print("%s: %s" % (i[0], i[1]))
            print("\n- %s completed in: %s" % (job_id, str(current_time)[0:7]))
            print("\n- Config results for job ID %s -\n" % job_id)
            for i in data['Messages']:
                for ii in i.items():
                    if ii[0] == "Oem":
                        print("-" * 80)
                        for iii in ii[1]['Dell'].items():
                            print("%s: %s" % (iii[0], iii[1]))
                    else:
                        pass

            sys.exit()
        elif "No changes" in data[u'Oem'][u'Dell'][u'Message'] or "No configuration changes" in data[u'Oem'][u'Dell'][u'Message']:
            print("\n- PASS, job ID %s marked completed\n" % job_id)
            print("- Detailed job results for job ID %s\n" % job_id)
            for i in data['Oem']['Dell'].items():
                print("%s: %s" % (i[0], i[1]))
            sys.exit()
        else:
            print("- WARNING, JobStatus not completed, current status: \"%s\", percent complete: \"%s\"" % (data[u'Oem'][u'Dell'][u'Message'],data[u'Oem'][u'Dell'][u'PercentComplete']))
            time.sleep(1)
            continue

if __name__ == "__main__":
    if args["st"]:
        get_sharetypes()
    else:
        import_server_configuration_profile()
        loop_job_status()
        
