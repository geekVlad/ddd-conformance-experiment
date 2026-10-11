#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
semgrep_bin="$root/.venv-experiment/bin/semgrep"
config="$root/tools/semgrep/ddd-boundaries.yml"
output_dir="$root/results/semgrep"

mkdir -p "$output_dir"
repositories=(
  sylius symfony-ddd-hexarch-cqrs proophessor-do explicit-architecture-php php-engine
  bitloops-ddd finance-project-ddd domain-driven-hexagon ultimate-backend fastify-boilerplate
  python-ddd openvair fastapi-clean-example python-ddd-example enforcer-clean-architecture
)
for id in "${repositories[@]}"; do
  "$semgrep_bin" scan --config "$config" --json --no-git-ignore \
    --include '*.py' --include '*.php' --include '*.ts' --include '*.tsx' \
    "$root/corpus/$id" > "$output_dir/$id.json"
done
