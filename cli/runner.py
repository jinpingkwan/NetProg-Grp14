import ansible_runner
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_playbook(playbook: str, host: str, extra_vars: dict) -> None:
    result = ansible_runner.run(
        project_dir=str(PROJECT_ROOT),
        playbook=f"playbooks/{playbook}.yml",
        inventory=str(PROJECT_ROOT / "inventory" / "hosts.yml"),
        extravars={"target_host": host, **extra_vars},
        quiet=False,
    )
    if result.rc != 0:
        raise SystemExit(1)
