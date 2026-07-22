#!/bin/sh
set -eu

repo_root=$(CDPATH= cd "$(dirname "$0")" && pwd -P)

if ! command -v git >/dev/null 2>&1; then
    printf '%s\n' '[FAIL] Checking prerequisites: Git is required.' >&2
    printf '%s\n' '    Next: Install Git from https://git-scm.com/downloads, then rerun the installer after Git is available.' >&2
    exit 1
fi

python_command=
for candidate in python3 python
do
    if command -v "$candidate" >/dev/null 2>&1 &&
        "$candidate" -c 'import sys;raise SystemExit(0 if sys.version_info >= (3, 14) else 1)' >/dev/null 2>&1
    then
        python_command=$candidate
        break
    fi
done

if [ -z "$python_command" ]; then
    printf '%s\n' '[FAIL] Checking prerequisites: Python 3.14 or newer is required.' >&2
    printf '%s\n' '    Next: Install Python from https://www.python.org/downloads/, then rerun the installer after Python is available.' >&2
    exit 1
fi

if [ ! -t 0 ]; then
    BA_TOOLS_NONINTERACTIVE=1
    export BA_TOOLS_NONINTERACTIVE
fi

exec "$python_command" -X utf8 "$repo_root/installer/bootstrap.py" "$@"
