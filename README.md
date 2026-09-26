# VC Research Copilot

An evidence-first research copilot for VC analysts. Investment judgment stays with the analyst.

[SPEC.md](SPEC.md) is the approved product and architecture specification. Implementation is limited to Step 1 (contracts and offline fixtures); no live research, backend server, database worker or product frontend exists yet.

The existing `platform/` directory is a preserved, inactive Sites/Vinext scaffold from before architecture approval. Its deployment instructions are not the development workflow for this project. Local Site identity, installed modules and runtime state are excluded from Git. The approved React/Vite frontend will be addressed in its implementation step, without silently replacing this scaffold.

Open this repository root in VS Code. Source, fixtures and documentation live here; generated local state belongs in ignored `.venv/` or `.local/`. No remote IDE or cloud service is required.

Step 1 setup and test commands will be documented alongside implementation. No service should be started or deployed from this initial checkpoint.
