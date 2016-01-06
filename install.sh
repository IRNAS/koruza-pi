#!/bin/bash -e

if [ ${EUID} -ne 0 ]; then
  echo "ERROR: This installation script must be run as root."
  exit 1
fi

./make-package.sh
tar -xf koruza-package.tar.bz2 -C /
/koruza/install
