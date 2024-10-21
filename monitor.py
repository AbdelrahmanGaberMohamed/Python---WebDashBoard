import requests
import urllib3
import time
import csv
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import pymsteams

#Supress cert warning to avoid contaminated data
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#Load Env vars
load_dotenv()
#Vars
webhook = os.getenv('webhook')
url_auth = "https://10.0.10.10/AdminLogin"
url_usage = "https://10.0.10.10/api/v1/SysStatusUsage/"
payload = ""
auth_headers = {
    "name": os.getenv('username'),
    "password": os.getenv('password')
}
csv_file = '/home/ubuntu/fml-monitor/test.csv'
file_exist = os.path.isfile(csv_file)
cpu_tracker = [0,0,0,0]
mem_tracker = [0,0,0,0]
alert_sent = 0
# Create CSV file if not exist and add the column Titles
if not file_exist:
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Time", "CPU", "Memory"])
# Authenticate with API and extract session cookie from response
response = requests.post('https://10.0.10.10/api/v1/AdminLogin/', json=auth_headers, verify=False)
cookie_jar = response.cookies
for cookie in cookie_jar:
    cookie_name = cookie.name
    cookie_value = cookie.value
# Main
while True:
    # Get current time
    current_time = datetime.now()
    query_Date = current_time.strftime("%Y-%m-%d")
    query_time= current_time.strftime("%H:%M:%S")
    headers = {
        'Cookie': f'{cookie_name}={cookie_value}'
    }
    #Query usage
    response = requests.request("GET", url_usage, headers=headers, data=payload, verify=False)
    #print(response.text)
    #Store data as CSV
    data = json.loads(response.text)
    CPU_Util =  data.get("cpu")
    Memory_util =  data.get("memory")
    if CPU_Util == None:
        response = requests.post('https://10.0.10.10/api/v1/AdminLogin/', json=auth_headers, verify=False)
        cookie_jar = response.cookies
        for cookie in cookie_jar:
            cookie_name = cookie.name
            cookie_value = cookie.value
        print('New session')
        continue
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        print(query_Date)
        print(query_time)
        print (CPU_Util)
        print (Memory_util)
        writer.writerow([query_Date,query_time,CPU_Util,Memory_util])
    # Alertingl
    cpu_tracker.append(CPU_Util)
    mem_tracker.append(Memory_util)
    if len(cpu_tracker) > 4:
        cpu_tracker.pop(0)
    if len(mem_tracker) > 4:
        mem_tracker.pop(0)
    cpu_avg = sum(cpu_tracker) / len(cpu_tracker)
    mem_avg = sum(mem_tracker) / len(cpu_tracker)
    alert_condition = int(cpu_avg) > 80  or int(mem_avg) > 80
    if alert_condition == True and alert_sent == 0:
        myTeamsMessage = pymsteams.connectorcard(webhook)
        myTeamsMessage.text(f"Problem:\nFortiMail Utilization High\nAvg_CPU: '{cpu_avg}', Avg_Memory: '{mem_avg}'")
        myTeamsMessage.send()
        alert_sent = 1
    elif alert_condition == False and alert_sent == 1:
        myTeamsMessage = pymsteams.connectorcard(webhook)
        myTeamsMessage.text(f"Resolved:\nFortiMail Utilization High\nAvg_CPU: '{cpu_avg}', Avg_Memory: '{mem_avg}'")
        myTeamsMessage.send()
        alert_sent = 0


    # Sleep between calls    
    time.sleep(30) 
