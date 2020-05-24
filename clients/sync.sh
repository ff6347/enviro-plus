#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

UP=false
DOWN=false

print_help() {
  printf "\n\nUsage\n\n"
  printf "Usage: %s -u\n" "${0}"
  printf "Usage: %s -d\n" "${0}"
  printf "Upload overrules download\n"
  printf "flag -u upload files %s\n" $UP
  printf "flag -d download files %s\n\n\n" $DOWN

}
while getopts 'ud' flag; do
  case "${flag}" in
  u) UP=true ;;
  d) DOWN=true ;;
  *)
    print_help
    exit 1
    ;;
  esac
done

if [[ $UP == true ]]; then
  echo "⬆ UP"
  rsync -auv --inplace --progress /Users/icke/Documents/enviro-plus/clients/* enviro:/home/pi/enviroplus-python/collector/
  exit 0
fi

if [[ $DOWN == true ]]; then
  echo "⬇ DOWN"
  rsync -auv --inplace --progress enviro:/home/pi/enviro-plus-collector/python/collector/ /Users/icke/Documents/environ-plus/clients
  exit 0
fi
