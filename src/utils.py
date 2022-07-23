

def pair_to_line(srcs, tgts):
    r'''
    >>> pair_to_line(['feliz', 'felices'], ['happy', 'this, is, a test'])
    'feliz,felices:happy,this\\, is\\, a test'
    '''
    return ','.join([escape(src) for src in srcs]) + ':' + ','.join([escape(tgt) for tgt in tgts])


def line_to_pair(line):
    r'''
    >>> line_to_pair('feliz,felices:happy,this\\, is\\, a test')
    [['feliz', 'felices'], ['happy', 'this, is, a test']]
    '''
    src_line, tgt_line = split_unescape(line, ':')
    srcs = split_unescape(src_line, ',')
    tgts = split_unescape(tgt_line, ',')
    return [srcs, tgts]


def escape(s, badchars=':,\\', escape='\\'):
    r'''
    >>> escape('test')
    'test'
    >>> escape('test:test')
    'test\\:test'
    >>> escape('test\\test')
    'test\\\\test'
    '''
    ret = []
    for c in s:
        if c in badchars:
            ret.append(escape)
        ret.append(c)
    return ''.join(ret)


# see: https://stackoverflow.com/questions/18092354/python-split-string-without-splitting-escaped-character/21882672#21882672
def split_unescape(s, delim, escape='\\', unescape=True):
    """
    >>> split_unescape('foo,bar', ',')
    ['foo', 'bar']
    >>> split_unescape('foo$,bar', ',', '$')
    ['foo,bar']
    >>> split_unescape('foo$$,bar', ',', '$', unescape=True)
    ['foo$', 'bar']
    >>> split_unescape('foo$$,bar', ',', '$', unescape=False)
    ['foo$$', 'bar']
    >>> split_unescape('foo$', ',', '$', unescape=True)
    ['foo$']
    """
    ret = []
    current = []
    itr = iter(s)
    for ch in itr:
        if ch == escape:
            try:
                # skip the next character; it has been escaped!
                if not unescape:
                    current.append(escape)
                current.append(next(itr))
            except StopIteration:
                if unescape:
                    current.append(escape)
        elif ch == delim:
            # split! (add current to the list and reset it)
            ret.append(''.join(current))
            current = []
        else:
            current.append(ch)
    ret.append(''.join(current))
    return ret
