# https://www.home-assistant.io/integrations/file/
#  For reading the results: https://community.home-assistant.io/t/how-to-extract-from-nested-json/99768/3
# https://psutil.readthedocs.io/en/latest/

import time
import datetime
#import urllib.request  ### Old external IP addr.
import math
import mdstat # https://pypi.org/project/mdstat/
import psutil
import json
import GPUtil
import string
import socket
from pySMART import Device
from requests import get


drive_types = ['nvme','sd','scsi']
GIGABYTE = 1024*1024*1024
hostname = socket.gethostname().lower()
### Since the script needs to run as root, I'm unaware of a way to automatically detect the output file path 
file_paths = {
    'schlerver': '/home/kschlichter/.hass_monitor/',
    'klaptop': '/home/kschlichter/.hass_monitor/',
    'nvschlichter': '/home/kschlichter/.hass_monitor/',
    'koldstorage': '/home/kschlichter/.hass_monitor/'
}

hass_monitor = {}


### CPUs ###
cpus, cpu_temps = {}, {}
cpu_temp = 'k10temp' if 'k10temp' in psutil.sensors_temperatures() else 'coretemp' #use AMD temp, if available

### Why do I need temp info for each core? ###
#for proc in range(0, len(psutil.sensors_temperatures()[cpu_temp])):
#    label, current, high, critical2 = psutil.sensors_temperatures()[cpu_temp][proc]
#    cpu_temps.update({label: current})

_, cpus["temp"], cpus["high"], cpus["critical"] = psutil.sensors_temperatures()[cpu_temp][0]
cpus["core_count"] = psutil.cpu_count()
cpus["utilization"] = psutil.cpu_percent()
cpus["load_average_15min"] = psutil.getloadavg()[2]


### memory ###
mem_dict = psutil.virtual_memory()._asdict()
memory = {
    "total": mem_dict['total'] // GIGABYTE,
    "available": mem_dict['available'] // GIGABYTE,
    "used": mem_dict['used'] // GIGABYTE,
    "free": mem_dict['free']// GIGABYTE,
    "pct_used": mem_dict['percent']
}


### swap ###
swap_dict = psutil.swap_memory()._asdict()
swap = {
    "total": swap_dict['total'] // GIGABYTE,
    "used": swap_dict['used'] // GIGABYTE,
    "free": swap_dict['free'] // GIGABYTE,
    "pct_used": swap_dict['percent']
}


### GPUs ###
gpus = GPUtil.getGPUs()
gpu_dict = {}
if gpus:
    for gpu in gpus:
        gpu = {
            "id": gpu.id,
            "uuid": gpu.uuid,
            "name": gpu.name,
            "utilization": 0 if math.isnan(gpu.load) else (gpu.load * 100),
            "memory_total": gpu.memoryTotal,
            "memory_used": gpu.memoryUsed,
            "memory_free": gpu.memoryFree,
            "pct_used": gpu.memoryUsed // gpu.memoryTotal,
            "temperature": gpu.temperature
        }
    #
    gpu_dict.update({gpu['id']: gpu})


### nics ###
nics,nics_unkeyed = {},{}
ifaces = psutil.net_if_addrs()
for name, v in ifaces.items():
    ip = v[0].address
    if not '::' in ip and not 'docker' in name and not 'br-' in name and not 'lo' in name:
        nics.update({name: ip})
#external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
external_ip = get('https://api.ipify.org').content.decode('utf8')
nics.update({"external": external_ip})

### drives ###
drives, partitions = {}, {}

for type in drive_types:
    for drive in ([str(x) for x in string.ascii_lowercase[0:10]] + [str(x) for x in range(10)]):
        if Device('/dev/' + type + drive).model:
            output = {}
            output.update({"model": Device('/dev/' + type + drive).model})
            output.update({"serial_number": Device('/dev/' + type + drive).serial})
            output.update({"assignment": '/dev/' + type + drive})
            output.update({"assessment": Device('/dev/' + type + drive).assessment})
            output.update({"temperature": Device('/dev/' + type + drive).temperature})
            #
            drives.update({"/dev/" + type + drive: output})
        elif Device('/dev/' + type + drive , interface='scsi').model:
            output = {}
            output.update({"model": Device('/dev/' + type + drive , interface='scsi').model})
            output.update({"serial_number": Device('/dev/' + type + drive , interface='scsi').serial})
            output.update({"assignment": '/dev/' + type + drive})
            output.update({"assessment": Device('/dev/' + type + drive , interface='scsi').assessment})
            output.update({"temperature": Device('/dev/' + type + drive , interface='scsi').temperature})
            #
            drives.update({"/dev/" + type + drive: output})


### partitions ###
all_disks = psutil.disk_partitions()
for idx, disk in enumerate(all_disks):
  if "/dev/mapper" in disk.device or "/dev/nvme" in disk.device or "/dev/sd" in disk.device:
    partitions[disk.mountpoint] = disk.device

# round to two 2 decimal places so /boot/efi shows up as > 0
for part in partitions:
    part_dict = psutil.disk_usage(part)._asdict()
    partition = {
        "drive": partitions[part],
        "total": round(part_dict['total'] / GIGABYTE,2),
        "used": round(part_dict['used'] / GIGABYTE,2),
        "free": round(part_dict['free'] / GIGABYTE,2),
        "pct_used": part_dict['percent']
    }
    drives.update({part: partition})


### mdraid ###
mdstat_out = mdstat.parse()
if mdstat_out['devices']:
  drives.update({"mdstat" : mdstat_out})


### battery ###
batt = psutil.sensors_battery()
battery = {}
if batt:
    battery_level, _, battery_ac = batt
    battery.update({"battery_level": battery_level, "battery_ac": battery_ac})


### boot ###
boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
boot_time = boot_time.strftime("%Y-%m-%d %H:%M:%S")


### put it together ###
hass_monitor = {
    "cpus": cpus,
    "memory": memory,
    "swap": swap,
    "gpus": gpu_dict,
    "nics": nics,
    "drives": drives,
    "battery": battery,
    "boot_time": boot_time,
    # Add a time_stamp key to the dictionary so we know it's not stale data.
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
}


### write it out to file ###
with open(file_paths[hostname] + "hass_monitor_" + hostname + ".json", "w") as json_file:
    json.dump(hass_monitor, json_file)

####To make it legible, convert it to a string and indent it; or use "jq . monitor_schlerver.json" from above.
#schlerver = json.dumps(schlerver, indent=2)
#with open("/mnt/storage/home-assistant/hass/file_sensors/schlerver/monitor_schlerver_human.json", "w") as outfile:
#    outfile.write(schlerver)
