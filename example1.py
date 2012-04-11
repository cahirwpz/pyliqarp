#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

from pyliqarp.client.disk import PoliqarpCorpus


def PoliqarpCorpusTest():
  """ Przykładowe użycie klasy PoliqarpCorpus. """
  corpus = PoliqarpCorpus("corpus/sample/sample")

  for segment in corpus:
    if segment.base == 'bogaty':
      n = segment.position
      segments = map(str, [corpus[n-2], corpus[n-1], segment.pretty(),
                           corpus[n+1], corpus[n+2]])
      print('{0}: "{1}"'.format(n, ' '.join(segments)))


if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

  if (sys.version_info.major, sys.version_info.minor) < (3, 3):
    raise SystemExit('Python 3.3 is required.')

  PoliqarpCorpusTest()
