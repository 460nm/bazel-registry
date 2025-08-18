#!/bin/bash

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Not enough arguments"
  echo "[-p <prefix/path>] [-m <MODULE.bazel>] <archive_url> <module_name> <module_version>"
  exit 1
fi

strip_prefix=""
module_file="MODULE.bazel"

while getopts "p:m:" flag; do
  case "$flag" in
      p) strip_prefix=$OPTARG;;
      m) module_file=$OPTARG;;
  esac
done

pos_args=("${@:$OPTIND}")
archive_url=${pos_args[0]}
module_name=${pos_args[1]}
module_version=${pos_args[2]}

strip_prefix=$(echo $strip_prefix | tr '\\' '/' | sed 's/^\/*\(.*[^/]\)\/*$/\1/g')
strip_components=$(echo $strip_prefix | awk -F/ '{ print NF }')

archive_file="/tmp/$(openssl rand -base64 18 | tr -- '+/=' '_-')"

curl -sS $archive_url -o $archive_file --fail-with-body

module_dir="modules/$module_name/$module_version"

if [[ -e $module_dir ]]; then
  echo "Module $module_name@$module_version already exists"
  exit 1
fi

integrity="sha256-$(openssl dgst -sha256 -binary $archive_file | openssl base64 -A)"

module_json=$(jq -n \
  --arg url "$archive_url" \
  --arg integrity "$integrity" \
  '$ARGS.named')

if [[ -n $strip_prefix ]]; then
  module_json=$(echo $module_json | jq --arg strip_prefix "$strip_prefix" '. += $ARGS.named')
  module_file="$strip_prefix/$module_file"
fi

mkdir -p $module_dir
echo $module_json | jq . > $module_dir/source.json
tar xf $archive_file --strip-components $strip_components -C $module_dir $module_file

rm -f $archive_file

