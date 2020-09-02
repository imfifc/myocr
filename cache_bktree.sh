#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

BKROOT="${DIR}/ocr_structuring/core/utils/bk_tree"
BKDATA="${BKROOT}/data"
BKCACHE="${BKROOT}/.tree"

declare -a sources_md5
declare -a cached_md5

for filepath in "${BKDATA}"/*.txt; do
    sources_md5+=("$(md5sum -b "${filepath}" | awk '{print $1}')")
done

mkdir -p "${BKCACHE}"
for md5 in "${sources_md5[@]}"; do
    curl -sSL --fail \
        -o "${BKCACHE}/${md5}.json" \
        "https://nexus-h.tianrang-inc.com/repository/assets/tianshi/cache/ocr-structuring/bktree/${md5}.json"
    
    ret=$?
    if [[ $ret == 0 ]]; then
        cached_md5+=("${md5}")
        echo "Cache HIT: ${md5}.json"
    elif [[ $ret == 22 ]]; then
        echo "Cache MISS: ${md5}.json"
        rm -rf "${BKCACHE}/${md5}.json"
    fi
done

sleep 3
exec_time="$(date '+%s')"
sleep 3

PYTHONPATH="${DIR}" python scripts/cache_all_bk_trees.py

while IFS= read -r -d '' filepath
do
    echo "Uploading $filepath"
    curl -sSL --fail --user admin:admin123 \
        --upload-file "${filepath}" \
        "https://nexus-h.tianrang-inc.com/repository/assets/tianshi/cache/ocr-structuring/bktree/$(basename "${filepath}")" ||
        {
            echo "Cannot upload asset: ${filepath}"
        }
done < <(find "${BKCACHE}" -type f -name '*.json' -newermt "@${exec_time}" -print0)
