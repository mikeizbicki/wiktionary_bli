# Wiktionary_bli

This is a collection of training and testing datasets for the Bilingual Lexicon Induction problem.
The dataset and motivation are described in the paper [Aligning Word Vectors on Low-Resource Languages with Wiktionary](paper/paper.pdf)

The `/final` folder contains the datasets for each language.
For example, for the Korean language datasets are located at

| final name | purpose |
| --- | --- |
| `/final/ko-en.all` | the full collection of word/definition pairs extracted from wiktionary |
| `/final/ko-en.train` | the training set |
| `/final/ko-en.test` | the full test set |
| `/final/ko-en.testsmall` | the small test set|

<!--
## Recreating the data

```
$ sh src/download.sh        # download the wiktionary dump
$ python3 src/extract.py    # generate the intermediate data files
$ sh src/to_bli_dataset.sh  # construct the BLI dataset from the intermediate files
```
-->
