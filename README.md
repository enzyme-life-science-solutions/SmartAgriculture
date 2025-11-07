# SmartAgriculture

<!-- What changed: Reframed the SmartAgriculture project to mirror the GenomeServices documentation template while aligning to GCP agritech pipelines that blend genomics, AI agents, and remote sensing intelligence. -->

SmartAgriculture is a research platform that explores how Google Cloud–native pipelines can integrate genome analytics, AI-driven orchestration, and remote sensing feeds to deliver actionable agronomic insights at scale.

## Overview
- End-to-end pipelines unify genome sequencing analysis with field telemetry and imagery.
- AI agents coordinate workflows, detect anomalies, and recommend interventions.
- Cloud-first architecture (Vertex AI, Cloud Life Sciences, Dataflow, BigQuery, Cloud Run) ensures secure, scalable operations.
- MIT License (placeholder) pending downstream compliance review and collaboration agreements.

## Branch & Pipeline
- **Branches**
  - `main` → CI only (build + test + package python distribution tagged with `$COMMIT_SHA`).
  - `deploy` (default) → Manual-approval release to Cloud Run / Composer environments using `_RUNTIME_SA`.
- **Substitutions**: `_REGION`, `_GCS_PIPELINES_BUCKET`, `_ARTIFACT_REGISTRY_REPO`, `_RUNTIME_SA`, `_REMOTE_SENSING_TOPIC` configured in trigger definitions (Console), not YAML.
- **Compliance**: field data governance (ISO/IEC 27001), workflow traceability (IEC 62304), controlled release cycles (ISO 13485), privacy commitments for genomic data (HIPAA/GDPR).

```mermaid
flowchart LR
  A[PR to main] -->|Code review| B[Merge main]
  B --> C[Cloud Build (main): tests + build + publish :COMMIT_SHA pkg]
  C --> D[Artifact Registry (python + container)]
  D --> E[Merge/cherry-pick to deploy branch]
  E --> F[Cloud Build (deploy): assemble infra plan + resolve artifact digest]
  F --> G{Manual approval}
  G -->|Approved| H[Deploy pipelines\nComposer / Dataflow / Cloud Run\nRuntime SA = ${_RUNTIME_SA}]
  G -->|Rejected| I[Stop rollout]
```

*Main branch guarantees tested artifacts. Deploy branch enforces human approval and digest-based releases into Google Cloud environments. Substitutions remain external to preserve security baselines.*

## CI/CD Overview
- CI stage runs pytest, validates linting, and publishes artifacts tagged with `$COMMIT_SHA`.
- CD stage rolls out Composer DAG updates, Dataflow templates, and Cloud Run agents using artifact digests.
- Release gates require manual approval from agritech operations and data governance stakeholders.
- Sensitive identifiers (topics, buckets, service accounts) are injected via substitutions rather than stored in source.

## Pipeline at a Glance
- PR → run tests + static analysis + dry-run infra plan (no deployments). Why: IEC 62304 verification, ISO 13485 change control.
- Merge to `main` → package Python modules + build container images + upload Dataflow templates with `$COMMIT_SHA` tags. Why: traceability across data pipelines.
- Promote to `deploy` → approval gate → deploy by digest, update Composer DAGs, refresh Vertex AI endpoints, re-scan IAM bindings. Why: deterministic releases, least privilege enforcement.
- Default environment values (`_REGION`, `_GCS_PIPELINES_BUCKET`, `_ARTIFACT_REGISTRY_REPO`, `_RUNTIME_SA`, `_REMOTE_SENSING_TOPIC`) derive from Cloud Build trigger settings.

## Pipeline spotlight — Early detection of tomato bacterial leaf spot

- **Objective**: Detect tomato bacterial leaf spot before visible canopy damage, enabling targeted treatment and reduced crop loss.
- **Data sources**
  - Whole-genome sequencing of pathogen isolates captured in field scouting kits (Cloud Life Sciences pipelines).
  - Hyperspectral and RGB imagery from drones/Edge TPU cameras streaming through Pub/Sub and Dataflow.
  - IoT telemetry (humidity, leaf wetness, temperature) pushed into BigQuery tables for contextual features.
- **Workflow outline**
  1. **Ingestion**: Pub/Sub topics ingest imagery metadata; Dataflow jobs tile images and store derived indices (NDVI, PRI) in BigQuery + Cloud Storage. IoT telemetry arrives via Cloud IoT Core replacement (Pub/Sub bridges).
  2. **Genomics**: Cloud Life Sciences pipelines perform read alignment and pathogen variant calling; outputs normalized to BigQuery and Vertex AI Feature Store.
  3. **Feature fusion**: Vertex AI Feature Store jobs merge genomic markers, spectral signatures, and microclimate signals.
  4. **AI agent**: Vertex AI Agent triggers model scoring (AutoML / custom model) to predict infection risk; annotates hotspots and writes advisories to Firestore and Looker dashboards.
  5. **Alerting**: Cloud Functions / Cloud Run services notify agronomists and update farm management systems with recommended interventions.
- **Success metrics**
  - Detection lead time ≥ 3 days before visual symptoms.
  - ≥ 90% precision in hotspot identification on validation plots.
  - Automated report latency ≤ 30 minutes from data capture.
- **Next steps**
  - Curate labeled datasets (historical imagery + lab-confirmed cases).
  - Define Vertex AI pipeline for training/serving spectral-genomic fusion models.
  - Prototype the Composer DAG overseeing ingestion, genomics, and scoring stages.

### Cloud Build (CI) snippet
```yaml
substitutions:
  _REGION: "<REGION>"
  _ARTIFACT_REGISTRY_REPO: "<ARTIFACT_REPO>"
steps:
- id: tests
  name: gcr.io/cloud-builders/python
  entrypoint: bash
  args:
    - -lc
    - |
      python -m venv .venv
      source .venv/bin/activate
      pip install -e .[dev]
      pytest
- id: build-container
  name: gcr.io/cloud-builders/docker
  args:
    - build
    - -t
    - ${_REGION}-docker.pkg.dev/$PROJECT_ID/${_ARTIFACT_REGISTRY_REPO}/smart-agents:$COMMIT_SHA
    - .
- id: push-container
  name: gcr.io/cloud-builders/docker
  args:
    - push
    - ${_REGION}-docker.pkg.dev/$PROJECT_ID/${_ARTIFACT_REGISTRY_REPO}/smart-agents:$COMMIT_SHA
```

### Cloud Build (CD) snippet
```yaml
substitutions:
  _REGION: "<REGION>"
  _ARTIFACT_REGISTRY_REPO: "<ARTIFACT_REPO>"
  _RUNTIME_SA: "<RUNTIME_SA>"
  _REMOTE_SENSING_TOPIC: "<PUBSUB_TOPIC>"
steps:
- id: resolve-digest
  name: gcr.io/google.com/cloudsdktool/cloud-sdk
  args:
    - bash
    - -lc
    - |
      IMAGE_BASE="${_REGION}-docker.pkg.dev/$PROJECT_ID/${_ARTIFACT_REGISTRY_REPO}/smart-agents"
      DIGEST=$(gcloud artifacts docker images describe "${IMAGE_BASE}:${COMMIT_SHA}" --format='value(image_summary.digest)')
      echo IMAGE_BY_DIGEST=${IMAGE_BASE}@${DIGEST} > /workspace/digest.env
- id: deploy-runtime
  name: gcr.io/google.com/cloudsdktool/cloud-sdk
  args:
    - bash
    - -lc
    - |
      source /workspace/digest.env
      gcloud run deploy smart-agents --image="$IMAGE_BY_DIGEST" --region="${_REGION}" --service-account="${_RUNTIME_SA}" --no-allow-unauthenticated --quiet
- id: update-composer
  name: gcr.io/google.com/cloudsdktool/cloud-sdk
  args:
    - bash
    - -lc
    - |
      gcloud composer environments storage dags import \
        --location "${_REGION}" \
        --environment smart-agriculture-composer \
        --source dags/
```

## Project Structure

```
SmartAgriculture/
├── .gitignore
├── AGENTS.md
├── Gemini.md
├── LICENSE
├── pyproject.toml
├── README.md
├── TASKS_AND_DOCS.md
├── configs/
│   └── sample_config.json
├── data/
│   └── .gitkeep
├── docs/
│   └── .gitkeep
├── notebooks/
│   └── .gitkeep
├── scripts/
│   └── .gitkeep
├── src/
│   └── smart_agriculture/
│       ├── __init__.py
│       ├── cli.py
│       └── pipelines/
│           ├── __init__.py
│           └── gcs_utils.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_cli.py
    └── test_gcs_utils.py
```

## Development instructions
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
smart-agriculture
```

The CLI currently emits placeholder insights from `configs/sample_config.json`. Replace it with connectors to BigQuery tables, Vertex AI models, or Pub/Sub topics as the pipelines mature.

## How to run

```bash
python scripts/self_check.py
```

- **What/Why/Standard**: Executes the HSI self-check harness to ensure the parse→export flow remains reproducible (IEC 62304), detects calibration drift early (ISO 14971), and keeps evidence on local storage with no secret material (ISO/IEC 27001).
- **Expected outputs**
  - `data_proc/hsi_meta.csv` mirrored metadata for auditors.
  - ≥3 `data_processed/*_spectrum.csv` files with normalized VISNIR/SWIR spectra.
  - `reports/trace_log.txt` appended with a `self_check` line documenting the run.
  - Console table summarizing meta rows, sensor counts, timepoints, and pass/fail status.
- **Common failures and fixes**
  - Empty `data/tomato_leaf`: populate the raw HSI folders with matching `.hdr/.bil` pairs and rerun.
  - Missing cloth captures: acquire cloth reference files so normalization can keep VISNIR/SWIR means in range.
  - Non-monotonic wavelengths or NaN reflectance: inspect the offending `_spectrum.csv` file for corrupt ENVI headers.
  - Fewer than three spectra: verify the export step produced both sensor families and that filenames end with `_spectrum.csv`.

## Compliance Notes
- Least privilege: Separate build and runtime service accounts; runtime SA injected via substitutions (ISO/IEC 27001).
- Traceability: Commit SHA → artifact digest → deployed DAG/container version (IEC 62304, ISO 13485).
- Privacy: Genomic and field telemetry stored in regional buckets with CMEK and access monitoring (HIPAA/GDPR alignment).
- Observability: Cloud Logging, Cloud Monitoring, and Security Command Center enable audit trails across pipelines.

## Roadmap
- Terraform modules for Composer, Dataflow, Vertex AI, BigQuery, and Pub/Sub.
- Implement WDL/CWL pipelines for genomic analysis via Cloud Life Sciences.
- Stand up remote sensing ingestion jobs with Dataflow + Earth Engine exports.
- Develop AI agent behaviors for decision support and irrigation/fertility planning.
- Introduce synthetic datasets and automated regression tests for insight quality.
- Extend detection playbooks to additional pathogens and crops using the tomato pipeline as a pattern.

## Disclaimer
Research use only. Not validated for clinical or production agronomy decisions without further certification and stakeholder review.
