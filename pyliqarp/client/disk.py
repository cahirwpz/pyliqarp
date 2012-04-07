#!/usr/bin/env python
# -*- coding: utf-8 -*-

from array import array
from collections import namedtuple
from functools import partial
from itertools import izip

import mmap
import os
import stat
import struct
import struct


class Tagging(namedtuple('Tagging', 'base tags')):
    """Klasa pomocnicza przechowująca otagowanie i formę bazową.

    Potrzebna kiedy słowo nie daje się jednoznacznie otagować i występuje w
    kilku formach.
    """
    __slots__ = ()

    def pretty(self):
        return "[\033[1;37m%s\033[0m|\033[1;33m%s\033[0m]" % (self.base, ':'.join(self.tags))


class Word(namedtuple('Word', 'orth baseforms')):
    """ Klasa przechowująca słowo wraz z jego wszystkimi niejednoznacznymi
    otagowaniami.

    @field orth: słowo
    @field baseforms: lista wszystkich możliwych otagowań
    @field base: pierwotna forma bazowa
    @field tags: pierwotne otagowanie

    @method pretty		- wydrukowanie z kolorkami
    """

    @property
    def base(self):
        return self.baseforms[0].base

    @property
    def tags(self):
        return self.baseforms[0].tags

    def pretty(self):
        return "\033[1;31m%s\033[0m %s" % (self.orth, self.baseforms[0].pretty())


def ReadPoliqarpDict(parser, prefix, name):
    image = ReadImageFile(prefix, name)
    offsets = ReadOffsetFile(prefix, name)

    lengths = [struct.unpack('i', image[(i-4) : i])[0] for i in offsets]
    records = [parser(image, i, n) for i, n in izip(offsets, lengths)]

    print "%s '%s' contains %d records." % (parser.__name__, name, len(records))

    return records


def ReadOffsetFile(prefix, name):
    path = '{0}.poliqarp.{1}.offset'.format(prefix, name)

    if not os.path.isfile(path):
        raise IOError('File %s does not exist.' % path)

    with open(path) as f:
        offsets = array('i')
        offsets.fromstring(f.read())

    return offsets


def ReadImageFile(prefix, name):
    path = '{0}.poliqarp.{1}.image'.format(prefix, name)

    if not os.path.isfile(path):
        raise IOError('File %s does not exist.' % path)

    with open(path) as f:
        fd = f.fileno()
        image = mmap.mmap(fd, os.fstat(fd)[stat.ST_SIZE], mmap.MAP_PRIVATE)

    return image


def PoliqarpSimpleDict(image, i, n):
    """Parses single record of simple dictionary."""
    return image[i: (i+n-1)]


def PoliqarpTagsDict(image, i, n):
    """Parses single record of tags dictionary."""
    return tuple(image[i: (i+n-1)].split(':'))


def PoliqarpSubposDict(image, i, n):
    """Parses single record of subpos dictionary."""
    record = array('i', struct.unpack("H" * (n >> 1), image[i: (i+n)]))

    return [(record[i], record[i+1] >> 4)
            for i in xrange(0, len(record), 2)]


ReadPoliqarpSimpleDict = partial(ReadPoliqarpDict, PoliqarpSimpleDict)
ReadPoliqarpTagsDict = partial(ReadPoliqarpDict, PoliqarpTagsDict)
ReadPoliqarpSubposDict = partial(ReadPoliqarpDict, PoliqarpSubposDict)


def PoliqarpBaseFormDict(base_dict, tag_dict, subpos_dict):
    def UnfoldRecord(subpos):
        return [Tagging(base_dict[i1], tag_dict[i2]) for i1, i2 in subpos]

    return map(UnfoldRecord, subpos_dict)


class PoliqarpCorpus(object):
    """ Właściwa klasa implementująca słownik korpusu.
    
    Implementuje interator i operator indeksowania (można odczytywać
    poszczególne słowa, jak z listy).
    """

    def __init__(self, prefix):
        """
          @param prefix	- prefiks określający ścieżkę do słownika.
        """
        path = prefix + ".poliqarp.corpus.image"

        if not os.path.isfile(path):
            raise IOError('File %s does not exist.' % path)

        # wczytaj słowniki pomocnicze
        self.orth_dict = ReadPoliqarpSimpleDict(prefix, "orth") 
        self.baseform_dict = PoliqarpBaseFormDict(
                ReadPoliqarpSimpleDict(prefix, "base1"),
                ReadPoliqarpTagsDict(prefix, "tag"),
                ReadPoliqarpSubposDict(prefix, "subpos1"))

        size = os.stat(path)[stat.ST_SIZE]

        with open(path) as f:
            fd = f.fileno()
            size = os.fstat(fd)[stat.ST_SIZE]
            self.corpus_dict = mmap.mmap(fd, size, mmap.MAP_PRIVATE)
            self.corpus_size = size >> 3

        # podsumowanie
        print "PoliqarpCorpus:", str(len(self)), "words in corpus."

    def __len__(self):
        return self.corpus_size

    def __getitem__(self, key):
        if type(key) is not IntType:
            raise TypeError
        if key < 0 or key >= len(self):
            raise IndexError

        return self.__get_item_at(key)

    def __iter__(self):
        for i in range(len(self)):
            yield self.__get_item_at(i)

    def __get_item_at(self, key):
        i = key << 3
        n = struct.unpack('q', self.corpus_dict[i:(i+8)])[0]

        # 21 bitowe indeksy
        ai = int((n >> 1) & 0x1FFFFF)
        bi = int((n >> 22) & 0x1FFFFF)
        ci = int((n >> 43) & 0x1FFFFF)

        return Word(self.orth_dict[ai], self.baseform_dict[bi])
