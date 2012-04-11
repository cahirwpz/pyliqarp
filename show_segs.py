#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys

from pyliqarp.corpus import Corpus


def ParseArguments():
  parser = argparse.ArgumentParser(
      description='Print out selected range of segments from a corpus.')
  parser.add_argument('--corpus', type=str, default='./corpus/sample',
      help='path to directory containing Poliqarp corpus')
  parser.add_argument('--first', type=int, default=0,
      help='index of first segment to show (numbering starts from 0)')
  parser.add_argument('--count', type=int, default=0,
      help='number of segments to show (default: all)')

  args = parser.parse_args()

  if not os.path.isdir(args.corpus):
    raise SystemExit('Directory "%s" does not exist!' % args.corpus)

  return args


if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

  if (sys.version_info.major, sys.version_info.minor) < (3, 3):
    raise SystemExit('Python 3.3 is required.')

  args = ParseArguments()
  corpus = Corpus.FromPath(args.corpus)

  args.count = args.count or len(corpus)

  last = args.count + args.first

  if last > len(corpus):
    last = len(corpus)

  for i in range(args.first, last):
    print(corpus[i].pretty(), end=' ')

  print()
