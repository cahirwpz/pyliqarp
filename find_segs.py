#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys

from pyliqarp.corpus import Corpus


def ParseArguments():
  parser = argparse.ArgumentParser(
      description='Find all occurences of a segment with given base form.')
  parser.add_argument('--corpus', type=str, default='./corpus/sample',
      help='path to directory containing Poliqarp corpus')
  parser.add_argument('--baseform', type=str, default='bogaty',
      help='base form of words to be looked for')

  args = parser.parse_args()

  if not os.path.isdir(args.corpus):
    raise SystemExit('Directory "%s" does not exist!' % args.corpus)

  return args


def FindSegments(corpus, baseform):
  """Searches through corpus for segments with given base form."""
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

  args = ParseArguments()

  FindSegments(Corpus.FromPath(args.corpus), args.baseform)
