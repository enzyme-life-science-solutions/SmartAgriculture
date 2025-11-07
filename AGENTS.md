# Agents Guide

<!-- What changed: Guidance originally authored for GenomeServices; aligned here
     to SmartAgriculture while preserving the same compliance controls (27001/13485/62304). -->

This document defines conventions for AI agents collaborating on the SmartAgriculture repository (inherits GenomeServices guardrails).

## Repository Layout
SmartAgriculture is a single HSI research pipeline, not a multi-service mono-repo. Ownership is split by top-level folders:
- `data/` – raw hyperspectral inputs (`.hdr/.bil`) and metadata drops.
- `data_processed/` – generated CSV outputs (`hsi_meta.csv`, `*_spectrum.csv`).
- `scripts/` – operational agents (`parse_inventory.py`, `export_spectra.py`, `self_check.py`, `sync_data.sh`).
- `src/smart_agriculture/` – reusable Python packages/config shared by scripts and tests.
- `docs/` – compliance guidance, deployment notes, prompt catalog.
- `notebooks/` – exploratory/ML notebooks.
- `tests/` – pytest suite covering shared modules.
- `build/`, `remote-kernel/`, `test_env/` – tooling scratchpads (leave untouched unless coordinated).

## Agent Responsibilities
- Maintain documentation and follow coding standards.
- Run `pytest` before committing.
- Update this file with progress notes and next steps.
- Keep TODO entries synchronized across AGENTS.md and GEMINI.md (#TODO rule) so agents see a single source of truth.
- Ensure work aligns with IEC 62304, ISO 13485 and ISO/IEC 27001.
- Add inline comments explaining WHY decisions are made, with references to
  applicable standards when relevant (e.g., 27001, 13485, 62304).
- All YAML must use substitutions for environment values; do not hardcode
  service accounts, buckets, or repository names. Define `_REGION`, `_AR_REPO`,
  `_IMAGE_NAME`, `_RUNTIME_SA`, `_EVIDENCE_BUCKET` in triggers.
- Each YAML/doc must include “what/why/standard” comments to support audits.
- Separation of identities: Build SA (triggers) != Runtime SA (Cloud Run). Do
  not use the Runtime SA in triggers; pass it via `_RUNTIME_SA` substitution.

## Quick Rules
- Never hardcode environment identifiers; use trigger substitutions.
- Build SA (trigger SA) ≠ Runtime SA.
- Each YAML/doc must include WHY comments tied to standards.

## Naming Conventions
| Context            | Convention        | Example                   | Rationale |
|--------------------|------------------|---------------------------|-----------|
| Repository folder  | PascalCase       | `VariantEffectService`    | Matches class/module style in codebases (Python/Java). Easier to associate with service responsibility. |
| Docker image name  | kebab-case       | `variant-effect-service`  | Required for Artifact Registry, Docker, and K8s (lowercase DNS-compliant). |
| Cloud Run service  | kebab-case       | `variant-effect-service`  | Cloud Run/K8s enforce lowercase + hyphens. |
| URLs               | kebab-case       | `/variant-effect-service` | Readable and consistent with REST/HTTP norms. |

**Rule:** Always use `VariantEffectService` inside the repo. Always use `variant-effect-service` for deployment artifacts, containers, and URLs.

### Substitution Naming (Cloud Build)
- Use leading underscore + UPPER_SNAKE_CASE (e.g., `_RUNTIME_SA`, `_EVIDENCE_BUCKET`).
- Common set:
  - `_REGION`, `_AR_REPO`, `_IMAGE_NAME` (non-sensitive build context)
  - `_RUNTIME_SA` (runtime identity; never hardcode)
  - `_EVIDENCE_BUCKET` (optional audit bucket)
  - `_TAG` (deploy reference; defaults to `$COMMIT_SHA`)

## Deployment Approach
- Build Docker images with Google Cloud Build.
- Push images to Google Artifact Registry.
- Retrieve secrets from Google Secret Manager.

### Separation of Concerns: Build vs Runtime Identity
- Build SA: Cloud Build service account with permissions to build/push images and
  read substitutions. It must NOT be used to run services.
- Runtime SA: Dedicated Cloud Run service account used only to execute the
  service. It should have the minimum runtime permissions required.
- Rationale: ISO/IEC 27001 (least privilege) and ISO 13485 (separation of responsibilities).

## CI/CD Conventions
- **Build Pipeline (`cloudbuild.yaml`):**
  - **Purpose:** Build and push a container image for a specific service.
  - **Trigger:** Runs automatically on code changes to a service's directory.
  - **Artifact:** A Docker image tagged with `$COMMIT_SHA` pushed to the `_AR_REPO` Artifact Registry repository.
  - **Rationale:** Provides rapid feedback and ensures every change produces a traceable, testable artifact.

- **Deploy Pipeline (`cloudbuild.deploy.yaml`):**
  - **Purpose:** Deploy a *specific, pre-built* container image to an environment.
  - **Trigger:** Manual execution only, requiring human approval.
  - **Parameters:** Requires an `_IMAGE_REF` (full Artifact Registry path to an image) at runtime.
  - **Rationale:** Enforces controlled release management (IEC 62304, ISO 13485), separating the act of building from the act of deploying. This prevents untested code from reaching production environments.

- **Roadmap:** Future iterations will integrate secrets from Secret Manager and assign least-privilege service accounts during deployment (ISO/IEC 27001).
- **Post-merge automation:** Add GitHub Actions / Vertex CI triggers that run the Gemini self-check prompts after merges to keep evidence fresh.

## Branch Status
| Branch | Purpose |
|--------|---------|
| main   | Build + push image (CI) |
| deploy | Deploy by digest with approval |


## Microservice Status
| Service | Status |
|---------|--------|
| VariantEffectService | Deploy pipeline substitution fix applied |

## Project Tree (excerpt)
```
SmartAgriculture/
├── AGENTS.md
├── GEMINI.md
├── README.md
├── TASKS_AND_DOCS.md
├── data/
├── data_processed/
├── docs/
├── notebooks/
├── scripts/
│   ├── parse_inventory.py
│   ├── export_spectra.py
│   ├── self_check.py
│   └── sync_data.sh
├── src/
│   └── smart_agriculture/
├── tests/
└── requirements.txt
```

## Data Citation Style
When citing the hyperspectral imaging data, use the following format:
Li, S., 2024. Data from: Hyperspectral Imaging Analysis for Early Detection of Tomato Bacterial Leaf Spot Disease. https://doi.org/10.15482/USDA.ADC/26046328.v2

---

# Agent — Automation & Oversight Guide

## Overview
Gemini CLI + lightweight Python agents orchestrate:
- Local preprocessing (`scripts/parse_inventory.py`)
- Spectral normalization (`scripts/export_spectra.py`)
- Validation & trace (`scripts/self_check.py`)
- Cloud sync helpers (`scripts/sync_data.sh`)

## Execution Flow
```
data/tomato_leaf → parse_inventory → export_spectra → self_check → data_processed/
```

## Local Run
```bash
python scripts/parse_inventory.py
python scripts/export_spectra.py
python scripts/self_check.py
```

## Cloud Sync
```bash
make sync-up-raw
make sync-up-proc
```

## Logging & Compliance
- Every stage appends to `reports/trace_log.txt`.
- Scripts emit `[OK]`, `[ERR]`, `[DONE]` for ISO 13485 traceability.
- All timestamps are UTC ISO-8601; no secrets or PII are logged.

## Fail-Safe Normalization Policy
When cloth reference lookups fail, normalization cascades:
1. Use D0 baseline spectra (`BASELINE`).
2. Else use z-score normalization (`ZSCORE`).
3. Otherwise apply cloth normalization (`CLOTH`).
Persist chosen mode in `norm_mode_used` for audits.

## TODO
- Add automatic Gemini run triggers post-merge (GitHub Actions / Vertex CI).
- Implement `scripts/features.py` agent plus Gemini prompt coverage for feature extraction.
- Add Looker dashboard prompt + upload agent so analytics stay aligned with data drops.
- Emit notifications when `self_check` reports FAIL.
- Define a Vertex AI job template to automate the full pipeline.
- Integrate Gemini evaluation to compare `self_check` PASS rate across runs.
