#!/bin/bash

set -eo pipefail

if [ ! -z "$GPG_IMPORT_PUBLIC_KEYS" ]; then
  echo "Importing keys from environment variable"
  echo "$GPG_IMPORT_PUBLIC_KEYS" | gpg --import
fi

if [ ! -z "$GPG_IMPORT_PUBLIC_KEYS_FROM_URL" ]; then
  echo "Importing keys from ${GPG_IMPORT_PUBLIC_KEYS_FROM_URL}"
  curl -s "$GPG_IMPORT_PUBLIC_KEYS_FROM_URL" | gpg --import
fi

if [ ! -z "$GPG_RECIPIENTS_FROM_URL" ]; then
  echo "Configuring recipients from ${GPG_RECIPIENTS_FROM_URL}"
  BAG_GPG_RECIPIENTS=$(curl -s "$GPG_RECIPIENTS_FROM_URL")
  export BAG_GPG_RECIPIENTS
fi

exec "$@"
