import random
import os

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

valid_pos = {
        'Adjective'     : 350,
        'Adverb'        : 150,
        'Conjunction'   : 25,
        'Determiner'    : 25,
        'Interjection'  : 25,
        'Noun'          : 500,
        'Number'        : 50,
        'Pronoun'       : 25,
        'Proper noun'   : 50,
        'Verb'          : 300,
        }


def load_rank_from_vec(path):
    '''
    '''
    words = []
    with open(path) as fin:
        for line in fin:
            word = line.split()[0]
            words.append(word)

    return { word:i for i,word in enumerate(words) }


def reorder_file(ranks, path):
    with open(path) as fin:
        lines = fin.readlines()
    def get_rank(line):
        return ranks.get(line.split(':')[0], 99999999999999999999)
    lines.sort(key=get_rank)
    with open(path+'.sorted', 'w') as fout:
        for line in lines:
            fout.write(line)


if __name__ == '__main__':
    random.seed(0)
    langiso, lang = 'ko', 'Korean'
    langiso, lang = 'fr', 'French'
    langiso, lang = 'zh', 'Chinese'
    #langiso, lang = 'de', 'German'
    langiso, lang = 'ja', 'Japanese'
    langiso, lang = 'th', 'Thai'
    langiso, lang = 'es', 'Spanish'
    indirname = os.path.join('output.en.old', lang)
    outdirname = 'final'

    logging.info('loading ranks')
    ranks = load_rank_from_vec('/home/mizbicki/proj/korean/models/wiki.'+langiso+'.vec')

    words = {}
    for filename in os.listdir(indirname):
        if '.' not in filename:
            path = os.path.join(indirname, filename)
            with open(path) as fin:
                lines = fin.readlines()
                def get_rank(line):
                    return ranks.get(line.split(':')[0], 99999999999999999999)
                lines.sort(key=get_rank)
            words[filename] = lines

    train = {}
    test = {}
    for pos in valid_pos:
        if pos not in words:
            words[pos] = []
        factor = 10000 // valid_pos['Noun']
        maxpos = min(factor*valid_pos[pos], len(words[pos]))
        numsamples = min(maxpos, valid_pos[pos])
        test_indexes = set(random.sample(range(0,maxpos), numsamples))
        train[pos] = []
        test[pos] = []
        for i, line in enumerate(words[pos]):
            if i in test_indexes:
                test[pos].append(line)
            else:
                train[pos].append(line)
        def write_lines(path, lines):
            with open(path, 'w') as fout:
                for line in lines:
                    src, tgts = line.split(':')
                    src = src.strip().lower()
                    for tgt in tgts.split(','):
                        tgt = tgt.strip().lower()
                        fout.write(f'{src}\t{tgt}\n')
        write_lines(os.path.join(outdirname, f'{langiso}-en.train.{pos}'), train[pos])
        write_lines(os.path.join(outdirname, f'{langiso}-en.test.{pos}'), test[pos])

    all_train = []
    all_test = []
    for pos in valid_pos:
        all_train.extend(train[pos])
        all_test.extend(test[pos])
    def get_rank(line):
        return ranks.get(line.split(':')[0], 99999999999999999999)
    all_train.sort(key=get_rank)
    all_test.sort(key=get_rank)
    write_lines(os.path.join(outdirname, f'{langiso}-en.train.all'), all_train)
    write_lines(os.path.join(outdirname, f'{langiso}-en.test.all'), all_test)
