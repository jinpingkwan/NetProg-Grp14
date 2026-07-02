import re

path = '/var/tmp/vrnetlab/common/vrnetlab.py'
with open(path, 'r') as f:
    data = f.read()

# Change the default cpu parameter from "host" to "qemu64"
data = data.replace('cpu="host"', 'cpu="qemu64"')

with open(path, 'w') as f:
    f.write(data)

# Verify
with open(path, 'r') as f:
    for i, line in enumerate(f, 1):
        if 'cpu=' in line and 'qemu' in line.lower():
            print(f"Line {i}: {line.rstrip()}")
        if 'cpu=' in line and 'host' in line:
            print(f"Line {i} STILL HAS HOST: {line.rstrip()}")

print("Patch applied successfully.")
