#!/bin/bash

VERSION=$1
shift # Jetzt sind die weiteren Parameter ab $1

# Default Werte
RELEASE=""
DISTRO=""
EXECUTOR=""

# Parameter parsen
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --release)
      RELEASE="$2"
      shift 2
      ;;
    --distro)
      DISTRO="$2"
      shift 2
      ;;
    --executor)
      EXECUTOR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option $1"
      shift
      ;;
  esac
done

echo "Building xbat daemon version $VERSION, release $RELEASE, distro $DISTRO, executor $EXECUTOR"
# Hier kannst du dann deine Build-Befehle reinpacken
