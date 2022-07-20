import glob
from collections import defaultdict, Counter
import logging
import os
import json


def reverse_translate(target, intermediate_dir='intermediate'):
    '''
    Find all non-English translations of a given English target word.
    '''
    ret = defaultdict(lambda: [])
    for path in glob.glob(os.path.join(intermediate_dir, '*/translations.*')):
        lang = os.path.basename(os.path.dirname(path))
        logging.debug(f'{path}')
        with open(path) as fin:
            for i,line in enumerate(fin):
                try:
                    word, defns_str = line.split(':')
                    defns = defns_str.split(',')
                    if target in defns:
                        ret[lang].append(word)
                except ValueError:
                    logging.warning(f'error in line {i} in {path} : {line}')
    return dict(ret)


if __name__ == '__main__':
    import os
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--intermediate_dir', default='output.en')
    parser.add_argument('word')
    args = parser.parse_args()

    ret = reverse_translate(args.word, args.intermediate_dir)
    print(json.dumps(ret, sort_keys=True, indent=4))
