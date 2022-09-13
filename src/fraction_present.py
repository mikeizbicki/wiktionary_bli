#!/usr/bin/python3

import logging


def fraction_present(word_vector_path, bli_path, *, tgt_vectors_path=None, max_vocab=200000, print_every=10000):

    logging.info(f'loading {bli_path}')
    srcs = []
    with open(bli_path) as fin:
        for line in fin:
            src = line.split()[0]
            srcs.append(src)
    srcs_set = set(srcs)

    tgts_set = set()
    if tgt_vectors_path:
        logging.info(f'loading {tgt_vectors_path}')
        with open(tgt_vectors_path) as fin:
            for i, line in enumerate(fin):
                if max_vocab > 0 and i >= max_vocab:
                    break
                word = line.split()[0]
                tgts_set.add(word)

    logging.info(f'loading {word_vector_path}')
    words = []
    words_not_in_bli = []
    words_in_bli = 0
    words_in_tgt = 0
    with open(word_vector_path) as fin:
        for i, line in enumerate(fin):
            if max_vocab > 0 and i > max_vocab:
                break
            word = line.split()[0]
            words.append(word)
            if word in srcs_set:
                words_in_bli += 1
            elif word in tgts_set:
                words_in_tgt += 1
            else:
                words_not_in_bli.append(word)
            if i % print_every == 0 and i != 0:
                logging.info(f'i={i}, words_in_bli/i={words_in_bli/i:0.4f} (words_in_bli+words_in_tgt)/i={(words_in_bli+words_in_tgt)/i:0.4f}')

    #for i, word in enumerate(words_not_in_bli[:1000]):
        #logging.debug(f'word {i:06} not in bli is {word}')


if __name__ == '__main__':
    import clize
    logging.basicConfig(level=logging.DEBUG)
    clize.run(fraction_present)
