#!/bin/sh

files="
$1/Adjective
$1/Adverb
$1/Conjunction
$1/Determiner
$1/Definitions
$1/Interjection
$1/Noun
$1/Number
$1/Numeral
$1/Pronoun
$1/Proper noun
$1/Verb
"

IFS='
'
for file in $files; do
    wc -l $file
done
