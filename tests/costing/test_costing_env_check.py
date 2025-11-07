import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts" / "check_env.sh"


def run_script(extra_env):
    """Helper: run the pre-flight check with controlled env vars."""
    env = os.environ.copy()
    env.update(extra_env)
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
    )
    return result


def test_check_env_blocks_when_missing_values():
    """Cost guard: fail fast if required vars are absent."""
    result = run_script({"GOOGLE_CLOUD_PROJECT": "", "GOOGLE_CLOUD_LOCATION": "", "GCS_BUCKET": ""})
    assert result.returncode == 1
    assert "status: BLOCKED" in result.stdout
    assert "missing required environment values" in result.stdout


def test_check_env_ready_when_env_and_skip_flag_present():
    """Cost guard: confirm READY output when env + skip flag supplied."""
    result = run_script(
        {
            "GOOGLE_CLOUD_PROJECT": "demo-project",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GCS_BUCKET": "demo-bucket",
            "SKIP_GCLOUD_CHECK": "1",
        }
    )
    assert result.returncode == 0
    assert "status: READY" in result.stdout
