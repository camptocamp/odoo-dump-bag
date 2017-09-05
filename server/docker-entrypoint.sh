#!/bin/bash

set -eo pipefail

echo "$GPG_IMPORT_PUBLIC_KEYS" | gpg --import

exec "$@"
