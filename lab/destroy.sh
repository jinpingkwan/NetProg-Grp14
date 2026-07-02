#!/usr/bin/env bash
# =============================================================================
# destroy.sh — Tear down the NetAuto Containerlab topology
# =============================================================================
# Usage:  bash destroy.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TOPO_FILE="netauto-lab.clab.yml"

if [ -z "${DOCKER_HOST:-}" ] && [ ! -S /var/run/docker.sock ] && [ -S "$HOME/.docker/desktop/docker.sock" ]; then
    export DOCKER_HOST="unix://$HOME/.docker/desktop/docker.sock"
fi

echo "============================================="
echo "  NetAuto Lab — Destroy"
echo "============================================="
echo

echo "Destroying Containerlab topology ($TOPO_FILE)..."
containerlab destroy -t "$TOPO_FILE" --cleanup
echo
echo "  ✔ Lab destroyed and cleaned up."
echo "============================================="
