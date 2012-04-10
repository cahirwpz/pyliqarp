#!/usr/bin/env python3.3
# -*- coding: utf-8 -*-

import logging

from pyliqarp.client.disk import PoliqarpCorpus


def PoliqarpCorpusTest():
  """ Przykładowe użycie klasy PoliqarpCorpus. """
  corpus = PoliqarpCorpus("corpus/sample/sample")

  for n, word in enumerate(corpus):
    if word.base == 'bogaty':
      segments = map(str,
          [corpus[n-2], corpus[n-1], word.pretty(), corpus[n+1], corpus[n+2]])
      print('{0}: "{1}"'.format(n, ' '.join(segments)))


if __name__ == "__main__":
  logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

  PoliqarpCorpusTest()
