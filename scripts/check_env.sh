#!/usr/bin/env bash
# Verifies that the minimum Gemini/GCP environment variables are available before
# running any CLI prompts. Exiting early prevents costly API retries (IEC 62304),
# enforces least privilege (ISO/IEC 27001), and keeps TODO status consistent.

set -euo pipefail

REQUIRED_VARS=(
  GOOGLE_CLOUD_PROJECT
  GOOGLE_CLOUD_LOCATION
  GCS_BUCKET
)

missing=()
for var in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    missing+=("$var")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  cat <<BLOCK
[Gemini CLI]
status: BLOCKED
reason: missing required environment values
missing: ${missing[*]}
actions:
  - source your .env (e.g., "source .env") or export the values manually
  - rerun scripts/check_env.sh before calling "gemini ..."
notes:
  - env vars are scoped per shell; reopen terminals reset them
  - canonical values live in .env under version control
BLOCK
  exit 1
fi

if ! gcloud auth print-access-token >/dev/null 2>&1; then
  cat <<'BLOCK'
[Gemini CLI]
status: BLOCKED
reason: gcloud auth not active for this shell
actions:
  - run "gcloud auth application-default login" (or activate service account)
  - rerun scripts/check_env.sh
notes:
  - Gemini CLI relies on Application Default Credentials when no API key is set
BLOCK
  exit 1
fi

cat <<'BLOCK'
[Gemini CLI]
status: READY
message: environment and gcloud auth detected; safe to run Gemini commands.
next:
  - gemini run --file prompts/...
BLOCK
