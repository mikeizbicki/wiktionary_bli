import os
from collections import Counter

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

import sys
sys.path.append('src')
from to_bli_dataset import langs_157
langs_157_to_iso = { iso:lang for lang,iso in langs_157.items() }


if __name__ == '__main__':
    import os
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--conj", action='store_true')
    parser.add_argument('--max', default=10, type=int)
    parser.add_argument('--outdir', default='../korean/paper/fig')
    args = parser.parse_args()

    stats = {}
    for lang in os.listdir(args.output):
        lang_path = os.path.join(args.output, lang)
        stats[lang] = Counter()
        for filename in os.listdir(lang_path):
            if filename.startswith('translations.') or (args.conj and filename.startswith('conjugations.')):
                pos = filename.split('.')[1]
                path = os.path.join(lang_path, filename)
                if pos in valid_pos:
                    with open(path) as fin:
                        stats[lang][pos] += len(fin.readlines())

    totals = [ (lang, sum(stats[lang].values())) for lang in stats.keys() ]
    totals.sort(key=lambda x: x[1], reverse=True)

    testsmall_score = {}
    testfull_score = {}
    totalsmall = Counter()
    totalfull = Counter()
    for lang in stats:
        smallsum = sum([ min(stats[lang][k], valid_pos_small[k]) for k in valid_pos_small])
        fullsum = sum([ min(stats[lang][k], valid_pos[k]) for k in valid_pos ])
        testsmall_score[lang] = 100*smallsum // 250
        testfull_score[lang] = 100*fullsum // 1500
        for score in [100, 90, 80, 70, 60, 50]:
        #for score in range(0,101):
            if testsmall_score[lang] >= score:
                totalsmall[score]+=1
            if testfull_score[lang] >= score:
                totalfull[score]+=1

    
    def is_ancient(lang):
        if lang in ['Pali', 'Ottoman Turkish', 'Tocharian B', 'Coptic', 'Yola']:
            return True
        # Ingrian (almost extinct), Yola (extinct as of 1998)
        return 'Old' in lang or 'Middle' in lang or 'Classical' in lang or 'Early' in lang or 'Ancient' in lang or 'Proto' in lang
            
    print(' '*38, end=' ')
    for pos in valid_pos:
        print(f'{pos[:6]:6} ', end='')
    print()
    j = 0
    for i, (lang,total) in enumerate(totals):
        if lang not in langs_157_to_iso and not is_ancient(lang):
            j += 1
            print(f'{j:4} {lang.replace(" ", "_"):22} {total:10}', end='')
            for pos in valid_pos:
                #print(f' {stats[lang].get(pos,0)/total:0.4f}', end='')
                print(f' {stats[lang].get(pos,0):6}', end='')
            print(f' {(testsmall_score[lang]):3}', end='')
            print(f' {(testfull_score[lang]):3}', end='')
            print()
            if j>=args.max:
                break


    table_size = 20
    with open(args.outdir + '/of_interest.tex', 'w') as fout:
        fout.write(r'''
        \begin{tabular}{rlr}
        \toprule
        Rank & Language & Total words \\
        \midrule
        ''')
        j = 0
        for i, (lang,total) in enumerate(totals):
            footnote = ''
            if lang == 'Ingrian':
                #footnote = r"\tablefootnote{The Ingrian language is classsified as ``severely endangered'' as it has only about 130 living native speakers.  See: \url{https://www.endangeredlanguages.com/lang/1457}.}"
                footnote=r'$^\ddag$'
            if not is_ancient(lang) and lang not in langs_157_to_iso:
                j += 1
                fout.write(f'{j:4} & {lang}{footnote} $\!\!\!\!\!$ & ' + r'\numprint{' + f'{total:10}' + '}\\\\\n')
            if j>=table_size:
                break
        fout.write(r'''
        \bottomrule
        \end{tabular}''')

    with open(args.outdir + '/ancient.tex', 'w', encoding='utf-8') as fout:
        fout.write(r'''
        \begin{tabular}{rlr}
        \toprule
        Rank & Language & Total words \\
        \midrule
        ''')
        j = 0
        for i, (lang,total) in enumerate(totals):
            footnote=r''
            if lang=='Yola':
                footnote=r'$^\dag$'
                #footnote=r'\tablefootnote{The last speaker of Yola, Jack Devereux, died in 1998.  See \\url{https://www.independent.ie/regionals/wexfordpeople/out-about/fascinating-book-on-yola-dialect-of-forth-and-bargy-39143296.html}.}'
            if is_ancient(lang):
                j += 1
                fout.write(f'{j:4} & {lang}{footnote}$\!\!\!\!\!$ & ' + r'\numprint{' + f'{total:10}' + '}\\\\\n')
            if j>=table_size:
                break
        fout.write(r'''
        \bottomrule
        \end{tabular}''')

    with open(args.outdir + '/pos_summary.tex', 'w') as fout:
        fout.write(r'''
        \begin{tabular}{rlrrrrrrrrrrr}
        \toprule
        &&\multicolumn{10}{c}{Parts of Speech} \\
                \cmidrule{4-13}
        %Rank & Language & Total words & Adjective & Adverb & Conjunction & Determiner & Interjection & Noun & Number & Pronoun & Proper Noun & Verb \\
        Rank & Language & Total~~ & Adj & Adv & Conj & Det & Interj & Noun & Num & Pron & PN & Verb \\
        \midrule
        ''')
        def output_range(enumtotals):
            for i, (lang,total) in enumtotals:
                if lang == 'German Low German':
                    lang_disp = 'Low German'
                elif lang == 'Central Sierra Miwok':
                    lang_disp = 'Sierra Miwok'
                else:
                    lang_disp = lang
                fout.write(f'{i+1:4} & {lang_disp:22}$\!\!\!\!\!$ & ' + r'\numprint{' + f'{total:10}' + '}')
                for pos in valid_pos:
                    fout.write(r' & \numprint{' + f'{stats[lang].get(pos,0):6}' + r'}')
                fout.write('\\\\\n')
        enumtotals = list(enumerate(totals[1:]))
        output_range(enumtotals[:20])
        fout.write(r'\vdots & \\')
        #output_range(enumtotals[50:60])
        #fout.write(r'\vdots & \\')
        output_range(enumtotals[100:110])
        fout.write(r'\vdots & \\')
        output_range(enumtotals[200:210])
        fout.write(r'\vdots & \\')
        output_range(enumtotals[500:510])
        fout.write(r'\vdots & \\')
        fout.write(r'''
        \bottomrule
        \end{tabular}
        ''')

    with open(args.outdir + '/test_sizes.tex', 'w') as fout:
        fout.write(r'''
        \begin{tabular}{rrr}
        \toprule
        Percent & Small & Full \\
        \midrule
        ''')
        for score in sorted(totalsmall, reverse=True): 
            fout.write(f'{score:4} & {totalsmall[score]:6} & {totalfull[score]:6} \\\\\n')
        fout.write(r'''
        \bottomrule
        \end{tabular}
        ''')

