#!/usr/bin/env bash
# Unpack the archived docs of every release line older than the latest, for a Pages build.
#
# When a line's successor ships, Release Assets attaches the old line's docs to its last release as
# <repo>-docs-<line>.tar.gz. This finds each line's last stable release, unpacks the archive it
# carries into <dest>/<line>/, and prints the lines it unpacked as the JSON list the site reads
# from docs_versions in SITE_METADATA_FILE. A line without an archive is left out, and so is the
# latest tag's own line.
#
# Needs gh with GH_TOKEN and GITHUB_REPOSITORY (owner/name) set, as in a workflow.
#
# Usage: bash scripts/download-docs-archives.sh <dest> <latest stable tag>
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <dest> <latest stable tag>" >&2
  exit 2
fi

dest="$1"
current_line="$(sed -E 's/^(v[0-9]+\.[0-9]+)\..*/\1/' <<<"$2")"
asset_prefix="${GITHUB_REPOSITORY#*/}-docs-"
tab="$(printf '\t')"

# Each line's newest stable release, as line, tag and asset names. It's read into a variable
# first so a failed API call stops the script rather than publishing without the archives.
releases="$(
  gh api --paginate "repos/${GITHUB_REPOSITORY}/releases?per_page=100" \
    --jq '.[] | select(.draft == false and .prerelease == false) | [.tag_name, ([.assets[].name] | join(" "))] | @tsv' \
    | sort -t "${tab}" -k1,1 -rV \
    | awk -F '\t' '{ line = $1; sub(/\.[0-9]+$/, "", line); if (!(line in seen)) { seen[line] = 1; print line "\t" $1 "\t" $2 } }'
)"

mkdir -p "${dest}"
versions='[]'
while IFS="${tab}" read -r line tag assets; do
  asset="${asset_prefix}${line}.tar.gz"
  if [ -z "${line}" ] || [ "${line}" = "${current_line}" ] || [[ " ${assets} " != *" ${asset} "* ]]; then
    continue
  fi
  mkdir -p "${dest}/${line}"
  gh release download "${tag}" --repo "${GITHUB_REPOSITORY}" --pattern "${asset}" --output - \
    | tar -xz --no-same-owner -C "${dest}/${line}"
  versions="$(jq -c --arg version "${line}" --arg release "${tag}" '. + [{version: $version, release: $release}]' <<<"${versions}")"
done <<<"${releases}"

printf '%s\n' "${versions}"
