# Task: Add an automated test suite for the `netauto` CLI layer

## Context

The project has a working CLI (`cli/commands/configure.py`, `info.py`,
`discover.py`) that parses arguments, validates them, and builds an
`extra_vars` dict passed to `cli/runner.py`'s `run_playbook()`, which shells
out to `ansible_runner.run()` against the lab inventory.

There is currently no automated test suite anywhere in the repo (no
`tests/` directory, no `pytest` in `requirements.txt`, nothing wired into
`pyproject.toml`). The only way to verify the CLI behaves correctly today is
to run it against the live Containerlab lab by hand — see
[docs/installation.md](../installation.md) and
[docs/cli-playbook-map.md](../cli-playbook-map.md). That's slow (the
CSR1000v routers take minutes to boot) and means small regressions in
argument parsing or validation (e.g. a broken `--mask` check) can only be
caught by manually re-running commands against real routers.

The CLI layer itself — argument validation, `extra_vars` construction — has
no dependency on Ansible actually running. It can and should be tested in
isolation, with `run_playbook` mocked out, so this suite runs in CI or on a
laptop with no lab, no Docker, and no KVM.

## Goal

Add a `pytest`-based test suite covering every `netauto` command's argument
validation and the exact `extra_vars` dict each command hands to
`run_playbook`, with `run_playbook` mocked so no real Ansible run ever
happens.

## What to build

1. **Test tooling**
   - Add `pytest` to `requirements.txt` (or a new `requirements-dev.txt` if
     you'd rather keep runtime/dev deps separate — your call, just document
     which one in the PR).
   - Add a `[tool.pytest.ini_options]` section to `pyproject.toml` pointing
     at a `tests/` directory (`testpaths = ["tests"]`).

2. **`tests/` directory**, mirroring `cli/commands/`:
   - `tests/test_configure.py`
   - `tests/test_info.py`
   - `tests/test_discover.py`

   Use `typer.testing.CliRunner` (already a transitive dep via
   `typer[all]`) to invoke `cli.main.app`, and `unittest.mock.patch` (or
   `pytest-mock` if you add it) to patch `cli.runner.run_playbook` at the
   import site used by each command module (e.g.
   `cli.commands.configure.run_playbook`) so tests assert on the call
   arguments instead of touching Ansible.

3. **Coverage — `configure` commands** (`cli/commands/configure.py`):
   - `configure ip <host> --ip --mask` → asserts `run_playbook` called with
     `("configure_ip", host, {"ip_address": ..., "subnet_mask": ...,
     "prefix_length": ...})`, including the mask → prefix-length derivation
     (e.g. `255.255.255.0` → `24`).
   - Same, with `--iface` supplied → `interface_name` present in
     `extra_vars`; without it → key absent (matches the "defaults to
     `default_data_interface`" behavior documented in
     [cli-playbook-map.md](../cli-playbook-map.md)).
   - Invalid `--ip` (e.g. `999.1.1.1`) and invalid `--mask` (e.g.
     `255.255.255.7`) each exit non-zero via `typer.BadParameter` and never
     call `run_playbook`.
   - `configure user <host> --username` — password is prompted
     (`hide_input`, `confirmation_prompt`); test by passing `input=` to
     `CliRunner.invoke` with matching password lines.
   - `configure banner`, `configure interface`, `configure route` — each
     asserts the correct playbook name and `extra_vars` shape.
   - `configure route` invalid `--dest` (not CIDR) and invalid `--via` (not
     an IPv4 address) both fail validation before `run_playbook` is called.

4. **Coverage — `info` commands** (`cli/commands/info.py`):
   - `info device <host>` → `run_playbook("info_device", host, {})`.
   - `info system <host>` → `run_playbook("info_system", host, {})`.
   - `info system <host> --host <ip>` → `extra_vars` includes
     `{"ansible_host": ip}`.

5. **Coverage — `discover`** (`cli/commands/discover.py`):
   - Bare `netauto discover` → `run_playbook("discover", "all", {})`.

## Acceptance criteria

- `pytest` runs green from the project root with no lab, no Docker, and no
  network access — `run_playbook` must never actually be called through to
  `ansible_runner` in any test.
- Every CLI command in `cli/commands/` has at least one passing-path test
  and, where validation exists, at least one failing-path test.
- Tests fail loudly (not silently pass) if someone changes an `extra_vars`
  key name — e.g. renames `subnet_mask` — since that's exactly the class of
  regression this suite exists to catch.
- Update [docs/installation.md](../installation.md) with a short "Running
  the test suite" note (`pip install -r requirements.txt && pytest`) — this
  is the first thing in the repo that doesn't need the lab running, worth
  calling out.

## Out of scope

- Integration tests that actually run playbooks against the lab (that's
  what the acceptance criteria in
  [implement-configure-playbooks.md](implement-configure-playbooks.md)
  already cover manually).
- Testing the Ansible playbooks themselves (`playbooks/*.yml`) — this task
  is scoped to the Python CLI layer only.
- CI pipeline setup (GitHub Actions, etc.) — just get the suite green
  locally; wiring it into CI is a separate task.
