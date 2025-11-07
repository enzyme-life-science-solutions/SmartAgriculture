# Experience System – Cost & CI Playbook

## CI Placement Strategy
- **What:** Split workloads so GitHub Actions handles fast lint/unit tests while heavy builds stay on Google Cloud.
- **Why:** GitHub often provides free minutes for public repos, whereas Cloud Build charges per minute—this mix keeps costs predictable.
- **Next:** Revisit the split whenever quotas change; move jobs toward the platform with more headroom.

## Cost-Guard Test Suite
- **What:** Added `tests/costing/*` to ensure normalization math and env preflight logic fail fast.
- **Why:** Catch expensive failure loops (Gemini retries, invalid spectra) before they consume cloud resources.
- **Next:** Keep expanding coverage for any workflow that can loop (e.g., future feature extraction prompts).

## Gemini Pre-flight Check
- **What:** `scripts/check_env.sh` validates env vars & auth before Gemini CLI runs.
- **Why:** Prevents repeated API retries when a single missing variable would otherwise burn quota.
- **Next:** Detect repeated CLI errors automatically and emit cost warnings.

## CI Python Alignment
- **What:** GitHub Actions now uses Python 3.14 and installs the repo via `pip install -e .`.
- **Why:** Keeps dependency behavior consistent with local dev (e.g., bleach pin), avoiding version-specific failures.
- **Next:** Monitor new Python releases; upgrade both local + CI when 3.15 stabilizes.
