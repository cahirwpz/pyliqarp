#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import sys

from os import path

from pyliqarp.corpus import PoliqarpCorpus


def PoliqarpCorpusTest(path, baseform):
  """ Przykładowe użycie klasy PoliqarpCorpus. """
  corpus = PoliqarpCorpus.FromPath(path)

  for segment in corpus:
    if segment.base == baseform:
      n = segment.position
      segments = map(str, [corpus[n-2], corpus[n-1], segment.pretty(),
                           corpus[n+1], corpus[n+2]])
      print('{0}: "{1}"'.format(n, ' '.join(segments)))


if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

  if (sys.version_info.major, sys.version_info.minor) < (3, 3):
    raise SystemExit('Python 3.3 is required.')

  parser = argparse.ArgumentParser(
      description='Find all occurences of a segment with given base form.')
  parser.add_argument('--corpus', type=str, default='./corpus/sample',
      help='path to directory containing Poliqarp corpus')
  parser.add_argument('--baseform', type=str, default='bogaty',
      help='base form of words to be looked for')

  args = parser.parse_args()

  if not path.isdir(args.corpus):
    raise SystemExit('Directory "%s" does not exist!' % args.corpus)

  PoliqarpCorpusTest(args.corpus, args.baseform)
