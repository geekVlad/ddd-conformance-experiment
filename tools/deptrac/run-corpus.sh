#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
deptrac="$root/tools/deptrac-runtime/vendor/bin/deptrac"
config="$root/tools/deptrac/deptrac.php"
output_dir="$root/results/deptrac"
repositories=(sylius symfony-ddd-hexarch-cqrs proophessor-do explicit-architecture-php php-engine)

mkdir -p "$output_dir"
for id in "${repositories[@]}"; do
  DEPTRAC_TARGET="$root/corpus/$id" "$deptrac" --config-file="$config" --formatter=json --no-cache \
    > "$output_dir/$id.json"
done
