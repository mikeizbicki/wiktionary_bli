#!/bin/sh

bli=final
MUSEdir=../korean/MUSE/data/crosslingual/dictionaries

for f in $bli/*.train; do
    muse_basename=$(basename $f | cut -f1 -d'.').txt
    muse=$MUSEdir/$muse_basename
    if [ -e $muse ]; then
        wiktionary_test=$bli/$(basename $f | cut -f1 -d'.').test
        muse_tabs=$(cat $muse | sed 's/ /\t/g')
        #muse_aug=''
        #cat $wiktionary_test | wc -l
        #muse_aug=$(grep -v -x -f $wiktionary_test $muse)
        muse_aug=$(echo "$muse_tabs" | grep -v -x -f $wiktionary_test)
        echo "$muse_aug" > $f.MUSE
        echo $muse $(cat $muse | wc -l) $(echo "$muse_aug" | wc -l)
    fi
done
