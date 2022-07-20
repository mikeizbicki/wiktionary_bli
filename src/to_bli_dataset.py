from collections import defaultdict
import random
import os
import sys
import glob
import math

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

valid_pos_small = {
        'Adjective'     : 50,
        'Adverb'        : 25,
        'Noun'          : 125,
        'Verb'          : 50,
        }

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

langs = {
        'af': 'Afrikaans',
        'als': 'Alemannic German',
        'am': 'Amharic',
        'an': 'Aragonese',
        'ar': 'Arabic',
        'arz': 'Egyptian Arabic',
        'as': 'Assamese',
        'ast': 'Asturian',
        'az': 'Azerbaijani',
        'azb': 'Azerbaijani', # Southern Azerbaijani
        'ba': 'Bashkir',
        'bar': 'Bavarian',
        'bcl': 'Bikol Central', # syn:Centeral Bicolano
        'be': 'Belarusian',
        'bg': 'Bulgarian',
        'bh': 'Bihari',
        'bn': 'Bengali',
        'bo': 'Tibetan',
        'bpy': 'Bishnupriya Manipuri',
        'br': 'Breton',
        'bs': 'Bosnian',
        'bs': 'Serbo-Croatian', #'Bosnian',
        'ca': 'Catalan',
        'ce': 'Chechen',
        'ceb': 'Cebuano',
        'ckb': 'Central Kurdish', #syn: 'Kurdish (Sorani)',
        'co': 'Corsican',
        'cs': 'Czech',
        'cv': 'Chuvash',
        'cy': 'Welsh',
        'da': 'Danish',
        'de': 'German',
        'diq': 'Zazaki',
        'dv': 'Dhivehi',
        'el': 'Greek',
        'eml': 'Emilian',
        'en': 'English',
        'eo': 'Esperanto',
        'es': 'Spanish',
        'et': 'Estonian',
        'eu': 'Basque',
        'fa': 'Persian',
        'fi': 'Finnish',
        'fr': 'French',
        'frr': 'North Frisian',
        'fy': 'West Frisian',
        'ga': 'Irish',
        'gd': 'Scottish Gaelic',
        'gl': 'Galician',
        'gom': 'Konkani', #syn:'Goan Konkani',
        'gu': 'Gujarati',
        'gv': 'Manx',
        'he': 'Hebrew',
        'hi': 'Hindi',
        'hif': 'Fiji Hindi',
        'hr': 'Croatian',
        'hr': 'Serbo-Croatian', # Croatian
        'hsb': 'Upper Sorbian',
        'ht': 'Haitian Creole',
        'hu': 'Hungarian',
        'hy': 'Armenian',
        'ia': 'Interlingua',
        'id': 'Indonesian',
        'ilo': 'Ilocano',
        'io': 'Ido',
        'is': 'Icelandic',
        'it': 'Italian',
        'ja': 'Japanese',
        'jv': 'Javanese',
        'ka': 'Georgian',
        'kk': 'Kazakh',
        'km': 'Khmer',
        'kn': 'Kannada',
        'ko': 'Korean',
        'ku': 'Northern Kurdish', # syn: 'Kurdish (Kurmanji)',
        'ky': 'Kyrgyz', #'Kirghiz',
        'la': 'Latin',
        'lb': 'Luxembourgish',
        'li': 'Limburgish',
        'lmo': 'Lombard',
        'lt': 'Lithuanian',
        'lv': 'Latvian',
        'mai': 'Maithili',
        'mg': 'Malagasy',
        'mhr': 'Eastern Mari', # syn: Meadow Mari
        'min': 'Minangkabau',
        'mk': 'Macedonian',
        'ml': 'Malayalam',
        'mn': 'Mongolian',
        'mr': 'Marathi',
        'mrj': 'Western Mari', # syn: 'Hill Mari',
        'ms': 'Malay',
        'mt': 'Maltese',
        'mwl': 'Mirandese',
        'my': 'Burmese',
        'myv': 'Erzya',
        'mzn': 'Mazanderani', # a->e
        'nah': 'Classical Nahuatl', # Nahuatl
        'nap': 'Neapolitan',
        'nds': 'Low German', #'Low Saxon',
        'ne': 'Nepali',
        'new': 'Newar',
        'nl': 'Dutch',
        'nn': 'Norwegian Nynorsk',
        'no': 'Norwegian Bokmål',
        'nso': 'Northern Sotho',
        'oc': 'Occitan',
        'or': 'Oriya',
        'os': 'Ossetian',
        'pa': 'Punjabi', # 'Eastern Punjabi',
        'pam': 'Kapampangan',
        #'pfl': 'Palatinate German',
        'pl': 'Polish',
        'pms': 'Piedmontese',
        'pnb': 'Punjabi', #'Western Punjabi',
        'ps': 'Pashto',
        'pt': 'Portuguese',
        'qu': 'Quechua',
        'rm': 'Romansch',  # add c
        'ro': 'Romanian',
        'ru': 'Russian',
        'sa': 'Sanskrit',
        'sah': 'Yakut', #'Sakha',
        'sc': 'Sardinian',
        'scn': 'Sicilian',
        'sco': 'Scots',
        'sd': 'Sindhi',
        'sh': 'Serbo-Croatian',
        'si': 'Sinhalese',
        'sk': 'Slovak',
        'sl': 'Slovene',
        'so': 'Somali',
        'sq': 'Albanian',
        'sr': 'Serbo-Croatian', # 'Serbian',
        'su': 'Sundanese',
        'sv': 'Swedish',
        'sw': 'Swahili',
        'ta': 'Tamil',
        'te': 'Telugu',
        'tg': 'Tajik',
        'th': 'Thai',
        'tk': 'Turkmen',
        'tl': 'Tagalog',
        'tr': 'Turkish',
        'tt': 'Tatar',
        'ug': 'Uyghur',
        'uk': 'Ukrainian',
        'ur': 'Urdu',
        'uz': 'Uzbek',
        'vec': 'Venetian',
        'vi': 'Vietnamese',
        'vls': 'West Flemish',
        'vo': 'Volapük',
        'wa': 'Walloon',
        'war': 'Waray-Waray',
        'xmf': 'Mingrelian',
        'yi': 'Yiddish',
        'yo': 'Yoruba',
        'zea': 'Zealandic',
        'zh': 'Chinese',
        }
langs_157 = langs

langs_ancient = {
        'grc': 'Ancient Greek',
        'enm': 'Middle English',
        }


def load_rank_from_vec(path, maxn=None): #200000):
    '''
    '''
    words = []
    with open(path, encoding='utf-8', errors='ignore') as fin:
        for i,line in enumerate(fin):
            word = line.split()[0]
            words.append(word)
            if maxn and i>maxn:
                break
    return { word:i for i,word in enumerate(words) }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--langiso', nargs='+', default=None)
    parser.add_argument('--seed')
    parser.add_argument('--max_defns', type=int, default=3)
    parser.add_argument('--clobber', action='store_true')
    parser.add_argument('--print_langisos', action='store_true')
    parser.add_argument('--numpar', type=int, default=1)
    parser.add_argument('--parid', type=int, default=0)
    parser.add_argument('--nounfactor', type=int, default=10000)
    parser.add_argument('--rank_side', default='tgt', choices=['tgt', 'src', 'srctgt'])
    args = parser.parse_args()

    random.seed(args.seed)

    # print the ids and quit
    if args.print_langisos:
        for i, langiso in enumerate(langs):
            #if i % args.numpar == (args.parid-1):
            print(langiso)
        sys.exit(0)

    # make the output dir
    outdirname = args.output
    os.makedirs(outdirname, exist_ok=True)

    # load the English vectors only if needed
    if 'tgt' in args.rank_side:
        logging.debug('loading English word vectors')
        tgt_ranks = load_rank_from_vec('/home/mizbicki/proj/korean/models/crawl-300d-2M.vec')

    # compute the languages we'll be looping over
    if not args.langiso:
        langisos = langs.keys()
    else:
        langisos = args.langiso

    # loop over the languages
    for langiso in langisos:
        lang = langs[langiso]
        logging.debug(f'{langiso}:{lang}')

        # if files already exist, then skip
        # FIXME: broken?
        if False:
            existingfiles = glob.glob(f'{outdirname}/{langiso}-*')
            if len(list(existingfiles)) > 0:
                logging.debug(f'skipping language')
                continue

        # loading the ranks is slow;
        # only do it if needed
        if 'src' in args.rank_side:
            logging.debug(f'loading {langiso}:{lang} word vectors')
            src_ranks = load_rank_from_vec('/home/mizbicki/proj/korean/models/cc.'+langiso+'.300.vec')

        # this helper function will be used later as the key for sorting ops
        def get_rank(line):
            unranked = 20000000
            src_rank = 1
            tgt_rank = 1
            if 'src' in args.rank_side:
                word = line.split(':')[0]
                src_rank += src_ranks.get(word, unranked)
            if 'tgt' in args.rank_side:
                words = line.split(':')[1].split(',')[:args.max_defns]
                ranks = [ tgt_ranks.get(word, unranked) for word in words ]
                tgt_rank += sum(ranks) / (len(ranks) + 1e-6)
            #print(line.strip(), words, "src_rank, tgt_rank=",src_rank, tgt_rank)
            #return math.sqrt(src_rank*src_rank + tgt_rank*tgt_rank)
            return max([src_rank, tgt_rank])

        # load the words
        indirname = os.path.join(args.input, lang)
        words = defaultdict(lambda: [])
        for filename in os.listdir(indirname):
            if filename.startswith('translations.'):
                pos = filename[13:]
                path = os.path.join(indirname, filename)
                try:
                    with open(path) as fin:
                        lines = fin.readlines()
                        lines.sort(key=get_rank)
                except FileNotFoundError:
                    print(f'FileNotFoundError: {path}')
                words[pos] = lines

        # compute the test splits
        train = defaultdict(lambda: [])
        trainsmall = defaultdict(lambda: [])
        test = defaultdict(lambda: [])
        testsmall = defaultdict(lambda: [])

        for pos in valid_pos:
            factor = args.nounfactor // valid_pos['Noun']
            maxpos = min(factor*valid_pos[pos], len(words[pos]))
            numsamples = max(0, min(maxpos, valid_pos.get(pos,0))-valid_pos_small.get(pos,0))
            test_indexes = set(random.sample(range(testsmall.get(pos,0),maxpos), numsamples))
            for i, line in enumerate(words[pos]):
                if i < valid_pos_small.get(pos, 0):
                    testsmall[pos].append(line)
                    test[pos].append(line)
                elif i in test_indexes:
                    trainsmall[pos].append(line)
                    test[pos].append(line)
                else:
                    train[pos].append(line)
            def write_lines(path, lines):
                with open(path, 'w') as fout:
                    deduplines = set()
                    for line in lines:
                        try:
                            src, tgts = line.split(':')
                        except ValueError:
                            continue
                        src = src.strip().lower()
                        dedupline = src + ':' + tgts
                        if dedupline in deduplines:
                            continue
                        deduplines.add(dedupline)
                        defns = tgts.split(',')
                        if args.max_defns:
                            defns = defns[:args.max_defns]
                        for i,tgt in enumerate(defns):
                            tgt = tgt.strip().lower()
                            fout.write(f'{src}\t{tgt}\n')
            write_lines(os.path.join(outdirname, f'{langiso}-en.train.{pos}'), train[pos])
            write_lines(os.path.join(outdirname, f'{langiso}-en.trainsmall.{pos}'), trainsmall[pos])
            write_lines(os.path.join(outdirname, f'{langiso}-en.test.{pos}'), test[pos])
            write_lines(os.path.join(outdirname, f'{langiso}-en.testsmall.{pos}'), testsmall[pos])

        all_train = []
        all_trainsmall = []
        all_test = []
        all_testsmall = []
        all = []
        for pos in valid_pos:
            all_train.extend(train[pos])
            all_trainsmall.extend(trainsmall[pos])
            all_test.extend(test[pos])
            all_testsmall.extend(testsmall[pos])
            all.extend(train[pos]+test[pos])
        #def get_rank(line):
            #return ranks.get(line.split(':')[0], 99999999999999999999)
        all_train.sort(key=get_rank)
        all_trainsmall.sort(key=get_rank)
        all_test.sort(key=get_rank)
        all_testsmall.sort(key=get_rank)
        all.sort(key=get_rank)
        write_lines(os.path.join(outdirname, f'{langiso}-en.train'), all_train)
        write_lines(os.path.join(outdirname, f'{langiso}-en.trainsmall'), all_trainsmall)
        write_lines(os.path.join(outdirname, f'{langiso}-en.test'), all_test)
        write_lines(os.path.join(outdirname, f'{langiso}-en.testsmall'), all_testsmall)
        write_lines(os.path.join(outdirname, f'{langiso}-en.all'), all)
