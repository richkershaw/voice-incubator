#!/usr/bin/env bash
# Write app/config.yaml's version: upstream's release number with a build
# number after it, "0.3.5.42", the count of commits. Home Assistant enables its
# update when the new version is newer, which a build number always is; a
# commit id after a dash is not -- 0.3.5-abc does not compare newer than
# 0.3.5-def. The number before the build stays upstream's.
#
#   scripts/app_version.sh [app]
#
# The build number names the commit the source came from; the stamp commit's
# message says which. .github/workflows/version.yml runs this after each push
# to main and commits it.
set -euo pipefail

app="${1:-app}"
app="${app%/}"
test -f "${app}/config.yaml" || { echo "${app} has no config.yaml: not the app folder" >&2; exit 1; }

cd "$(dirname "$0")/.."
base="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' voice_incubator/__init__.py)"
test -n "${base}" || { echo "voice_incubator/__init__.py has no __version__" >&2; exit 1; }
version="${base}.$(git rev-list --count HEAD)"
sed -i "s/^version: .*/version: ${version}/" "${app}/config.yaml"
echo "${version} -> ${app}/config.yaml"
