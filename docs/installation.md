# Installation Guide

This document covers every dependency needed to run NetAuto, and the exact
steps to get from a clean machine to a working `netauto discover`.

Tested on Fedora Linux 44 (Workstation). Steps are Linux-oriented throughout
(Docker + Containerlab + KVM); adjust package manager commands for your
distro.

---

## 1. System prerequisites

| Requirement | Why | Verify |
|---|---|---|
| Linux with KVM support | CSR1000v routers run as a QEMU VM inside a container (via vrnetlab) | `ls /dev/kvm` |
| Python ≥ 3.11 | Runs the `netauto` CLI and Ansible | `python3 --version` |
| git | Clones vrnetlab, project version control | `git --version` |
| Docker Engine | Runs all lab containers (routers, servers) | `docker --version` |
| Containerlab | Orchestrates the lab topology from the `.clab.yml` file | `containerlab version` |
| sudo access | `containerlab deploy`/`destroy` manage host network namespaces and need root | — |

### 1.1 Docker

Install Docker Engine for your distro (see
[docs.docker.com/engine/install](https://docs.docker.com/engine/install/)),
then add yourself to the `docker` group so you don't need `sudo` for every
`docker` command:

```bash
sudo usermod -aG docker "$USER"
```

Log out/in (or start a new shell session) afterwards — group membership
doesn't apply to already-open shells.

### 1.2 KVM / virtualization

The Cisco CSR1000v router image is a full IOS-XE VM booted via QEMU/KVM
inside a Docker container (vrnetlab), not a native container image. Confirm
hardware virtualization is available and you can access `/dev/kvm`:

```bash
ls -la /dev/kvm
groups | grep kvm || sudo usermod -aG kvm "$USER"
```

If `/dev/kvm` doesn't exist, enable virtualization (VT-x/AMD-V) in your
BIOS/hypervisor settings.

### 1.3 Containerlab

Install via the official script:

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

See [containerlab.dev/install](https://containerlab.dev/install/) for
alternative install methods (package repos, binary download). This project
was built and tested against containerlab **0.77.0** — run
`containerlab version` to confirm what you have, since node `kind` names
(e.g. `cisco_c8000v`) have changed across releases.

### 1.4 Optional: sshpass

Not required to run the app, but handy for manually poking at lab devices
during troubleshooting (Ansible itself doesn't need it):

```bash
sudo dnf install sshpass   # Fedora/RHEL
sudo apt install sshpass   # Debian/Ubuntu
```

---

## 2. Python environment

From the project root:

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt   # typer, ansible, ansible-runner, rich
pip install -e .                  # registers the `netauto` CLI entry point
```

`requirements.txt` pulls in the full `ansible` community package (not just
`ansible-core`), which already bundles the collections this project needs —
`cisco.ios`, `ansible.netcommon`, `ansible.utils`, etc. **No separate
`ansible-galaxy collection install` step is required.**

Verify:

```bash
netauto --help
ansible --version
```

> **Note on `ansible-pylibssh`:** you'll see
> `[WARNING]: ansible-pylibssh not installed, falling back to paramiko` when
> running network device playbooks. This is intentional — do not install
> `ansible-pylibssh`. It links against the system's libssh/OpenSSL crypto
> policies, which on modern distros (Fedora's default crypto policy included)
> reject the legacy `diffie-hellman-group14-sha1` key exchange and `ssh-rsa`
> host key algorithm that the lab's IOS-XE routers require. Paramiko ships
> its own, more permissive algorithm support and is what actually works
> against this gear.

---

## 3. Lab images

The lab topology (`lab/netauto-lab.clab.yml`) needs two Docker images built
locally before it can deploy: a custom Alpine Linux server image, and a
Cisco CSR1000v router image.

### 3.1 Linux server image

```bash
cd lab
docker build -t netauto-linux -f Dockerfile.linux .
```

### 3.2 Cisco CSR1000v router image

CSR1000v is Cisco proprietary software and **cannot be redistributed** —
you must obtain your own `.qcow2` image (e.g. from Cisco CML/VIRL or a
Cisco download portal you have licensed access to). This project was built
against `csr1000v-universalk9.16.09.05.qcow2`.

The image is built using [vrnetlab](https://github.com/hellt/vrnetlab),
vendored under `lab/vrnetlab/` (cloned from
`https://github.com/hellt/vrnetlab.git`; if that directory is missing,
re-clone it with `git clone https://github.com/hellt/vrnetlab.git lab/vrnetlab`):

```bash
cp /path/to/csr1000v-universalk9.16.09.05.qcow2 lab/vrnetlab/cisco/csr1000v/
cd lab/vrnetlab/cisco/csr1000v
sudo make docker-image
```

This takes several minutes — it boots the VM once with `--privileged` to
inject a serial-console bootstrap config, then commits the result as a
Docker image. `sudo` is required because the build step runs
`docker run --privileged`.

Confirm the image landed with the tag the topology file expects:

```bash
sudo docker images | grep -i csr
# should show: vrnetlab/cisco_csr1000v   16.09.05
```

If you're building a different CSR1000v version, update the `image:` tag
under the `cisco_c8000v` kind in `lab/netauto-lab.clab.yml` to match (see
the comment block at the top of that file — this containerlab version has
no `cisco_csr1000v` kind, so the image runs under kind `cisco_c8000v`,
which shares the same vrnetlab boot/console handling).

---

## 4. Lab topology

`lab/netauto-lab.clab.yml` deploys 4 nodes on a shared `172.20.20.0/24`
management network: 2 Cisco CSR1000v routers (backbone-linked to each other)
and 2 Alpine Linux servers, each single-homed behind one router.

| Hostname | Role | Platform | Mgmt IP | Data interface(s) | Connected to |
|---|---|---|---|---|---|
| `router1` | Router | Cisco CSR1000v (IOS-XE, kind `cisco_c8000v`) | 172.20.20.11 | Gi2: `10.10.10.1/30` · Gi3: `192.168.10.1/24` | Gi2 ↔ `router2` Gi2 (backbone) · Gi3 ↔ `server1` eth1 (LAN) |
| `router2` | Router | Cisco CSR1000v (IOS-XE, kind `cisco_c8000v`) | 172.20.20.12 | Gi2: `10.10.10.2/30` · Gi3: `192.168.20.1/24` | Gi2 ↔ `router1` Gi2 (backbone) · Gi3 ↔ `server2` eth1 (LAN) |
| `server1` | Linux server | Alpine Linux (`netauto-linux` image) | 172.20.20.21 | eth1: `192.168.10.10/24` | eth1 ↔ `router1` Gi3 (LAN); default route to `192.168.20.0/24` via `router1` |
| `server2` | Linux server | Alpine Linux (`netauto-linux` image) | 172.20.20.22 | eth1: `192.168.20.10/24` | eth1 ↔ `router2` Gi3 (LAN); default route to `192.168.10.0/24` via `router2` |

```
        10.10.10.0/30 (backbone)
router1 ─────────────────────── router2
  │ Gi3                            │ Gi3
  │ 192.168.10.0/24                │ 192.168.20.0/24
server1                          server2
```

For direct access bypassing the management network, the routers' SSH/NETCONF
ports are also published to the host: `router1` on `localhost:12201`
(SSH)/`12831` (NETCONF), `router2` on `12202`/`12832`.

Per-host IPs and interface metadata live in `inventory/host_vars/<hostname>.yml`
(the source of truth the playbooks read from); connection settings and
default lab credentials live in `inventory/group_vars/{routers,linux_servers}.yml`.

---

## 5. Deploy the lab

```bash
cd lab
bash deploy.sh
```

This builds the Linux image, deploys the containerlab topology, and prints
a summary of node addresses. Or run the steps manually:

```bash
cd lab
sudo containerlab deploy -t netauto-lab.clab.yml --reconfigure
```

The CSR1000v routers take a few minutes to fully boot (real IOS-XE VM, not
a lightweight container) — watch progress with:

```bash
sudo docker logs -f clab-netauto-router1
```

To tear the lab down:

```bash
cd lab
bash destroy.sh
```

---

## 6. Verify the installation

From the project root, with the venv activated:

```bash
netauto discover
```

Expected: all four hosts (`router1`, `router2`, `server1`, `server2`)
report `[ UP ]` with model/OS/version details. See
[cli-playbook-map.md](cli-playbook-map.md) for the full command reference.

### Troubleshooting

- **`host key mismatch` errors on routers** — routers get a fresh SSH host
  key every redeploy but keep the same management IP, so a stale
  `~/.ssh/known_hosts` entry from a previous deploy will block the new
  connection. `deploy.sh` clears these automatically; if you deploy
  manually, run `ssh-keygen -R 172.20.20.11 && ssh-keygen -R 172.20.20.12`.
- **`permission denied ... docker.sock`** — your shell session predates
  being added to the `docker` group; open a new terminal/session, or prefix
  commands with `sudo` in the meantime.
- **`pull access denied for cisco_csr1000v`** — the topology file's image
  tag doesn't match what `make docker-image` actually produced. Check
  `sudo docker images | grep csr` and make sure `lab/netauto-lab.clab.yml`
  points at the exact same tag (including the `vrnetlab/` prefix).

---

## 7. Running the test suite

The project includes a pytest-based test suite for the CLI commands. The
tests mock `run_playbook`, so no Containerlab topology, Docker containers,
or network devices are required.

Install the project dependencies:

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
pytest
```

For more detailed output:

```bash
pytest -v
```

To verify that the tests do not invoke Ansible directly, you can search the
test directory:

```bash
grep -rn "ansible_runner" tests/
```

No matches should be returned because every test mocks
`run_playbook()` rather than executing real playbooks.