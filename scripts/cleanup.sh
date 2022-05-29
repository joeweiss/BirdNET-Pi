#!/usr/bin/env bash
source /etc/birdnet/birdnet.conf
set -xe

[ -z $STORAGE_LIMIT ] || STORAGE_LIMIT=50M

remove_empties() {
  cd "${PROCESSED}" || exit 1
  empties=($(find ${PROCESSED} -size 57c))
  for i in "${empties[@]}";do
    rm -f "${i}"
    rm -f "${i/.csv/}"
  done
}

cleanup() {
  space=$(du -b $PROCESSED|awk '{print $1}')
  STORAGE_LIMIT=$(numfmt --from=iec $STORAGE_LIMIT)
  if [ $space -gt $STORAGE_LIMIT ];then
    until [ $space -le $STORAGE_LIMIT ];do
      find $PROCESSED -type f | sort -r | tail -n10 | xargs rm -fv
      space=$(du -b $PROCESSED|awk '{print $1}')
    done
  fi
}

remove_empties
cleanup
