#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Build images and deploy the NetAuto Containerlab topology
# =============================================================================
# Usage:  bash deploy.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TOPO_FILE="netauto-lab.clab.yml"
LINUX_IMAGE="netauto-linux"
DOCKERFILE="Dockerfile.linux"
CSR_IMAGE="vrnetlab/cisco_csr1000v:16.09.05"
CSR_QCOW2_GLOB="csr1000v-universalk9.*.qcow2"
CSR_ISO_GLOB="csr1000v-universalk9.*.iso"

# Docker Desktop doesn't expose the standard /var/run/docker.sock, so point
# the docker/containerlab clients at its own socket if that's what's running.
if [ -z "${DOCKER_HOST:-}" ] && [ ! -S /var/run/docker.sock ] && [ -S "$HOME/.docker/desktop/docker.sock" ]; then
    export DOCKER_HOST="unix://$HOME/.docker/desktop/docker.sock"
fi

echo "============================================="
echo "  NetAuto Lab — Deploy"
echo "============================================="
echo

# Installs a CSR1000v .iso onto a fresh qcow2 disk via a headless QEMU boot,
# since vrnetlab only accepts a ready-made .qcow2 (its Makefile globs *.qcow2).
convert_csr_iso_to_qcow2() {
    local iso="$1"
    local qcow2="${iso%.iso}.qcow2"
    local disk_size="8G"
    local timeout_secs=1800
    local workdir
    workdir="$(mktemp -d)"
    local console_log="$workdir/console.log"

    echo "     No .qcow2 found, but found $(basename "$iso") — installing it onto a new qcow2..."
    qemu-img create -f qcow2 "$qcow2" "$disk_size" >/dev/null

    local kvm_flag="-enable-kvm"
    if [ ! -r /dev/kvm ]; then
        echo "     ⚠ /dev/kvm not accessible, falling back to software emulation (much slower)."
        kvm_flag=""
    fi

    echo "     Booting installer headlessly (this can take 15-30 min)."
    echo "     Console log: $console_log"
    qemu-system-x86_64 \
        $kvm_flag -cpu host -m 4096 -smp 2 \
        -drive file="$qcow2",if=virtio,format=qcow2 \
        -cdrom "$iso" \
        -boot order=cd \
        -serial file:"$console_log" \
        -display none \
        -daemonize -pidfile "$workdir/qemu.pid"

    local bar_width=40
    local hashes dots
    hashes="$(printf '%*s' "$bar_width" '' | tr ' ' '#')"
    dots="$(printf '%*s' "$bar_width" '' | tr ' ' '.')"

    local elapsed=0
    until grep -q "Press RETURN to get started" "$console_log" 2>/dev/null; do
        local pct=$(( elapsed * 100 / timeout_secs ))
        (( pct > 100 )) && pct=100
        local filled=$(( elapsed * bar_width / timeout_secs ))
        (( filled > bar_width )) && filled=$bar_width
        printf "\r     [%s%s] %3d%%  (%02d:%02d elapsed)" \
            "${hashes:0:filled}" "${dots:filled}" "$pct" $((elapsed/60)) $((elapsed%60))

        sleep 10
        elapsed=$((elapsed + 10))
        if (( elapsed >= timeout_secs )); then
            echo
            echo "     ✖ Timed out after ${timeout_secs}s waiting for the install to finish."
            echo "       Check $console_log for what's stuck, then re-run deploy.sh."
            kill "$(cat "$workdir/qemu.pid")" 2>/dev/null || true
            rm -rf "$workdir"
            exit 1
        fi
    done
    printf "\r     [%s] 100%%  (%02d:%02d elapsed)\n" "$hashes" $((elapsed/60)) $((elapsed%60))

    echo "     ✔ Install finished, shutting the VM down..."
    kill -TERM "$(cat "$workdir/qemu.pid")" 2>/dev/null || true
    sleep 5
    rm -rf "$workdir"
    echo "     ✔ Built $(basename "$qcow2")"
}

# ── Step 0: Check for CSR1000v vrnetlab image ────────────────────────────────
echo "[0/3] Checking for CSR1000v image ($CSR_IMAGE)..."
if docker image inspect "$CSR_IMAGE" &>/dev/null; then
    echo "     ✔ CSR1000v image found."
else
    echo "     ✖ CSR1000v image NOT found — attempting to build it."

    qcow2_file="$(find . -maxdepth 1 -name "$CSR_QCOW2_GLOB" -print -quit)"
    if [ -z "$qcow2_file" ]; then
        iso_file="$(find . -maxdepth 1 -name "$CSR_ISO_GLOB" -print -quit)"
        if [ -n "$iso_file" ]; then
            convert_csr_iso_to_qcow2 "$iso_file"
            qcow2_file="${iso_file%.iso}.qcow2"
        fi
    fi

    if [ -z "$qcow2_file" ]; then
        echo
        echo "     No .qcow2 or .iso found for CSR1000v."
        echo "     Build it with vrnetlab:"
        echo "       git clone https://github.com/hellt/vrnetlab.git"
        echo "       cd vrnetlab/cisco/csr1000v"
        echo "       cp /path/to/csr1000v-universalk9.16.09.05.qcow2 ."
        echo "       make"
        echo
        exit 1
    fi

    if [ ! -d vrnetlab ]; then
        echo "     Cloning vrnetlab..."
        git clone --quiet https://github.com/hellt/vrnetlab.git
    fi
    cp "$qcow2_file" vrnetlab/cisco/csr1000v/
    echo "     Building vrnetlab image from $(basename "$qcow2_file")..."
    ( cd vrnetlab/cisco/csr1000v && make )
    echo "     ✔ CSR1000v image built."
fi
echo

# ── Step 1: Build custom Linux image ─────────────────────────────────────────
echo "[1/3] Building custom Linux server image ($LINUX_IMAGE)..."
docker build -t "$LINUX_IMAGE" -f "$DOCKERFILE" .
echo "     ✔ Image built successfully."
echo

# ── Step 2: Deploy Containerlab topology ─────────────────────────────────────
echo "[2/3] Deploying Containerlab topology ($TOPO_FILE)..."
containerlab deploy -t "$TOPO_FILE" --reconfigure
echo "     ✔ Topology deployed."
echo

# ── Step 3: Print summary ────────────────────────────────────────────────────
echo "[3/3] Lab summary:"
echo
containerlab inspect -t "$TOPO_FILE"
echo
echo "============================================="
echo "  Lab is ready!  Management addresses:"
echo "    router1  → 172.20.20.11  (SSH 12201, NETCONF 12831)"
echo "    router2  → 172.20.20.12  (SSH 12202, NETCONF 12832)"
echo "    server1  → 172.20.20.21"
echo "    server2  → 172.20.20.22"
echo ""
echo "  Quick test:"
echo "    ssh admin@172.20.20.11          # router1 (CSR1000v)"
echo "    ssh root@172.20.20.21           # server1 (password: netauto)"
echo "    ansible-playbook playbooks/ping_all.yml"
echo "============================================="
