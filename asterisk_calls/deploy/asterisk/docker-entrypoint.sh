#!/bin/bash
set -e

# dockerize templates
for i in `find /etc -name '*.tmpl'`; do
  dockerize -template "$i":"${i%%.tmpl}"
done

if [ "$1" = "" ]; then
  # This works if CMD is empty or not specified in Dockerfile
  exec /sbin/tini /usr/sbin/asterisk -Tfnvvv
else
  exec "$@"
fi
