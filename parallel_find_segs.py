#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import multiprocessing
import sys

from itertools import chain

from find_segs import *


def Worker(indexRange):
  global corpus
  global baseform

  return FindSegments(SegmentRange(corpus, indexRange.start, indexRange.stop), baseform)


if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(processName)s %(levelname)s %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

  if (sys.version_info.major, sys.version_info.minor) < (3, 3):
    raise SystemExit('Python 3.3 is required.')

  global corpus
  global baseform

  args = ParseArguments()
  corpus = Corpus.FromPath(args.corpus)
  baseform = args.baseform

  pool = multiprocessing.Pool()
  results = pool.map(Worker, corpus.Split(multiprocessing.cpu_count()))
  PrintSegments(corpus, chain.from_iterable(results))
