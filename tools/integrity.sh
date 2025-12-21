#!/bin/bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Not enough arguments"
  echo "Usage: <file>"
  exit 1
fi

file=$1
integrity="sha256-$(openssl dgst -sha256 -binary $file| openssl base64 -A)"

echo $integrity
