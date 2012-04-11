#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import multiprocessing
import pickle
import sys

from collections import namedtuple

from find_segs import *

WorkerArgs = namedtuple('WorkerArgs', 'baseform first last')


def Worker(args):
  global corpus

  FindSegments(SegmentRange(corpus, args.first, args.last), args.baseform)


if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(processName)s %(levelname)s %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

  if (sys.version_info.major, sys.version_info.minor) < (3, 3):
    raise SystemExit('Python 3.3 is required.')

  global corpus

  args = ParseArguments()
  corpus = Corpus.FromPath(args.corpus)

  pool = multiprocessing.Pool()
  pool.map(Worker, [WorkerArgs(args.baseform, r.start, r.stop)
                    for r in corpus.Split(multiprocessing.cpu_count())])
