#!/usr/bin/env bash
# Write app/config.yaml's version: upstream's release number with this
# checkout's last commit appended, "0.3.3-8dfa674". Home Assistant reads it
# from this repository and offers an update whenever the string changes, so
# every commit is a version it can install, while the number before the dash
# stays upstream's.
#
#   scripts/app_version.sh [app]
#
# The commit it names is the one the source came from: committing the line
# changes nothing else. .github/workflows/version.yml runs this after each
# push to main and commits it.
set -euo pipefail

app="${1:-app}"
app="${app%/}"
test -f "${app}/config.yaml" || { echo "${app} has no config.yaml: not the app folder" >&2; exit 1; }

cd "$(dirname "$0")/.."
base="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' voice_incubator/__init__.py)"
test -n "${base}" || { echo "voice_incubator/__init__.py has no __version__" >&2; exit 1; }
version="${base}-$(git rev-parse --short HEAD)"
sed -i "s/^version: .*/version: ${version}/" "${app}/config.yaml"
echo "${version} -> ${app}/config.yaml"
