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
netauto info system server1 --host 127.0.0.1
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
| **`netauto configure baseline <host> --username <name>`** | **`playbooks/playbook.yml`** | **`target_host`, `new_username`, `new_password`** |
| `netauto configure backup <host>` | `playbooks/backup_config.yml` | `target_host` |
| `netauto configure restore <host> [--file <path>]` | `playbooks/restore_config.yml` | `target_host`, `backup_file` |

### Baseline configuration

The **baseline** command configures a newly deployed router in a single execution.

It automatically applies:

- Interface descriptions
- Interface IP addresses
- Administrator user account
- MOTD banner
- Static routes defined in `inventory/host_vars`

This provides the same end state as running the individual configure commands one by one, making it suitable for the initial deployment of a router.

`prefix_length` is derived from `subnet_mask` by `cli/commands/configure.py`
(via `ipaddress.IPv4Network`) since `ios_l3_interfaces` needs `<ip>/<prefix>`
rather than a dotted mask.

`configure ip`'s `--iface` flag is optional. When omitted, it targets
`default_data_interface`.

**Examples:**

```bash
netauto configure ip router1 --ip 192.168.10.1 --mask 255.255.255.0

netauto configure user router1 --username admin

netauto configure banner router1 --message "Authorized access only"

netauto configure interface router1 --iface GigabitEthernet3 --desc "Uplink"

netauto configure route router1 --dest 10.0.0.0/24 --via 192.168.10.254

netauto configure baseline router1 --username admin

netauto configure backup router1

netauto configure restore router1 --file backups/router1_20260705120000.cfg
netauto configure restore router1   # restores the most recent backup for router1
```

### Backup and restore

`configure backup` snapshots a router's running-config to a timestamped file
under `backups/` on the **control node** — a safety net to fall back on
before a risky change. `configure restore` pushes a captured backup back;
`ios_config` diffs it against the running config and only applies the delta,
so restoring an already-current config is a no-op.

If `--file` is omitted, `restore` defaults to the most recent
`backups/<host>_*.cfg` file on disk for that host. A nonexistent `--file`
path fails with a clear error rather than a raw Ansible traceback.

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

`target_host` is always set from the `<host>` argument so that each playbook knows which inventory host to target.

The `discover` playbook is the only exception because it targets `all`.