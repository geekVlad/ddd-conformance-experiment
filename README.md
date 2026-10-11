# DDD analyzers

Source code and executable configurations for reproducing structural Domain-Driven Design analysis of PHP, TypeScript, and Python repositories.

## Contents

- `src/ddd_conformance/`: language adapters, structural metrics, path-policy induction, role/context inference, dependency verdicts, and optional LLM adjudication.
- `tests/`: automated tests of the implementation.
- `data/repositories.yaml`: corpus URLs, immutable revisions, licenses, and recorded environment metadata.
- `scripts/`: reproduction and optional adjudication entry points.
- `tools/`: Semgrep and Deptrac rules, runtime dependency locks, and policy templates.
- `pyproject.toml`, `uv.lock`: Python package/dependency configuration.

Third-party repository contents and generated results are not tracked. Downloaded sources remain subject to their original licenses.

## Setup and tests

Requirements: Git, `uv`, and Python 3.12.3 for the recorded baseline environment (the package supports Python >=3.11).

```bash
UV_PROJECT_ENVIRONMENT=.venv-experiment uv sync --frozen --all-groups --python 3.12.3
.venv-experiment/bin/python -m pytest
.venv-experiment/bin/ruff check src tests scripts
```

## Reproduce structural analysis

The runner fetches and checks out each accepted manifest revision, checks the actual SHA, and executes the unchanged analyzer modules. It writes JSON/YAML outputs and summaries under ignored `results/`.

```bash
.venv-experiment/bin/python scripts/reproduce.py
```

A selected repository, or an existing pinned checkout:

```bash
.venv-experiment/bin/python scripts/reproduce.py --repository python-ddd
.venv-experiment/bin/python scripts/reproduce.py --repository python-ddd --skip-fetch
```

The base parser, path-policy inducer, and architecture agent are independent procedures. File-selection rules differ, so their counts need not match. In particular, policy induction is not an input-policy handoff to the architecture agent. Unresolved targets and uncertain decisions are retained; confidence is not a calibrated probability or validated detection accuracy.

Analyze another repository without using the corpus runner:

```bash
.venv-experiment/bin/ddd-analyze /path/to/repository --output results/report.json
```

## External rules

Semgrep (recorded version: 1.74.0):

```bash
uv pip install --python .venv-experiment/bin/python 'semgrep==1.74.0'
bash tools/semgrep/run-corpus.sh
```

Deptrac (requires PHP and Composer; dependencies are locked in `tools/deptrac-runtime/composer.lock`):

```bash
composer install --working-dir=tools/deptrac-runtime
bash tools/deptrac/run-corpus.sh
```

External findings and agent verdicts have different observation units and rule sets; they are not interchangeable labels.

## Optional LLM adjudication

See `scripts/build_adjudication_sample.py --help`, `scripts/adjudicate_candidate.py --help`, and `tools/llm-adjudicator/` for inputs and fixed policy examples. API keys are read only from `EDUCATION_OPENAI_API_KEY` or `OPENAI_API_KEY` environment variables. Never commit credential values.

LLM output is a separate optional observation, not an automatic rewrite of structural policy. Exact historical provider snapshots and per-call execution records are not available; rerunning a model alias does not guarantee identical historical responses, even at temperature zero.

## License

The implementation is released under [MIT](LICENSE). Corpus repositories retain their own licenses listed in the manifest.
