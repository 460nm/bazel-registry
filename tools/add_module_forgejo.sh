#!/bin/bash

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Not enough arguments"
  echo "[-m <MODULE.bazel>] [-n <module_name>] [-h <https://forgejo.instance.url>] [-t <tag>] <owner> <repo> <version>"
fi

module_file="MODULE.bazel"
forgejo_instance="https://git.stevenlr.com"
tag=""
module_name=""

while getopts "m:h:t:n:" flag; do
  case "$flag" in
    m) module_file=$OPTARG;;
    h) forgejo_instance=$OPTARG;;
    t) tag=$OPTARG;;
    n) module_name=$OPTARG;;
  esac
done

pos_args=("${@:$OPTIND}")
owner=${pos_args[0]}
repo=${pos_args[1]}
version=${pos_args[2]}

tag=${tag:-"v${version}"}
module_name=${module_name:-$repo}

archive_url="${forgejo_instance}/${owner}/${repo}/archive/${tag}.tar.gz"
$(dirname $0)/add_module_archive.sh -m $module_file -p $repo $archive_url $module_name $version

