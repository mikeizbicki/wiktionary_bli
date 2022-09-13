import glob
from collections import defaultdict, Counter
import logging
import os
import simplejson as json


def reverse_translate(target, pos='*', intermediate_dir='intermediate'):
    '''
    Find all non-English translations of a given English target word.
    '''
    ret = defaultdict(lambda: [])
    paths = sorted(glob.glob(os.path.join(intermediate_dir, '*/translations.' + pos)))
    if pos == 'Noun':
        paths = sorted(paths + glob.glob(os.path.join(intermediate_dir, '*/translations.Proper noun')))
    for path in paths:
        logging.debug(f'path={path}')
        lang = os.path.basename(os.path.dirname(path))
        with open(path) as fin:
            for i,line in enumerate(fin):
                line_parsed = json.loads(line)
                word, = line_parsed['srcs']
                tgts = line_parsed['tgts']
                if target in tgts:
                    ret[lang].append(word)
    return dict(ret)


if __name__ == '__main__':
    import os
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--intermediate_dir', default='output.en')
    parser.add_argument('--outdir', default=None)
    parser.add_argument('--pos', default='*')
    parser.add_argument('word')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d : %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    ret = reverse_translate(args.word, args.pos, args.intermediate_dir)
    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
        outpath = os.path.join(args.outdir, args.word)
        with open(outpath, 'wt', encoding='utf-8') as fout:
            fout.write(json.dumps(ret, sort_keys=True))
    print(json.dumps(ret, sort_keys=True, indent=4, ensure_ascii=False))
    print("len(ret)=",len(ret))
