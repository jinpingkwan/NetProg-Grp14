# Task: Clean up the stale `playbooks/playbook.yml`

## Context

`playbooks/playbook.yml` predates the six modular `configure_*.yml` /
`info_device.yml` playbooks built in
[implement-configure-playbooks.md](implement-configure-playbooks.md). It
was already flagged there as "a separate, unrelated task" — this is that
task.

At the time it was flagged, the note assumed `playbook.yml` was still using
stale `arista.eos.*` modules. It isn't anymore (it's been updated to
`cisco.ios.*`, matching the current CSR1000v inventory — see recent commit
history). The problem now is different: it's **redundant and unsafe**, not
stale:

- It duplicates, in one hardcoded file, exactly what
  `configure_ip.yml` + `configure_interface.yml` + `configure_user.yml` +
  `configure_banner.yml` + `configure_route.yml` already do individually —
  two implementations of the same config pushes that can silently drift
  out of sync with each other.
- It hardcodes both routers' interface IPs, descriptions, and static
  routes directly in the play (`GigabitEthernet2`/`3`, `10.10.10.x`,
  `192.168.x.0/24`) instead of reading them from `host_vars/<host>.yml`
  (which already defines an `interfaces:` dict with this exact data — see
  `inventory/host_vars/router1.yml`).
- It hardcodes a **plaintext password** in play 3:
  `secret 0 netops123` — `secret 0` is IOS's unencrypted secret type. This
  is a lab, but it's still a bad pattern to leave sitting in the repo,
  especially since `configure_user.yml` already does this properly by
  taking `new_password` as an extra var instead of a literal.
- Nothing in the CLI or docs points at it — `netauto` never calls
  `playbook.yml`. It's only runnable manually
  (`ansible-playbook playbooks/playbook.yml`), which most contributors
  won't know still exists or is safe to ignore.

## Goal

Remove the duplication and the hardcoded secret. Two viable directions —
pick one and justify the choice briefly in your PR description:

**Option A — delete it.** The six modular playbooks + CLI fully supersede
it; nothing links to `playbook.yml`, so there's no behavior to preserve.
Simplest option if you agree it has no remaining purpose.

**Option B — turn it into a real "apply full baseline" playbook.** Some
users may want one command that configures a router from scratch (fresh
lab boot) rather than five separate `netauto configure *` calls. If so,
rework it to:
- Read interface IP/description from `host_vars/<host>.yml`'s existing
  `interfaces:` dict instead of hardcoding them.
- Take the new-user username/password as extra vars (or an
  `ansible-vault`-encrypted var file), never a literal in the play.
- Either `import_playbook`/`include_tasks` the existing `configure_*.yml`
  logic (so there's one source of truth for each config step) or, if that
  proves awkward given each file's `hosts: "{{ target_host }}"` pattern,
  at least parametrize every value that's currently hardcoded.

If you pick Option B, also add a corresponding
`netauto configure baseline <host>` command
(`cli/commands/configure.py` + `run_playbook("playbook", host, {})` or
similar) so it's actually reachable from the CLI like everything else —
and document it in [docs/cli-playbook-map.md](../cli-playbook-map.md).

## Acceptance criteria

- No plaintext password literal remains anywhere in `playbooks/`.
- No hardcoded per-router IP/interface/route data remains outside
  `inventory/host_vars/*.yml` and `inventory/group_vars/*.yml`.
- If Option A: `playbook.yml` is removed, and a `git grep -r playbook.yml`
  across the repo (docs included) turns up nothing referencing it.
- If Option B: `netauto configure baseline router1` (or whatever command
  name you choose) runs cleanly against a freshly-deployed lab and produces
  the same end state as running all five `netauto configure *` commands by
  hand, and is idempotent on a second run.
- [docs/cli-playbook-map.md](../cli-playbook-map.md) reflects whichever
  option you pick (either no mention of `playbook.yml`, or a documented new
  command).

## Out of scope

- `ansible-vault` integration in general (encrypting `ansible_password` /
  `ansible_become_password` in `inventory/group_vars/*.yml`) — that's a
  separate, broader task. Here, just don't make the *new* problem (a
  literal password) worse; a plain extra-var is a sufficient fix even if
  it's still passed in cleartext on the CLI for now.
