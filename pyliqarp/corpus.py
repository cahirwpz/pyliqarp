#!/usr/bin/env python
# -*- coding: utf-8 -*-

from array import array
from collections import Sequence
from functools import partial
from math import ceil
from os import path

import glob
import logging
import mmap
import os
import stat
import struct

from pyliqarp.utils import LogTiming
from pyliqarp.records import Segment, Tagging


def _MapFile(path):
  if not os.path.isfile(path):
    raise IOError('File %s does not exist.' % path)

  logging.info('Reading file "%s"', path)

  with open(path) as f:
    fd = f.fileno()
    size = os.fstat(fd)[stat.ST_SIZE]
    data = mmap.mmap(fd, size, mmap.MAP_PRIVATE)

  return data 

def _ArrayFromFile(path, typecode):
  mapped = _MapFile(path)

  data = array(typecode)
  data.frombytes(mapped)

  return data 


def PoliqarpSimpleDict(image, i, n):
  """Parses single record of simple dictionary."""
  return image[i: (i+n-1)].decode()


def PoliqarpTagsDict(image, i, n):
  """Parses single record of tags dictionary."""
  return tuple(image[i: (i+n-1)].decode().split(':'))


def PoliqarpSubposDict(image, i, n):
  """Parses single record of subpos dictionary."""
  record = array('i', struct.unpack('H' * (n >> 1), image[i: (i+n)]))

  return [(record[i], record[i+1] >> 4)
      for i in range(0, len(record), 2)]


def ReadPoliqarpDict(parser, path):
  image = _MapFile(path + '.image')
  offsets = _ArrayFromFile(path + '.offset', 'i')

  lengths = [struct.unpack('i', image[(i-4) : i])[0] for i in offsets]
  records = [parser(image, i, n) for i, n in zip(offsets, lengths)]

  logging.info('Dictionary "%s" contains %d records.', os.path.basename(path),
      len(records))

  return records


ReadPoliqarpSimpleDict = partial(ReadPoliqarpDict, PoliqarpSimpleDict)
ReadPoliqarpTagsDict = partial(ReadPoliqarpDict, PoliqarpTagsDict)
ReadPoliqarpSubposDict = partial(ReadPoliqarpDict, PoliqarpSubposDict)


def PoliqarpBaseFormDict(base_dict, tag_dict, subpos_dict):
  def UnfoldRecord(subpos):
    return [Tagging(base_dict[i1], tag_dict[i2]) for i1, i2 in subpos]

  return list(map(UnfoldRecord, subpos_dict))


class PoliqarpCorpus(Sequence):
  """Właściwa klasa implementująca słownik korpusu.

  Służy do odczytywania zawartości korpusu Poliqarp.  Implementuje interator
  oraz operator indeksowania.
  """

  @classmethod
  def FromPath(cls, corpus_path):
    """Znajduje wspólny prefiks wszystkich plików korpusu."""
    corpus_files = glob.glob(path.join(corpus_path, '*'))
    prefix = path.commonprefix(corpus_files).rstrip('.')
    corpus = cls(prefix)
    corpus.LoadData()
    corpus.LoadSegments()
    return corpus

  def __init__(self, prefix):
    """Konstruktor.

    @param prefix: prefiks wszystkich plików korpusu.
    """
    self._prefix = prefix

  def _DictPath(self, name):
    return '{0}.poliqarp.{1}'.format(self._prefix, name)

  @LogTiming('Loading auxiliary dictionaries')
  def LoadData(self):
    """Wczytaj słowniki pomocnicze."""
    self._orth = ReadPoliqarpSimpleDict(self._DictPath('orth'))

    try:
      interp = ReadPoliqarpSubposDict(self._DictPath('subpos1'))
    except IOError:
      interp = ReadPoliqarpSubposDict(self._DictPath('interp1'))

    base = ReadPoliqarpSimpleDict(self._DictPath('base1'))
    tag = ReadPoliqarpTagsDict(self._DictPath('tag'))

    self._baseform = PoliqarpBaseFormDict(base, tag, interp)

  @LogTiming('Loading corpus segments')
  def LoadSegments(self):
    """Wczytaj segmenty."""
    self._segments = _ArrayFromFile(self._DictPath('corpus.image'), 'Q')

    logging.info('Loaded %d segments from the corpus.', len(self))

  def __len__(self):
    return len(self._segments)

  def __getitem__(self, i):
    n = self._segments[i]

    # 21 bitowe indeksy
    ai = int((n >> 1) & 0x1FFFFF)
    bi = int((n >> 22) & 0x1FFFFF)
    # ci = int((n >> 43) & 0x1FFFFF)

    return Segment(i, self._orth[ai], self._baseform[bi])

  def __iter__(self):
    for i in range(len(self)):
      yield self[i]
