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


def apply_templates(text):
    '''
    A template is wiktionary code inside the double curly braces {{ }}.
    Most templates do not include text that is part of a definition, and so we simply drop the template:

    >>> apply_templates('{{lb|ms|Indonesia}}')
    ''
    >>> apply_templates('{{lb|ms|Indonesia}} [[free]]')
    ' free'
    >>> apply_templates('{{lb|ms|Indonesia}} [[free]]')
    ' free'
    >>> apply_templates('words {{lb|ms|Indonesia}} words')
    'words  words'

    Some templates, however, are commonly used in definitions to highlight alternative conjugations of words.
    These templates commonly have a parameter of `gloss=XXX` or `t=XXX` where the XXX is part of the definition.
    The following are examples from the Spanish definition of "hermana".

    >>> apply_templates('{{female equivalent of|es|hermano|gloss=sister}}')
    'sister'

    FIXME:
    There are too many other templates that use the t= argument.
    > apply_templates('words {{female equivalent of|es|hermano|t=sister}} more words')
    'words sister more words'

    FIXME:
    The explanation above is highly simplified.
    Technically, these named parameters should only be included for specific templates,
    and there may be other templates where these parameters should not be included.
    These parameters can also be specified positionally (pos 4),
    but the there are many other templates where pos 4 should not be included,
    so we're not representing that position.
    There may also be templates that use other parameter names/position numbers that should be included

    > # {{inflection of|la|piō||2|s|pres|actv|subj}}
    'piō'

    Templates can be nested, and so the parser needs to be able to handle these cases:

    >>> apply_templates('{{lb|de|with {{m|de|von}}}} [[free]] of {{gloss|not containing or unaffected by}}')
    ' free of '

    >>> apply_templates('[[blahblahblah|{{female equivalent of|es|hermano|gloss=sister}}]]')
    'sister'


    '''

    import mwparserfromhell
    wikicode = mwparserfromhell.parse(text)
    ret = []
    for node in wikicode.nodes:
        if type(node) is mwparserfromhell.nodes.wikilink.Wikilink:
            if node.text:
                ret.append(apply_templates(node.text))
            else:
                ret.append(apply_templates(node.title))
        elif type(node) is mwparserfromhell.nodes.template.Template:
            for param in node.params:
                if param.name == 'gloss':
                    ret.append(str(param.value))
        else:
            ret.append(str(node))
    return ''.join(ret)

    #parser = Lark(r"""
        #value: template
             #| link
             #| value+
             #| TEXT
#
        #link: "[[" TEXT ("|" value)? "]]"
#
        #template: "{{" parameter ("|" parameter?)* "}}"
#
        #parameter: assignment
                 #| pvalue
       # 
        #pvalue: value
#
        #assignment: value "=" value
#
        #TEXT: /[^\[\]{}|=]+/
        #""", start='value', parser='lalr')

    parser = Lark(r"""
        value: value? link
             | value? template
             | TEXT

        link: "[[" TEXT ("|" value)? "]]"

        template: "{{" TEXT ("|" TEXT?)* "}}"

        TEXT: /[^\[\]\{\}]+/
        """, start='value', parser='lalr')
    tree = parser.parse(text)
    print("tree=",tree)

    class MyTransformer(Transformer):
        def value(self, s):
            return ''.join(s)

        def link(self, xs):
            return xs[-1]

        def template(self, xs):
            return ''.join(xs)

        def parameter(self, s):
            return s[0]

        def pvalue(self, s):
            return ''

        def assignment(self, xs):
            if xs[0] in ['gloss']:
                return xs[1]
            return ''

        def TEXT(self, s):
            return s

    try:
        tree = parser.parse(text)
        #print("tree=",tree)
        #print("tree=",tree.pretty())

        result = MyTransformer().transform(tree)
        #print("result=",result)
    except Exception as e:
        logging.error(f'parse exception, text={text}')
        #raise
        return ''

    return result

"""
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


def extract_definitions(line):
    '''
    >>> extract_definitions("# [[free]] (''obtainable without payment'')")
    ['free']
    >>> extract_definitions('# [[perquisite]], [[free]] [[gift]]')
    ['perquisite', 'free gift']
    >>> extract_definitions('# {{lb|ms|Indonesia}} [[free]], without [[charge]]')
    ['free', 'without charge']
    >>> extract_definitions('# out of favor or kindness, without recompense or compensation, [[gratuitously]]')
    ['out of favor or kindness', 'without recompense or compensation', 'gratuitously']
    >>> extract_definitions('# [[#English|gratis]], [[free]]')
    ['gratis', 'free']
    >>> extract_definitions('# [[free]]; for free, without charge')
    ['free', 'for free', 'without charge']
    >>> extract_definitions("# [[free]]; [[unrestricted]]; ''more negative also:'' [[unrestrained]]; [[licentious]]")
    ['free', 'unrestricted', 'unrestrained', 'licentious']
    >>> extract_definitions("# {{lb|de|not freely applicable; see usage notes}} [[free of charge]], [[gratis]]")
    ['free of charge', 'gratis']
    >>> extract_definitions("# [[dog]] ''([[Canis familiaris]])''")
    ['dog']
    >>> extract_definitions('# {{inflection of|es|tú||dative}}: to you, for you')
    ['you', 'for you']

    >>> extract_definitions('# {{female equivalent of|es|hermano|gloss=sister}}')
    ['sister']

    # FIXME: see above
    > extract_definitions('# {{female equivalent of|es|hermano|t=sister}}')
    ['sister']

    FIXME:
    一共
    # {{lb|zh|figurative}} {{w|Mao Zedong|Mao}} or pre-[[w:Economic reform in the People's Republic of China|reform]] era of the [[People's Republic of China]]
    '''
    ret = []
    line = apply_templates(line)
    line = rm_parens(line)
    for part in re.split(r'[,;]', line[2:]):
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


def process_entry(title, text, rm_bad=True):
    r'''
    >>> json.dumps(process_entry('frei', find_entry('frei'), rm_bad=False)[1])
    '{"German": {"Adjective": {"free": 2, "unenslaved": 1, "unimprisoned": 1, "unrestricted": 1, "unrestrained": 1, "licentious": 1, "unblocked": 1, "free for passage": 1, "independent": 1, "unaffiliated": 1, "free of": 1, "liberal": 1, "free of charge": 1, "gratis": 1}}, "Pennsylvania German": {"Adjective": {"free": 1, "exempt": 1, "clear": 1}}, "Scots": {"Adjective": {"free": 1}}, "Sranan Tongo": {"Verb": {"fly": 1}, "Noun": {"wing": 1}}}'

    >>> json.dumps(process_entry('gratis', find_entry('gratis'), rm_bad=False)[1])
    '{"English": {"Adjective": {"Free": 1, "without charge": 1}, "Adverb": {"Free": 1, "without charge": 1}}, "Afrikaans": {"Adverb": {"free": 1, "without charge": 1}}, "Catalan": {"Adverb": {"free": 1, "for free": 1}}, "Danish": {"Adjective": {"gratis": 1, "free": 1}, "Adverb": {"gratis": 1, "free": 1}}, "Dutch": {"Adjective": {"free": 1, "without charge": 1}, "Adverb": {"free": 1, "without charge": 1}}, "French": {"Adverb": {"free": 1, "without charge": 1, "gratis": 1}, "Adjective": {"free": 1, "for free": 1, "without charge": 1}}, "Galician": {"Adjective": {"free": 1, "without charge": 1}, "Adverb": {"free": 1, "without charge": 1}}, "German": {"Adverb": {"free": 1, "without charge": 1}}, "Indonesian": {"Adjective": {"free": 1, "without charge": 1}}, "Italian": {"Adverb": {"gratis": 1, "free": 1}, "Adjective": {"free": 1}}, "Latin": {"Adverb": {"out of favor or kindness": 1, "without recompense or compensation": 1, "gratuitously": 1}}, "Malay": {"Adjective": {"free": 1, "without charge": 1}}, "Norwegian Bokm\\u00e5l": {"Adjective": {"free": 1}}, "Norwegian Nynorsk": {"Adjective": {"free": 1}}, "Polish": {"Noun": {"perquisite": 1, "free gift": 1}, "Adverb": {"free of charge": 1}}, "Romanian": {"Adverb": {"free of charge": 1, "for free": 1}, "Adjective": {"free of charge": 1, "for free": 1}}, "Spanish": {"Adjective": {"free": 1, "without charge": 1}, "Adverb": {"free": 1, "without charge": 1}}, "Swedish": {"Adverb": {"free": 1, "without charge": 1}, "Adjective": {"free": 1, "without charge": 1}}}'

    >>> json.dumps(process_entry('pies', find_entry('pies'), rm_bad=False)[1])
    '{"Cornish": {"Noun": {"magpies": 1}}, "Dutch": {"Noun": {"pee": 1, "piss": 1}}, "Kashubian": {"Noun": {"dog": 1}}, "Polish": {"Noun": {"dog": 1, "male dog": 1, "male fox or badger": 1, "cop": 1, "policeman": 1}}}'

    >>> json.dumps(process_entry('may', find_entry('may'), rm_bad=False)[1])
    '{"English": {"Verb": {"strong": 1, "have power": 1, "able": 1, "can": 1, "able to go": 1, "have permission": 1, "allowed": 1, "gather may": 1, "or flowers in general": 1, "celebrate May Day": 1}, "Noun": {"hawthorn bush or its blossoms": 1, "maiden": 1}}, "Azerbaijani": {"Noun": {"May": 1}}, "Bikol Central": {"Verb": {"there is": 1, "there\'s": 1, "have": 1}}, "Crimean Tatar": {"Noun": {"butter": 1, "oil": 1}}, "Kalasha": {"Determiner": {"my": 1}, "Pronoun": {"me": 1}}, "Mapudungun": {"Adverb": {"yes": 1}}, "Northern Kurdish": {"Noun": {"intervention": 1}}, "Pacoh": {"Pronoun": {"you": 1}}, "Quechua": {"Adverb": {"where": 1, "like": 1, "how": 1, "very": 1}, "Pronoun": {"which": 1}, "Verb": {"fear": 1}}, "Tagalog": {"Particle": {"have": 1}}, "Tatar": {"Noun": {"May": 1}}, "Vietnamese": {"Verb": {"sew": 1}, "Adjective": {"lucky": 1}}, "Walloon": {"Noun": {"May": 1}}}'
    '''

    if ' ' in title and rm_bad:
        return title, {}, {}

    lines = group_squiggles(text).split('\n')
    #if title == 'gratis':
        #print("text=",text)

    current_language = None
    current_subheader = None
    translations = defaultdict(lambda: defaultdict(lambda: Counter()))
    synonums = defaultdict(lambda: [])
    otherinfo = defaultdict(lambda: defaultdict(lambda: []))
    for line in lines:
        (level, header) = extract_header(line)
        if level == 2:
            current_language = header.strip()
        if level == 3 or level == 4:
            current_subheader = header.strip()
            current_subheader = current_subheader.replace('/', '_')
            if current_subheader == 'Numeral':
                current_subheader = 'Number'

        if len(line) >= 2 and line[0:2] == '# ':
            defns = extract_definitions(line)
            if rm_bad:
                defns = rm_bad_definitions(defns)
            if defns:
                translations[current_language][current_subheader].update(defns)

        matches = re.findall(r'\{\{[^\{\}]*\}\}', line)
        if matches:
            otherinfo[current_language][current_subheader].extend(matches)

    return [title, translations, otherinfo]
    #return [title, translations, otherinfo]
    #print(json.dumps(translations))
    #print(json.dumps(otherinfo, indent=4))


def write_output(dumpfile, outdir):
    for i, (title,text) in enumerate(iterate(dumpfile)):
        _, translations, other = process_entry(title, text)
        for lang in translations.keys():
            for pos in translations[lang].keys():
                if pos and lang:
                    try:
                        dirpath = os.path.join(outdir, lang)
                        os.makedirs(dirpath, exist_ok=True)
                        path = os.path.join(dirpath, 'translation.'+pos)
                        with open(path, 'at', encoding='utf-8') as fout:
                            fout.write(title + ':' + ','.join(translations[lang][pos].keys()) + '\n')
                    except FileNotFoundError as e:
                        logging.error(f'{e}')
        if i%1000 == 0:
            logging.info(f'i={i}, title={title}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    src_lang = 'en'
    write_output(dumpfile='data/'+src_lang+'wiktionary-20220701-pages-articles-multistream.xml', outdir='output.'+src_lang)
    #cleaner = Cleaner()
    #with open('out.jsonl', 'w') as fout:
        #for i, (title, text) in enumerate(iterate('data/enwiktionary-20220701-pages-articles-multistream.xml')):
            #print("i, title=",i, title)
            #fout.write(json.dumps(process_entry(title,text)))
            #fout.write('\n')
            #fout.flush()
            """
