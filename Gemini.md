# Agents Guide

<!-- What changed: Guidance originated under GenomeServices; mirrored here so
     SmartAgriculture agents follow the same 27001/13485/62304 controls. -->

This document defines conventions for AI agents collaborating on the SmartAgriculture repository (carrying forward GenomeServices standards).

## Repository Layout
- `data/` – raw HSI (`.hdr/.bil`).
- `data_processed/` – derived CSV artifacts.
- `scripts/` – operational helpers (parse/export/self_check/sync).
- `src/smart_agriculture/` – shared config + libraries.
- `docs/`, `notebooks/`, `tests/`, `build/`, `remote-kernel/`, `test_env/` – documentation, research, validation, and tooling workspaces.

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

## Testing Responsibilities (cost-aware)
- `pytest tests/test_features_indices.py` – keeps vegetation index math deterministic.
- `pytest tests/test_check_env.py` – ensures the Gemini env pre-check behaves without making API calls.
- `python scripts/self_check.py` – executes the HSI self-check harness before promoting builds.

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

## Status Tracking
| Service | Description | Status | Next Step |
|---------|-------------|--------|-----------|
| VariantEffectService | Variant effect prediction API | Deploy pipeline substitution fix applied | integrate real model |

## Progress Log
- Initial repository scaffolding: README, LICENSE, .gitignore, docs, CI workflow.
- Added `VariantEffectService` with FastAPI endpoints, tests, docs, and Dockerfile.
- Refactored `VariantEffectService` endpoints and tests to async/await for concurrency readiness; updated CI dependencies.
- Updated repository metadata and CI workflow.
- Documented naming conventions and developer guidelines.
- Restored digest lookup guard in `VariantEffectService` Cloud Build to fail on unresolved image digest (ISO/IEC 27001 integrity).
- Aligned CI/CD to main build and deploy branch with approval and digest pinning; updated docs and diagram.
- Adopted Cloud Deploy pipeline with PR build and merge-to-deploy release; added configs and docs.
- Corrected PR build step ID to comply with Cloud Build requirements (ensures CI job runs).
- Escaped runtime variables in `cloudbuild.deploy.yaml` to prevent invalid Cloud Build substitutions (ISO/IEC 27001 integrity).
- Introduced doc-driven task queue SOP, templates, and extractor script to keep documentation as the audit trail (IEC 62304, ISO 13485, ISO 14971, ISO/IEC 27001).
- Authored `TASKS_AND_DOCS.md` as the unified entrypoint for documentation↔queue lifecycle to onboard agents consistently (IEC 62304, ISO 13485).
- Hardened `parse_inventory.py` with config-driven paths, dataset citation, and compliance logging to preserve ISO 13485 / IEC 62304 traceability of the hyperspectral dataset.
- Added dataset sync CLI + helper to push `data/tomato_leaf` into `GCS_BUCKET` using substitution-friendly settings, plus enzyme_tech shim so pytest covers GCS uploads end-to-end.

## Suggested Next Step
- Pilot the doc-driven task extractor across active services and capture feedback for incremental automation hardening.

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

# Gemini Code Assist — Project Notes

## Purpose
Automate generation and validation of the Smart Agriculture hyperspectral (HSI) pipeline via Gemini Code Assist in VS Code or the CLI.

## Core Prompts (docs/prompts.md)
1. ✅ Config & inventory (`config.py`, `scripts/parse_inventory.py`)
2. ✅ Spectral normalization (`scripts/export_spectra.py`)
3. ✅ Self-check validation (`scripts/self_check.py`)
4. 🔄 Feature extraction (`scripts/features.py`)
5. 🔄 ML training notebook (`notebooks/02_model_v1.ipynb`)

## Usage
**VS Code:** `Ctrl+I` → *Gemini: Run Prompt* → pick the phase prompt block.  
**CLI:**
```bash
gemini projects set smartagriculture
gemini run --file prompts/export_spectra.txt
```

### Environment
```
PROJECT_ID=<gcp-project>
BUCKET=${PROJECT_ID}-smartagri
```

### Cloud Integration
- `scripts/sync_data.sh up|down` keeps `/data` ↔ `/data_processed` in sync.
- Gemini CLI can call `gcloud storage rsync` once the user is authenticated.

### Standards Reference
- IEC 62304 – lifecycle traceability for each generated artifact.
- ISO 14971 – calibration/risk checks baked into prompts.
- ISO/IEC 27001 – no secrets in prompts; use substitutions and env vars.

## TODO
- Add automatic Gemini run triggers post-merge (GitHub Actions / Vertex CI).
- Implement `scripts/features.py` agent plus Gemini prompt coverage for feature extraction.
- Add Looker dashboard prompt + upload agent so analytics stay aligned with data drops.
- Emit notifications when `self_check` reports FAIL.
- Define a Vertex AI job template to automate the full pipeline.
- Integrate Gemini evaluation to compare `self_check` PASS rate across runs.
- Add automated detection for cost-heavy CLI retries (warn when Gemini keeps retrying the same failure).
