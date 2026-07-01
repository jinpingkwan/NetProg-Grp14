import sys
with open('/var/tmp/vrnetlab/common/vrnetlab.py', 'r') as f:
    data = f.read()
data = data.replace('"-cpu", "host"', '"-cpu", "qemu64"')
with open('/var/tmp/vrnetlab/common/vrnetlab.py', 'w') as f:
    f.write(data)
