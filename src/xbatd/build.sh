#!/bin/bash

POSITIONAL_ARGS=()

EXECUTOR="podman"
DISTRO="el9"
RELEASE="0"

while [[ $# -gt 0 ]]; do
  case $1 in
    --executor)
      EXECUTOR="$2"
      shift
      shift
      ;;
    --distro)
      DISTRO="$2"
      shift
      shift
      ;;
    --release)
      RELEASE="$2"
      shift
      shift
      ;;
    --help)
      HELP=true
      shift
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

if [[ -z $1 || "$HELP" = true ]] ; then
    echo "$0 <version> [--distro (el8|el9)] [--release <release>] [--executor (docker|podman)] [--help]"
    exit 1
fi

VERSION=$1

echo "Building Version $VERSION Release $RELEASE for $DISTRO"

$EXECUTOR build --build-arg "VERSION=$VERSION" --platform=linux/amd64 --build-arg "RELEASE=$RELEASE" -t "xbatd:${DISTRO}" -f "xbatd.${DISTRO}.dockerfile" .

if [ $? -ne 0 ]; then
    echo "Failed to build $EXECUTOR container"
    exit 1
fi
id=$($EXECUTOR run --rm -d "xbatd:${DISTRO}" sleep infinity)
$EXECUTOR cp $id:/xbatd-${VERSION}-${RELEASE}.${DISTRO}.x86_64.rpm .
$EXECUTOR stop $id

echo "Copied xbatd-${VERSION}-${RELEASE}.${DISTRO}.x86_64.rpm to current directory."