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

echo "============================================="
echo "  NetAuto Lab — Deploy"
echo "============================================="
echo

# ── Step 0: Check for CSR1000v vrnetlab image ────────────────────────────────
echo "[0/3] Checking for CSR1000v image ($CSR_IMAGE)..."
if docker image inspect "$CSR_IMAGE" &>/dev/null; then
    echo "     ✔ CSR1000v image found."
else
    echo "     ✖ CSR1000v image NOT found!"
    echo
    echo "     Build it with vrnetlab:"
    echo "       git clone https://github.com/hellt/vrnetlab.git"
    echo "       cd vrnetlab/cisco/csr1000v"
    echo "       cp /path/to/csr1000v-universalk9.16.09.05.qcow2 ."
    echo "       make"
    echo
    exit 1
fi
echo

# ── Step 1: Build custom Linux image ─────────────────────────────────────────
echo "[1/3] Building custom Linux server image ($LINUX_IMAGE)..."
docker build -t "$LINUX_IMAGE" -f "$DOCKERFILE" .
echo "     ✔ Image built successfully."
echo

# ── Step 2: Deploy Containerlab topology ─────────────────────────────────────
echo "[2/3] Deploying Containerlab topology ($TOPO_FILE)..."
sudo containerlab deploy -t "$TOPO_FILE" --reconfigure
echo "     ✔ Topology deployed."
echo

# ── Step 3: Print summary ────────────────────────────────────────────────────
echo "[3/3] Lab summary:"
echo
sudo containerlab inspect -t "$TOPO_FILE"
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
