#!/bin/python3

from collections import defaultdict, Counter
import mwparserfromhell

import logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("conjugations")
    parser.add_argument("translations")
    #parser.add_argument("outfile")
    args = parser.parse_args()

    logging.info('load conjugations')
    failed_conjugations = []
    conjugations = defaultdict(lambda: set())
    with open(args.conjugations) as fin:
        for i, line in enumerate(fin.readlines()):
            conj, template = line.split(':', 1)
            wikicode = mwparserfromhell.parse(template)
            for node in wikicode.nodes:
                if type(node) is mwparserfromhell.nodes.template.Template and node.name not in ['es-compound of']:
                    if node.name in ['es-verb form of']:
                        lemma = node.get(1, None)
                    else:
                        lemma = node.get(2, None)
                    if lemma:
                        conjugations[str(lemma)].add(str(conj))
                    else:
                        failed_conjugations.append((conj, node))

            if i%10000 == 0:
                logging.info(f'  i={i}, conj={conj}')

            if i>10000:
                break

    logging.info(f"len(failed_conjugations)={len(failed_conjugations)}")

    logging.info(f'generating conjugated file')
    with open(args.translations) as fin:
        with open(args.translations+'.conjugated', 'w') as fout:
            for line in fin:
                fout.write(line)
                try:
                    lemma, trans = line.split('\t')
                except ValueError:
                    print("line=",line)
                    raise
                for conj in conjugations[lemma]:
                    fout.write(f'{conj}\t{trans}')
