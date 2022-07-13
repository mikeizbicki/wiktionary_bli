import os

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


if __name__ == '__main__':
    import os
    output = 'tmp'
    stats = {}
    for lang in os.listdir(output):
        lang_path = os.path.join(output, lang)
        stats[lang] = {}
        for filename in os.listdir(lang_path):
            if filename.startswith('translation.'):
                pos = filename[12:]
                path = os.path.join(lang_path, filename)
                if pos in valid_pos:
                    with open(path) as fin:
                        stats[lang][pos] = len(fin.readlines())

    totals = [ (lang, sum(stats[lang].values())) for lang in stats.keys() ]
    totals.sort(key=lambda x: x[1], reverse=True)

    print(' '*38, end=' ')
    for pos in valid_pos:
        print(f'{pos[:6]:6} ', end='')
    print()
    for i, (lang,total) in enumerate(totals):
        print(f'{i:4} {lang:20} - {total:10}', end='')
        for pos in valid_pos:
            #print(f' {stats[lang].get(pos,0)/total:0.4f}', end='')
            print(f' {stats[lang].get(pos,0):6}', end='')
        print()
        if i>100:
            break

