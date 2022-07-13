import re
import json
import os
import logging
from collections import defaultdict, Counter

from wiki_dump_reader import Cleaner, iterate
from lark import Lark, Transformer


def extract_header(line):
    '''
    >>> extract_header('==German==')
    (2, 'German')
    >>> extract_header('====Derived terms====')
    (4, 'Derived terms')
    >>> extract_header('body text')
    (0, 'body text')
    >>> extract_header('')
    (0, '')
    '''
    level = 0
    if len(line) == 0:
        return (0, '')
    while True:
        if line[level] == '=' and line[-1-level] == '=':
            level += 1
        else:
            break
        if level > len(line)-level:
            return (len(line)/2, '')
            #raise ValueError('No text in the header')
    return (level, line[level:len(line)-level])


def group_squiggles(text):
    r'''
    >>> group_squiggles("{{test}}\n{{test\ntest}}")
    '{{test}}\n{{test test}}'
    >>> group_squiggles("{{test}} {{a\nb c d\ne}}")
    '{{test}} {{a b c d e}}'
    '''
    ret = []
    squiggle_level = 0
    for line in text.split('\n'):
        squiggle_level += line.count('{{') - line.count('}}')
        ret.append(line)
        if squiggle_level == 0:
            ret.append('\n')
        else:
            ret.append(' ')
    return ''.join(ret[:-1])


def clean_brackets(text):
    '''
    >>> clean_brackets('test')
    'test'
    >>> clean_brackets('[[test]]')
    'test'
    >>> clean_brackets('this is a [[test]] of the [[function]]')
    'this is a test of the function'
    >>> clean_brackets('this is a [[#English|test]] more text')
    'this is a test more text'
    '''
    ret = []
    for p1 in text.split('[['):
        for p2 in p1.split(']]'):
            ret.append(p2.split('|')[-1])
    return ''.join(ret)


def parse_line(text):
    '''
    A template is wiktionary code inside the double curly braces {{ }}.
    Most templates do not include text that is part of a definition, and so we simply drop the template:

    >>> parse_line('{{lb|ms|Indonesia}}')['text']
    ''
    >>> parse_line('{{lb|ms|Indonesia}} [[free]]')['text']
    ' free'
    >>> parse_line('{{lb|ms|Indonesia}} [[free]]')['text']
    ' free'
    >>> parse_line('words {{lb|ms|Indonesia}} words')['text']
    'words  words'

    Some templates include information that is part of the actual text and this info should be inlined

    >>> parse_line('{{lb|pt|Christianity}} {{l|en|Holy Ghost}}; {{l|en|Holy Spirit}} {{gloss|one of the three figures of the Holy Trinity}}')['text']
    ' Holy Ghost; Holy Spirit '

    >>> parse_line('{{place|pt|municipality/state capital|s/Santa Catarina|c/Brazil|t=Florianópolis}}')['text']
    'Florianópolis'
    >>> parse_line('{{place|en|An <<overseas territory>> (technically an {{w|unincorporated territory}}) of the <<c/United States>>, located in the <<ocean/Pacific Ocean>>|official=Territory of Guam}}')['text']
    'An <<overseas territory>> (technically an unincorporated territory) of the <<c/United States>>, located in the <<ocean/Pacific Ocean>>'
    >>> parse_line('{{female equivalent of|es|hermano|gloss=sister}}')['text']
    'sister'
    >>> parse_line('{{ISO 639|2&3|ca|Catalan}}')['text']
    'Catalan'
    >>> parse_line('{{vern|African golden cat}} ({{taxlink|Caracal aurata|species|ver=210608}})')['text']
    'African golden cat (Caracal aurata)'

    # {{lb|en|historical}} The smallest unit of currency in South Asia, equivalent to {{frac|1|192}} of a [[rupee]] or {{frac|1|12}} of an [[anna]].
    'The smallest unit of currency in South Asia, equivalent to 1/192 of a rupee or 1/12 of an anna.

    Templates can be nested, and so the parser needs to be able to handle these cases:

    >>> parse_line('{{lb|de|with {{m|de|von}}}} [[free]] of {{gloss|not containing or unaffected by}}')['text']
    ' free of '

    >>> parse_line('[[blahblahblah|{{female equivalent of|es|hermano|gloss=sister}}]]')['text']
    'sister'


    # FIXME:

    > # {{inflection of|la|piō||2|s|pres|actv|subj}}
    'piō'

    #>>> parse_line('{{lb|en|Australian rules football|Gaelic football}} {{abbreviation of|en|free kick}}')
    #'free kick'



    =======
    Parsing synonyms
    =======

    >>> parse_line('{{syn|ru|же́нщина|t1=woman|ба́ба|;|t2=older woman|q2=informal}}')['syn']
    ['же́нщина', 'ба́ба']
    >>> parse_line('{{syn|en|wordbook|Thesaurus:dictionary}}')['syn']
    ['wordbook']
    >>> parse_line('{{syn|ru|совреме́нный<t:contemporary>|мо́дный<t:fashionable>|модерно́вый<tr:modɛrnóvyj><t:fashionable, contemporary><q:colloquial>}}')['syn']
    ['совреме́нный', 'мо́дный', 'модерно́вый']
    >>> parse_line('{{syn|ru|кавале́р|ухажёр|;|покло́нник<t:admirer, fan>|;|друг<t:boyfriend; friend>|;|па́рень<t:boyfriend; lad, boy>|;|возлю́бленный<t:sweetheart>|люби́мый<t:sweetheart>|;|жени́х<t:fiancé>|;|любо́вник<t:lover>|;|партнёр<t:partner>|;|сожи́тель<t:cohabitant>}}')['syn']
    ['кавале́р', 'ухажёр', 'покло́нник', 'друг', 'па́рень', 'возлю́бленный', 'люби́мый', 'жени́х', 'любо́вник', 'партнёр', 'сожи́тель']

    '''

    import mwparserfromhell
    wikicode = mwparserfromhell.parse(text)
    ret = defaultdict(lambda: [])
    #ret = {}
    #ret['unknown_templates'] = []
    #ret['conjugations'] = []
    #ret['synonyms'] = []
    
    def recurse(v):
        if v:
            r = parse_line(v)
            chunks.append(r['text'])
            ret['unknown_templates'].extend(r['unknown_templates'])

    chunks = []
    for node in wikicode.nodes:

        # the processed value for [[links]] is just the text that would be displayed in-browser
        if type(node) is mwparserfromhell.nodes.wikilink.Wikilink:
            if node.text:
                recurse(node.text)
                #chunks.append(parse_line(node.text))
            else:
                recurse(node.title)
                #chunks.append(parse_line(node.title))

        # {{templates}} require complex processing for each different template
        elif type(node) is mwparserfromhell.nodes.template.Template:
            nodename = str(node.name).strip()
            template_names[nodename] += 1
            if nodename in ['place']:
                recurse(node.get('t', node.get(2, None)).value)
            elif nodename in ['place']:
                recurse(node.get('t', node.get(2, None)).value)
            elif nodename in ['initialism of']:
                recurse(node.get('t', node.get(2, None)).value)
            elif nodename in ['w', 'unsupported']:
                recurse(node.get(2, node.get(1, None)))
            elif nodename in ['m', 'mention', 'l', 'link', 'l-lite', 'm-lite']:
                recurse(node.get('t', node.get(4, node.get(3, node.get(2, node.get(1, None))))))
            elif nodename in ['zh-l']:
                recurse(node.get('t', None))
            elif nodename in ['zh-classifier']:
                recurse(node.get(2, node.get('t', None)))

            elif nodename in ['ISO 639', 'ISO 3166']:
                recurse(node.get(3, None))

            elif nodename in ['vern']:
                recurse(node.get(1, None))
            elif nodename in ['taxlink']:
                recurse(node.get(3, node.get(1, None)))
            elif nodename in ['frac']:
                recurse(node.get(1, None))
                chunks.append('/')
                recurse(node.get(2, None))
            elif nodename in ['zh-original', 'zh-abbrev',]:
                recurse(node.get(2, None))

            elif nodename in ['abbreviation of', 'clipping of']:
                lemma = node.get(2, None)
                recurse(lemma)
                ret['conjugations'].append(str(node))
            elif nodename in [
                'inflection of',
                'alternative spelling of',
                'alternative form of',
                'alt form',
                'altform',
                'alt sp',
                'ca-verb form of',
                'fr-post-1990',
                'sv-noun-form-indef-pl',
                ] or nodename[-3:] == ' of' or nodename[-3:] == '-of' or nodename[-4:] == '-alt':
                ret['conjugations'].append(str(node))

            # just ignore these templates
            elif nodename in [ 
                # definition needed
                'rfdef',
                'rfclarify',
                'rfex',

                # used on individual letters
                'Latn-def', 'Latn-def-lite', 'Latn-def',

                # add non-definitional extra information
                'gl', 'gloss', 'gloss-lite',
                'lb', 'lbl', 'label', 'tlb', 'term-label',
                'ng', 'n-g', 'ngd', 'n-g-lite', 'non-gloss definition',
                'q', 'qf', 'qual', 'qualifier', 'q-lite', 'qualifier-lite',
                'c', 'C', 'topics',
                'given name', 'surname',
                'defdate',
                '+obj',
                'cln',
                'only used in', 'used in phrasal verbs',
                'term-label',
                'ja-def',
                'mul-kangxi radical-def',
                'zh-mw',
                'short for',

                # possibly these could be added?
                'bond credit rating',
                'taxon',

                # a type of anchor tag
                'anchor', 'senseid', 'rfd-sense', 'rfv-sense', 'sense', 'sense-lite',

                # typography
                ','
                ]:
                pass

            # synonyms; see https://en.wiktionary.org/wiki/Category:Semantic_relation_templates
            elif nodename in ['syn', 'synonyms', 'coordinate terms', 'ant', 'antonyms', 'holonyms', 'hypernyms', 'holonyms', 'holo', 'hyper', 'impf', 'imperfectives', 'meronyms', 'inline alt forms', 'perfectives', 'pf', 'troponyms']:
                for i in range(2,100):
                    v = node.get(i, None)
                    if v:
                        v = rm_parens(str(v), '<>')
                        if ':' not in v and ';' not in v:
                            ret[nodename[:3]].append(v)
                    #if t:
                        #ret['synonyms'].append(str(t.value))
                    t = node.get('t'+str(i), None)
                    if not v and not t:
                        break


            # couldn't match the template
            else:
                ret['unknown_templates'].append(str(node))
                unknown_template_names[nodename] += 1

            # FIXME:
            # catchall for glosses
            for param in node.params:
                if param.name == 'gloss':
                    recurse(param.value)
                    found_glosses[nodename] += 1

        # if it's not a template or a link, just return the raw text
        else:
            chunks.append(str(node))

    ret['text'] = ''.join(chunks)
    ret['translations'] = extract_definitions(ret['text'])
    return ret

template_names = Counter()
unknown_template_names = Counter()

found_glosses = Counter()


def rm_parens(text, brackets="()"):
    '''
    see: https://stackoverflow.com/questions/14596884/remove-text-between-and/14603508#14603508

    >>> rm_parens("[[dog]] ([[Canis familiaris]])")
    '[[dog]] '
    '''
    count = [0] * (len(brackets) // 2) # count open/close brackets
    saved_chars = []
    for character in text:
        for i, b in enumerate(brackets):
            if character == b: # found bracket
                kind, is_close = divmod(i, 2)
                count[kind] += (-1)**is_close # `+1`: open, `-1`: close
                if count[kind] < 0: # unbalanced bracket
                    count[kind] = 0  # keep it
                else:  # found bracket to remove
                    break
        else: # character is not a [balanced] bracket
            if not any(count): # outside brackets
                saved_chars.append(character)
    return ''.join(saved_chars)



def canonicalize(text):
    '''
    >>> canonicalize('A dog')
    'dog'
    >>> canonicalize('a dog')
    'dog'
    >>> canonicalize('the dog')
    'dog'
    >>> canonicalize('The dog')
    'dog'
    >>> canonicalize('A male dog')
    'male dog'
    >>> canonicalize('to abandon')
    'abandon'
    >>> canonicalize('to be familiar')
    'familiar'
    >>> canonicalize('to be allowed to')
    'allowed'
    '''
    words = text.split()
    stopwords = ['a', 'an', 'the', 'to', 'be']
    if len(words) > 0 and words[0].lower() in stopwords:
        return canonicalize(' '.join(words[1:]))
    if len(words) > 0 and words[-1].lower() in stopwords:
        return canonicalize(' '.join(words[:-1]))
    else:
        return text


def extract_definitions(text):
    '''
    >>> extract_definitions('perquisite, free gift')
    ['perquisite', 'free gift']
    >>> extract_definitions('out of favor or kindness, without recompense or compensation, gratuitously')
    ['out of favor or kindness', 'without recompense or compensation', 'gratuitously']
    >>> extract_definitions('free; for free, without charge')
    ['free', 'for free', 'without charge']

    >>> extract_definitions("free (''obtainable without payment'')")
    ['free']
    >>> extract_definitions('to you, for you')
    ['you', 'for you']
    '''
    ret = []
    text = rm_parens(text)
    for part in re.split(r'[,;]', text):
        part = clean_brackets(part)
        part = part.replace('.', '')
        part = part.replace(':', '')
        part = re.sub(r"''.*?''", "", part)
        part = canonicalize(part)
        part = part.strip()
        if part:
            ret.append(part)
    return ret


def rm_bad_definitions(defns):
    '''
    >>> rm_bad_definitions(['test'])
    ['test']
    >>> rm_bad_definitions(['test test'])
    []
    >>> rm_bad_definitions(['test', 'test test'])
    ['test']
    '''
    return [ defn for defn in defns if ' ' not in defn ]
    

def find_entry(word, dump='data/enwiktionary-20220701-pages-articles-multistream.xml'):
    '''
    This is a helper function for the `process_entry` doctests.
    '''
    for title, text in iterate(dump):
        if title == word:
            return text


def process_entry(title, text, rm_bad=False):
    r'''
    >>> __test_process_entry = lambda title: json.dumps(process_entry(title, find_entry(title))[1])

    >>> __test_process_entry('frei')
    '{"German": {"Adjective": {"free": 2, "unenslaved": 1, "unimprisoned": 1, "unrestricted": 1, "unrestrained": 1, "licentious": 1, "unblocked": 1, "free for passage": 1, "independent": 1, "unaffiliated": 1, "free of": 1, "liberal": 1, "free of charge": 1, "gratis": 1}}, "Pennsylvania German": {"Adjective": {"free": 1, "exempt": 1, "clear": 1}}, "Scots": {"Adjective": {"free": 1}}, "Sranan Tongo": {"Verb": {"fly": 1}, "Noun": {"wing": 1}}}'

    >>> __test_process_entry('gratis')
    '{"English": {"Adjective": {"Free": 1, "without charge": 1}, "Adverb": {"Free": 1, "without charge": 1}}, "Afrikaans": {"Adverb": {"free": 1, "without charge": 1}}, "Catalan": {"Adverb": {"free": 1, "for free": 1}}, "Danish": {"Adjective": {"gratis": 1, "free": 1}, "Adverb": {"gratis": 1, "free": 1}}, "Dutch": {"Adjective": {"free": 1, "without charge": 1}, "Adverb": {"free": 1, "without charge": 1}}, "French": {"Adverb": {"free": 1, "without charge": 1, "gratis": 1}, "Adjective": {"free": 1, "for free": 1, "without charge": 1}}, "Galician": {"Adjective": {"free": 1, "without charge": 1}, "Adverb": {"free": 1, "without charge": 1}}, "German": {"Adverb": {"free": 1, "without charge": 1}}, "Indonesian": {"Adjective": {"free": 1, "without charge": 1}}, "Italian": {"Adverb": {"gratis": 1, "free": 1}, "Adjective": {"free": 1}}, "Latin": {"Adverb": {"out of favor or kindness": 1, "without recompense or compensation": 1, "gratuitously": 1}}, "Malay": {"Adjective": {"free": 1, "without charge": 1}}, "Norwegian Bokm\\u00e5l": {"Adjective": {"free": 1}}, "Norwegian Nynorsk": {"Adjective": {"free": 1}}, "Polish": {"Noun": {"perquisite": 1, "free gift": 1}, "Adverb": {"gratis": 1, "free of charge": 1}}, "Romanian": {"Adverb": {"free of charge": 1, "for free": 1}, "Adjective": {"free of charge": 1, "for free": 1}}, "Spanish": {"Adjective": {"free": 1, "without charge": 1}, "Adverb": {"free": 1, "without charge": 1}}, "Swedish": {"Adverb": {"free": 1, "without charge": 1}, "Adjective": {"free": 1, "without charge": 1}}}'

    >>> __test_process_entry('pies')
    '{"Cornish": {"Noun": {"magpies": 1}}, "Dutch": {"Noun": {"pee": 1, "piss": 1}}, "Kashubian": {"Noun": {"dog": 1}}, "Polish": {"Noun": {"dog": 1, "male dog": 1, "male fox or badger": 1, "cop": 1, "policeman": 1}}}'

    >>> __test_process_entry('may')
    '{"Translingual": {"Symbol": {"Malay": 1}}, "English": {"Verb": {"strong": 1, "have power": 1, "able": 1, "can": 1, "able to go": 1, "have permission": 1, "allowed": 1, "gather may": 1, "or flowers in general": 1, "celebrate May Day": 1}, "Noun": {"hawthorn bush or its blossoms": 1, "maiden": 1}}, "Azerbaijani": {"Noun": {"May": 1}}, "Bikol Central": {"Verb": {"there is": 1, "there\'s": 1, "have": 1}}, "Crimean Tatar": {"Noun": {"butter": 1, "oil": 1}}, "Kalasha": {"Determiner": {"my": 1}, "Pronoun": {"me": 1}}, "Mapudungun": {"Adverb": {"yes": 1}}, "Northern Kurdish": {"Noun": {"intervention": 1}}, "Pacoh": {"Pronoun": {"you": 1}}, "Quechua": {"Adverb": {"where": 1, "like": 1, "how": 1, "very": 1}, "Pronoun": {"which": 1}, "Verb": {"fear": 1}}, "Tagalog": {"Particle": {"have": 1}}, "Tatar": {"Noun": {"May": 1}}, "Uzbek": {"Noun": {"May": 1}}, "Vietnamese": {"Verb": {"sew": 1}, "Adjective": {"lucky": 1}}, "Walloon": {"Noun": {"May": 1}}}'

    '''

    if ' ' in title and rm_bad:
        return title, {}, {}

    lines = group_squiggles(text).split('\n')
    #if title == 'gratis':
        #print("text=",text)

    current_language = None
    current_subheader = None
    parse_info = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: Counter())))
    #parse_info = defaultdict(lambda: defaultdict(lambda: { 
        #'conjugations': Counter(),
        #'translations': Counter(),
        #'unknown_templates': Counter(),
        #}))
    translations = defaultdict(lambda: defaultdict(lambda: Counter()))
    conjugations = defaultdict(lambda: defaultdict(lambda: []))
    synonums = defaultdict(lambda: [])
    otherinfo = defaultdict(lambda: defaultdict(lambda: []))

    page_hasword = False
    page_hashash = False

    for line in lines:
        (level, header) = extract_header(line)
        if level == 2:
            if current_language:
                if not lang_hasword and lang_hashash:
                    bad_langwords.append((title, current_language))
                else:
                    good_langwords.append((title, current_language))
            current_language = header.strip()
            lang_hasword = False
            lang_hashash = False
        if level == 3 or level == 4:
            current_subheader = header.strip()
            current_subheader = current_subheader.replace('/', '_')
            if current_subheader == 'Numeral':
                current_subheader = 'Number'

        #if len(line) >= 2 and line[0:2] == '# ':
        if line.startswith('#'):
            lang_hashash = True
            parse = parse_line(line[2:])
            #if parse['unknown_templates']:
                #for t in parse['unknown_templates']:
                    #if 'syn' in t:
                        #print("title, current_language=",title, current_language)
                        #print("text=",text)
                        #print("parse['unknown_templates']=",parse['unknown_templates'])
                        #raise ValueError
            translations = parse['translations']
            if rm_bad:
                translations = rm_bad_definitions(translations)
            for k,v in parse.items():
                if k != 'text':
                    if k != 'unknown_templates':
                        lang_hasword = True
                        page_hasword = True
                    parse_info[current_language][current_subheader][k].update(v)

        matches = re.findall(r'\{\{[^\{\}]*\}\}', line)
        if matches:
            otherinfo[current_language][current_subheader].extend(matches)

    if not page_hasword and page_hashash:
        bad_pages.append(title)
    else:
        good_pages.append(title)

    return [title, parse_info, otherinfo]
    #return [title, translations, otherinfo]
    #print(json.dumps(translations))
    #print(json.dumps(otherinfo, indent=4))

bad_pages = []
bad_langwords = []
good_pages = []
good_langwords = []


def write_output(dumpfile, outdir, rm_bad=True):
    for i, (title,text) in enumerate(iterate(dumpfile)):
        _, parseinfo, other = process_entry(title, text, rm_bad=rm_bad)
        for lang in parseinfo.keys():
            for pos in parseinfo[lang].keys():
                if pos and lang:
                    for parsekey,parseval in parseinfo[lang][pos].items():
                        if parseval:
                            try:
                                dirpath = os.path.join(outdir, lang)
                                os.makedirs(dirpath, exist_ok=True)
                                path = os.path.join(dirpath, parsekey+'.'+pos)
                                with open(path, 'at', encoding='utf-8') as fout:
                                    fout.write(title + ':' + ','.join(parseval.keys()) + '\n')
                            except FileNotFoundError as e:
                                logging.error(f'{e}')
                    #if parseinfo[lang][pos]['conjugations']:
                        #try:
                            #dirpath = os.path.join(outdir, lang)
                            #os.makedirs(dirpath, exist_ok=True)
                            #path = os.path.join(dirpath, 'conjugation.'+pos)
                            #with open(path, 'at', encoding='utf-8') as fout:
                                #fout.write(title + ':' + ','.join(parseinfo[lang][pos]['conjugations'].keys()) + '\n')
                        #except FileNotFoundError as e:
                            #logging.error(f'{e}')
        if i%1000 == 0:
            logging.info(f'i={i}, title={title}')

        #if i>10000:
            #break

    print('Found Templates:')
    for k,v in list(sorted(template_names.items(), reverse=True, key=lambda x: x[1]))[:20]:
        print(f'  {k:30} - {v:8}')

    print('Unkown Templates:')
    for k,v in list(sorted(unknown_template_names.items(), reverse=True, key=lambda x: x[1]))[:20]:
        print(f'  {k:30} - {v:8}')

    #print('Found Glosses:')
    #for k,v in list(sorted(found_glosses.items(), reverse=True, key=lambda x: x[1]))[:20]:
        #print(f'{k:30} - {v:8}')

    #print()
    #print("bad_pages=",bad_pages)

    #print()
    #print("bad_langwords=",bad_langwords)

    print("len(bad_pages)=",len(bad_pages))
    print("len(bad_langwords)=",len(bad_langwords))
    print("len(good_pages)=",len(good_pages))
    print("len(good_langwords)=",len(good_langwords))
    print("len(found_glosses)=",len(found_glosses))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    src_lang = 'en'
    #write_output(dumpfile='data/'+src_lang+'wiktionary-20220701-pages-articles-multistream.xml', outdir='output.'+src_lang)
    write_output(dumpfile='data/'+src_lang+'wiktionary-20220701-pages-articles-multistream.xml', outdir='tmp')
