#!/bin/sh

#langs='ar de es en fr he it ko ja ru vi zh ta th tl ms id hi fa bn qu sw cy sq ceb gl el pam gv gu qu sw cy sq ceb gl el ilo pam gv gu lmo ml yo yi ug tk tr'
langs=$(python3 src/to_bli_dataset.py --print_langisos)
for lang in $langs; do
    echo $lang && 
    sem --id="$0" --jobs=8 "
        python3 src/to_bli_dataset.py --input '$1' --output '$1.bli' --langiso=$lang --max_defns=3 --rank_side=srctgt
        "
done
sem --id="$0" --wait
