# Future Improvements

## Dynamic Inventory

The current project uses a static inventory (`inventory/hosts.yml`) where hosts, IPs, and connection details are hardcoded. This works well for a fixed lab environment but does not scale to real-world infrastructure.

### Limitation of static inventory

Every time a device is added, removed, or has its IP changed, the inventory files must be manually updated. Past around 20 hosts this becomes error-prone and hard to maintain.

### How dynamic inventory would work

Instead of a static file, Ansible would query an external source of truth at runtime — such as **NetBox** (a popular open-source network IPAM/DCIM tool) — and build the host list and variables automatically before each playbook run.

```
netauto <command>
      │
      ▼
ansible-runner
      │
      ▼
inventory plugin  ──queries──▶  NetBox / cloud API / CMDB
      │
      ▼
hosts + variables built at runtime
```

The static `inventory/hosts.yml` would be replaced by a plugin config:

```yaml
# inventory/netbox.yml
plugin: netutils.netbox.nb_inventory
api_endpoint: https://netbox.example.com
token: "{{ lookup('env', 'NETBOX_TOKEN') }}"
group_by:
  - device_role
  - platform
```

Ansible reads this file, calls the NetBox API, and receives all devices with their IPs and roles — automatically grouped into `routers`, `linux_servers`, and so on. Individual `host_vars/` files would no longer be needed.

### Practical difference

| | Static (current) | Dynamic (future) |
|---|---|---|
| New device added | Edit `hosts.yml` + create `host_vars/` manually | Add device in NetBox — immediately available |
| Device decommissioned | Manually remove from files | Remove in NetBox — gone from next run |
| IP changes | Edit `host_vars/<host>.yml` | Update in NetBox — picked up automatically |
| Scale | Breaks down past ~20 hosts | Works for thousands |

### Why it was not implemented

The project runs against a local Docker/Containerlab lab with a fixed set of 4 hosts. Integrating a live NetBox instance or cloud API would require external infrastructure that is outside the scope of this assignment. The static inventory is the appropriate choice for this environment.

Dynamic inventory would be the natural next step if NetAuto were deployed against real network infrastructure.
