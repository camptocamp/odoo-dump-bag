#!/bin/bash

set -eo pipefail

if [ ! -z "$GPG_IMPORT_PUBLIC_KEYS" ]; then
  echo "$GPG_IMPORT_PUBLIC_KEYS" | gpg --import
fi

exec "$@"
