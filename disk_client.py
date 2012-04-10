#!/usr/bin/env python3.3
# -*- coding: utf-8 -*-

from pyliqarp.client.disk import PoliqarpCorpus


def PoliqarpCorpusTest():
  """ Przykładowe użycie klasy PoliqarpCorpus. """
  corpus = PoliqarpCorpus("corpus/sample/sample")

  for word in corpus:
    if word.base == 'bogaty':
      print(word.pretty())


if __name__ == "__main__":
	PoliqarpCorpusTest()
