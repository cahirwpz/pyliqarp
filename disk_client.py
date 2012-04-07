#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyliqarp.client.disk import PoliqarpCorpus


def PoliqarpCorpusTest():
    """ Przykładowe użycie klasy PoliqarpCorpus. """
    corpus = PoliqarpCorpus("frek/frek")

    for word in corpus:
        if word.base == 'bogaty':
            print word.pretty()


if __name__ == "__main__":
	PoliqarpCorpusTest()
