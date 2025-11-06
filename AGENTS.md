# Agents Guide

<!-- What changed: Renamed project to GenomeServices. Added rules for inline
     rationale comments, substitution naming, and clarified Build vs Runtime SA
     separation to meet 27001/13485/62304. -->

This document defines conventions for AI agents collaborating on the GenomeServices repository.

## Microservices Architecture Rules
- Services live under `services/<name>`.
- Each service contains:
  - `src/` – application code
  - `tests/` – pytest suite
  - `docs/` – service documentation
  - `Dockerfile` – container definition

## Folder Structure Template
```
services/
└── <ServiceName>/
    ├── src/
    ├── tests/
    ├── docs/
    └── Dockerfile
```

## Agent Responsibilities
- Maintain documentation and follow coding standards.
- Run `pytest` before committing.
- Update this file with progress notes and next steps.
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

## Suggested Next Step
- Pilot the doc-driven task extractor across active services and capture feedback for incremental automation hardening.

## Microservice Status
| Service | Status |
|---------|--------|
| VariantEffectService | Deploy pipeline substitution fix applied |

## Project Tree
```
.
├── .github
│   └── workflows
│       └── ci.yml
├── .gitignore
├── AGENTS.md
├── LICENSE
├── README.md
├── clouddeploy
│   ├── pipeline.yaml
│   └── targets.yaml
├── docs
│   ├── COMPLIANCE_MATRIX.md
│   ├── PROJECT_INSTRUCTIONS.md
│   └── STANDARDS_REFERENCES.md
├── TASKS_AND_DOCS.md
└── services
    ├── __init__.py
    └── VariantEffectService
        ├── Dockerfile
        ├── __init__.py
        ├── cloudbuild.deploy.yaml
        ├── cloudbuild.pr.yaml
        ├── cloudbuild.yaml
        ├── docs
        │   └── README.md
        ├── requirements.txt
        ├── src
        │   ├── __init__.py
        │   └── main.py
        └── tests
            ├── __init__.py
            └── test_main.py
```

## Data Citation Style
When citing the hyperspectral imaging data, use the following format:
Li, S., 2024. Data from: Hyperspectral Imaging Analysis for Early Detection of Tomato Bacterial Leaf Spot Disease. https://doi.org/10.15482/USDA.ADC/26046328.v2