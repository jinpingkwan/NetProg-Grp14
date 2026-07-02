# Task: Add `netauto configure backup` / `restore`

## Context

Every `netauto configure *` command (`ip`, `user`, `banner`, `interface`,
`route` — see [cli-playbook-map.md](../cli-playbook-map.md)) pushes a
change straight to the router with no safety net. If a change is wrong
(bad IP, bad route, typo'd banner), the only way back is to manually SSH in
and fix it by hand — there's no snapshot of "what the config looked like
before" and no one-command way to put it back.

This is a real gap for a tool that calls itself network configuration
automation: config backup before a risky change, and restore after a bad
one, is table stakes for this kind of CLI.

## Goal

Add two new commands, `netauto configure backup <host>` and
`netauto configure restore <host>`, backed by two new playbooks, so a user
can snapshot a router's running-config and put it back later.

## What to build

1. **`playbooks/backup_config.yml`**
   Target: `cisco.ios.*`, same style as the existing `configure_*.yml`
   files (banner comment block, `hosts: "{{ target_host }}"`). Gather the
   running-config (`cisco.ios.ios_command` with `show running-config`, or
   `cisco.ios.ios_config` with its built-in `backup: true` option — either
   is fine, pick whichever gives you a clean text file) and write it to a
   file on the **control node** (not the router) at
   `backups/<host>_<timestamp>.cfg`. Since the play's connection is
   `network_cli`, the file-write task needs `delegate_to: localhost` (or
   `run_once` + `connection: local`, whichever pattern you find cleaner) —
   it must not try to write to the router's own filesystem.
   End with an `ansible.builtin.debug` reporting the backup file path.

2. **`playbooks/restore_config.yml`**
   Takes a `backup_file` extra var (path under `backups/`), reads it, and
   pushes it back with `cisco.ios.ios_config` (`src:` pointed at the backup
   file — `ios_config` diffs it against the running config and only pushes
   the delta, same idempotent behavior as the other `configure_*`
   playbooks). Fail early with a clear error if the file doesn't exist
   rather than letting Ansible surface a confusing lookup error.

3. **CLI: `cli/commands/configure.py`**
   - `netauto configure backup <host>` → `run_playbook("backup_config",
     host, {})`. No extra flags needed.
   - `netauto configure restore <host> --file <path>` → `run_playbook
     ("restore_config", host, {"backup_file": path})`. If `--file` is
     omitted, default to the most recent `backups/<host>_*.cfg` on disk
     (glob + sort by timestamp in the filename) — flag in your PR if you
     think this default is more confusing than useful and want to require
     `--file` explicitly instead.

4. **Housekeeping**
   - Create a `backups/` directory at the project root (with a `.gitkeep`,
     matching the convention already used in `inventory/`, `playbooks/`,
     `roles/`, `reflections/`).
   - Add `backups/*.cfg` to `.gitignore` — these are host-specific runtime
     artifacts, not something to commit (same reasoning as the existing
     `artifacts/` entry for ansible-runner output).
   - Update [docs/cli-playbook-map.md](../cli-playbook-map.md) with the two
     new commands, following the existing table format.

## Acceptance criteria

- With the lab running (`sudo containerlab deploy -t
  lab/netauto-lab.clab.yml`):
  ```bash
  netauto configure backup router1
  # → prints the path of a new file under backups/

  netauto configure banner router1 --message "temporary test banner"
  netauto configure restore router1 --file backups/router1_<timestamp>.cfg
  netauto info device router1   # confirm the banner is back to what it was
  ```
- Running `restore` with a config identical to the current running-config
  reports no changes (idempotent, same convention as every other
  `configure_*` playbook).
- Running `restore` with a nonexistent `--file` path fails with a clear
  error, not a raw Ansible traceback.
- File headers follow the existing banner-comment convention used in
  `discover.yml` / `info_system.yml`.

## Out of scope

- Automatically backing up before every `configure *` command runs (that's
  a reasonable follow-up once this lands, but adds a playbook change to
  five existing files — keep this task scoped to the two new commands).
- Diffing/previewing a restore before applying it (`--dry-run`) — nice to
  have, not required here.
- Retention/pruning of old backup files.
