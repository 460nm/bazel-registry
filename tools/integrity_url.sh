#!/bin/bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Not enough arguments"
  echo "Usage: <file_url>"
  exit 1
fi

file_url=$1
file="/tmp/$(openssl rand -base64 18 | tr -- '+/=' '_-')"

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

curl -sSL  $file_url -o $file --fail-with-body
file $file
$parent_path/integrity.sh $file
rm -f $file

