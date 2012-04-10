#!/usr/bin/env python3.2
# -*- coding: utf-8 -*-

from array import array
from collections import Sequence
from functools import partial
from math import ceil

import mmap
import os
import stat
import struct

from pyliqarp.common.records import Word, Tagging


def ReadPoliqarpDict(parser, prefix, name):
    image = ReadImageFile(prefix, name)
    offsets = ReadOffsetFile(prefix, name)

    lengths = [struct.unpack('i', image[(i-4) : i])[0] for i in offsets]
    records = [parser(image, i, n) for i, n in zip(offsets, lengths)]

    print("%s '%s' contains %d records." % (parser.__name__, name, len(records)))

    return records


def ReadOffsetFile(prefix, name):
    path = '{0}.poliqarp.{1}.offset'.format(prefix, name)

    if not os.path.isfile(path):
        raise IOError('File %s does not exist.' % path)

    with open(path, 'rb') as f:
        offsets = array('i')
        offsets.frombytes(f.read())

    return offsets


def ReadImageFile(prefix, name):
    path = '{0}.poliqarp.{1}.image'.format(prefix, name)

    if not os.path.isfile(path):
        raise IOError('File %s does not exist.' % path)

    with open(path) as f:
        fd = f.fileno()
        size = os.fstat(fd)[stat.ST_SIZE]
        image = mmap.mmap(fd, size, mmap.MAP_PRIVATE)

    return image


def ReadImageFileAsArray(prefix, name, typecode):
    path = '{0}.poliqarp.{1}.image'.format(prefix, name)

    if not os.path.isfile(path):
        raise IOError('File %s does not exist.' % path)

    with open(path, 'rb') as f:
        fd = f.fileno()
        size = os.fstat(fd)[stat.ST_SIZE]
        image = array(typecode)
        image.fromfile(f, int(size / image.itemsize))

    return image


def PoliqarpSimpleDict(image, i, n):
    """Parses single record of simple dictionary."""
    return image[i: (i+n-1)].decode()


def PoliqarpTagsDict(image, i, n):
    """Parses single record of tags dictionary."""
    return tuple(image[i: (i+n-1)].decode().split(':'))


def PoliqarpSubposDict(image, i, n):
    """Parses single record of subpos dictionary."""
    record = array('i', struct.unpack("H" * (n >> 1), image[i: (i+n)]))

    return [(record[i], record[i+1] >> 4)
            for i in range(0, len(record), 2)]


ReadPoliqarpSimpleDict = partial(ReadPoliqarpDict, PoliqarpSimpleDict)
ReadPoliqarpTagsDict = partial(ReadPoliqarpDict, PoliqarpTagsDict)
ReadPoliqarpSubposDict = partial(ReadPoliqarpDict, PoliqarpSubposDict)


def PoliqarpBaseFormDict(base_dict, tag_dict, subpos_dict):
    def UnfoldRecord(subpos):
        return [Tagging(base_dict[i1], tag_dict[i2]) for i1, i2 in subpos]

    return list(map(UnfoldRecord, subpos_dict))


class PoliqarpCorpus(Sequence):
    """ Właściwa klasa implementująca słownik korpusu.
    
    Implementuje interator i operator indeksowania (można odczytywać
    poszczególne słowa, jak z listy).
    """

    def __init__(self, prefix):
        """
          @param prefix	- prefiks określający ścieżkę do słownika.
        """
        # wczytaj słowniki pomocnicze
        self.orth_dict = ReadPoliqarpSimpleDict(prefix, "orth") 

        try:
          subpos = ReadPoliqarpSubposDict(prefix, "subpos1")
        except IOError:
          subpos = ReadPoliqarpSubposDict(prefix, "interp1")

        self.baseform_dict = PoliqarpBaseFormDict(
                ReadPoliqarpSimpleDict(prefix, "base1"),
                ReadPoliqarpTagsDict(prefix, "tag"),
                subpos)

        self.corpus_dict = ReadImageFileAsArray(prefix, 'corpus', 'Q')

        print("PoliqarpCorpus: %s words in corpus." % len(self))

    def __len__(self):
        return len(self.corpus_dict)

    def __getitem__(self, i):
        if type(key) is not IntType:
            raise TypeError
        if key < 0 or key >= len(self):
            raise IndexError

        return self.__get_item_at(key)

    def __iter__(self):
        for i in range(len(self)):
            yield self.__get_item_at(i)

    def __get_item_at(self, key):
        n = self.corpus_dict[key]

        # 21 bitowe indeksy
        ai = int((n >> 1) & 0x1FFFFF)
        bi = int((n >> 22) & 0x1FFFFF)
        ci = int((n >> 43) & 0x1FFFFF)

        return Word(self.orth_dict[ai], self.baseform_dict[bi])
