#!/bin/bash
set -euo pipefail

UPSTREAM="${TUNASYNC_UPSTREAM_URL}"
WORKDIR="${TUNASYNC_WORKING_DIR}"

if [[ -z "${UPSTREAM}" ]]; then
    echo "Please set TUNASYNC_UPSTREAM_URL"
    exit 1
fi

BRANCHES=()

while getopts "b:" opt; do
    case "$opt" in
        b)
            BRANCHES+=("$OPTARG")
            ;;
        *)
            echo "Usage: $0 -b <branch> [-b <branch> ...]"
            exit 1
            ;;
    esac
done

if [[ ${#BRANCHES[@]} -eq 0 ]]; then
    echo "At least one branch must be specified with -b"
    exit 1
fi

function repo_init() {
    git init --bare "$WORKDIR"

    cd "$WORKDIR"

    git remote add origin "$UPSTREAM"

    git config gc.auto 0

    touch git-daemon-export-ok

    # fetch
    git config --unset-all remote.origin.fetch || true

    for branch in "${BRANCHES[@]}"; do
        git config --add remote.origin.fetch \
            "+refs/heads/${branch}:refs/heads/${branch}"
    done
}

function update_server_info() {
    echo "Updating dumb HTTP metadata..."

    git update-server-info

    # gen packed refs
    git pack-refs --all

    # repack improve clone speed
    echo "repacking git repo..."
    git repack -a -d -b

    # update info
    git update-server-info
}

function update_linux_git() {
    cd "$WORKDIR"

    echo "==== SYNC $UPSTREAM START ===="

    git remote set-url origin "$UPSTREAM"

    /usr/bin/timeout -s INT 3600 \
        git fetch origin --prune

    local ret=$?

    [[ $ret -ne 0 ]] && \
        echo "git update failed with rc=$ret"

    local head
    head=$(git remote show origin | awk '/HEAD branch:/ {print $NF}')

    for branch in "${BRANCHES[@]}"; do
        if [[ "$branch" == "$head" ]]; then
            echo "ref: refs/heads/$head" > HEAD
            break
        fi
    done

    # update http server info
    update_server_info

    sz=$(git count-objects -v | grep -Po '(?<=size-pack: )\d+')
    sz=$((sz * 1024))

    echo "Total size is $(numfmt --to=iec "$sz")"

    echo "==== SYNC $UPSTREAM DONE ===="

    return $ret
}

if [[ ! -f "$WORKDIR/HEAD" ]]; then
    echo "Initializing $UPSTREAM mirror"
    repo_init
fi

update_linux_git
