# CLI Command to Ansible Playbook Map

This document maps every `netauto` CLI command to the Ansible playbook it
invokes and the extra variables passed through.

---

## Discovery

| CLI Command | Playbook | Extra Vars |
|---|---|---|
| `netauto discover` | `playbooks/discover.yml` | — |

**Example:**
```bash
netauto discover
```

---

## Info

| CLI Command | Playbook | Role | Extra Vars |
|---|---|---|---|
| `netauto info device <host>` | `playbooks/info_device.yml` | — | `target_host` |
| `netauto info system <host>` | `playbooks/info_system.yml` | `roles/linux_sysinfo` | `target_host` |

**Examples:**
```bash
netauto info device router1
netauto info system server1
netauto info system server1 --host 127.0.0.1   # override connection IP
```

---

## Configure

All configure playbooks target `cisco.ios.*` modules — routers run Cisco
CSR1000v / IOS-XE (see `inventory/group_vars/routers.yml`).

| CLI Command | Playbook | Extra Vars |
|---|---|---|
| `netauto configure ip <host> --ip <addr> --mask <mask> [--iface <name>]` | `playbooks/configure_ip.yml` | `target_host`, `ip_address`, `subnet_mask`, `prefix_length`, `interface_name` (optional) |
| `netauto configure user <host> --username <name>` | `playbooks/configure_user.yml` | `target_host`, `new_username`, `new_password` |
| `netauto configure banner <host> --message <text>` | `playbooks/configure_banner.yml` | `target_host`, `banner_message` |
| `netauto configure interface <host> --iface <name> --desc <text>` | `playbooks/configure_interface.yml` | `target_host`, `interface_name`, `interface_desc` |
| `netauto configure route <host> --dest <cidr> --via <gateway>` | `playbooks/configure_route.yml` | `target_host`, `route_dest`, `route_gateway` |

`prefix_length` is derived from `subnet_mask` by `cli/commands/configure.py`
(via `ipaddress.IPv4Network`) since `ios_l3_interfaces` needs `<ip>/<prefix>`
rather than a dotted mask, and the `netaddr` library isn't installed for the
Jinja `ipaddr` filter to do the conversion inside the playbook.

`configure ip`'s `--iface` flag is optional — when omitted it targets
`default_data_interface` (`GigabitEthernet3`, set per-router in
`group_vars/routers.yml`), the LAN-facing data link. Pass `--iface` to target
any other interface instead. (`netauto configure interface` remains the
command for setting just a description, independent of IP configuration.)

**Examples:**
```bash
netauto configure ip router1 --ip 192.168.10.1 --mask 255.255.255.0
netauto configure ip router1 --ip 192.168.20.1 --mask 255.255.255.0 --iface GigabitEthernet4
netauto configure user router1 --username admin
netauto configure banner router1 --message "Authorized access only"
netauto configure interface router1 --iface GigabitEthernet3 --desc "Uplink to core"
netauto configure route router1 --dest 10.0.0.0/24 --via 192.168.10.254
```

---

## How the CLI invokes playbooks

All commands go through `cli/runner.py`, which calls `ansible_runner.run()`:

```
netauto <command> <args>
        │
        ▼
cli/runner.py — run_playbook(playbook, host, extra_vars)
        │
        ▼
ansible-runner — playbooks/<playbook>.yml
        │         -e target_host=<host>
        │         -e <extra_vars>
        ▼
Ansible plays against inventory/hosts.yml
```

`target_host` is always set from the `<host>` argument so that each playbook
knows which inventory host to target via `hosts: "{{ target_host }}"`.
The `discover` playbook is the exception — it targets `all` directly and
ignores `target_host`.
