#!/bin/bash

#
# A quick and dirty way to carve prefetch files from an unformatted disk image.
#
# Note that ${SEARCH_STR} is currently configured only to find pf files from
#   Windows 8.  Other pf files have different signatures.  Their format is as follows:
#
#   version-signature,file-signature,unknown 4 Bytes.
#
#   version signature:
#       Win xp       - '\x11\x00\x00\x00'
#       Win vista/7  - '\x17\x00\x00\x00'
#       Win 8        - '\x1A\x00\x00\x00'
#       Win 10       - 'MAM'
#
#   File signature: '\x53\x43\x43\x41'
#
#   Unknown 4 bytes: '\x11\x00\x00\x00'
#
#  Combine them all together and make a search str!
#

SEARCH_STR='\x1A\x00\x00\x00\x53\x43\x43\x41\x11\x00\x00\x00'

if [ -z "${1}" ]
then
    echo "Error.  Usage: $(basename ${0}) <image_file>"
    exit 2
fi

while read LINE
do
    #Grep the offset off of results list.
    OFFSET=$(echo ${LINE} | grep -Eo '[0-9]{1,}')

    # since we know the file size is +12 bytes into the file and an int (4 bytes long), we use the following:
    SIZE_HEX_LE=$(dd status=none ibs=1 skip=$((${OFFSET}+12)) count=4 if=${1} | xxd -p)

    #conver to big endian so it doesn't break everything.  Yes this is ugly, we're slicing the string apart.  Since it's a fixed length, we can get away with it.
    SIZE_HEX_BE=${SIZE_HEX_LE:4:2}${SIZE_HEX_LE:2:2}${SIZE_HEX_LE:0:2}

    # convert that to decimal since I'm too dumb to do it all in the line above...
    SIZE_DEC=$((16#${SIZE_HEX_BE})) 

    echo "[+] Carving file at ${OFFSET}"
    #time to carve!
    dd status=none ibs=1 skip=${OFFSET} count=${SIZE_DEC} if=${1} of=pf-offset_${OFFSET}.pf 

done < <(grep -aPo --byte-offset ${SEARCH_STR} ${1})
