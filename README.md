# VC Research Copilot

An evidence-first research copilot for VC analysts. Investment judgment stays with the analyst.

[SPEC.md](SPEC.md) is the approved product and architecture specification. **Step 1 is implemented:** typed contracts, synthetic evidence fixtures, offline provider replay and tests. No live research, API server, PostgreSQL persistence, budget controller, financial execution engine or product UI exists yet.

## Open and inspect in VS Code

Open this existing directory using **File → Open Folder**. Use the integrated terminal:

```sh
cd "/Users/sacharichelme/Documents/ChatGPT/VC ANALYST AI"
git status --short --branch
git log --oneline -5
find backend/src backend/tests examples/demo evals docs -type f -not -path '*/__pycache__/*'
```

## Run Step 1 on this checkout

The repository-local `.venv` is already installed. No activation, credentials, database,
Node installation, Docker or cloud service is needed to run these tests:

```sh
cd "/Users/sacharichelme/Documents/ChatGPT/VC ANALYST AI"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c backend/pyproject.toml backend/tests
```

Run only the offline fixture demonstration/tests:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c backend/pyproject.toml backend/tests/test_fixtures.py -v
```

This validates fixture graphs and replays search/model responses; it is not a working
interactive demo of the eventual application. No default test sends a paid request.

## Recreate the environment if necessary

Use a normal Python **3.12 or newer** installation; the Mac system Python 3.9 is too old.
With Python 3.12 installed and on PATH, run from this repository root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.lock
.venv/bin/python -m pip check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c backend/pyproject.toml backend/tests
```

On this Mac, the first environment was bootstrapped with the available interpreter at
`/Users/sacharichelme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.
That absolute path can replace `python3.12` in the first command while it exists. It is
not required by the source code; a standard Python installation is sufficient. Like any
venv, `.venv` depends on its base interpreter remaining available; recreate it if the
interpreter is removed. No proprietary IDE is required.

Dependency installation uses the package registry; running the installed tests is offline.
All direct/transitive test dependencies are pinned in `backend/requirements-dev.lock`.
pytest's configuration adds `backend/src` to the import path; no editable install is needed.
Select `.venv/bin/python` as VS Code's Python interpreter if using its Python extension.

## Source map

- `backend/src/vc_research/domain/`: evidence, missing values, research/run, memo, thesis, relationship, correction, budget and routing contracts.
- `backend/src/vc_research/providers/`: small provider interfaces and demo-only replay.
- `backend/src/vc_research/fixtures.py`: referential/hash/excerpt integrity for synthetic bundles.
- `backend/src/vc_research/materiality.py`: conservative material-claim policy.
- `backend/src/vc_research/calculations.py`: exact-version calculation registry contracts; no execution.
- `backend/tests/`: offline unit/contract/fixture tests and network guard.
- `examples/demo/`: labeled original synthetic data and provider transcripts.
- `evals/`: development case manifest and human evaluation definitions, not benchmark claims.
- `docs/decisions/`: important design decisions and current limitations.

Pydantic's `model_json_schema()` exposes machine-readable contracts when needed; generated
frontend types will be introduced with the API/UI integration, not maintained in duplicate now.

## Services and safety

There are **no Step 1 services to start or stop**, migrations to run, scheduled tasks or
application logs. Tests finish normally; Ctrl+C stops them. PostgreSQL/worker setup is
Step 2, pending separate approval. Backend/frontend launch commands will be documented
when those components exist. Do not start the old scaffold to run Step 1.

Live adapters are absent, and configuration rejects enabling live operations. Credentials
in your environment do not enable execution. `.env.example` contains no secrets and is
not automatically loaded. Never put real credentials in examples, fixtures or Git.

The root `.gitignore` excludes environments, credentials, runtime state and generated
artifacts. Pattern-based secret scanning reduces risk but does not guarantee that every
possible secret can be detected; inspect changes before committing. Nothing has been pushed.

## Preserved scaffold

`platform/` is the inactive Sites/Vinext scaffold created before architecture approval.
It is preserved unchanged, including source and lockfile. Its old README/deployment
instructions are not the workflow for this project. Installed modules, local Site identity
and runtime state are ignored. The approved React/Vite frontend will be addressed at its
implementation step without silently deleting this work.
