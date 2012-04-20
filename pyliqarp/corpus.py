#!/usr/bin/env python
# -*- coding: utf-8 -*-

from array import array
from collections import Sequence
from functools import partial
from math import ceil

import glob
import logging
import mmap
import os
import struct

from pyliqarp.utils import LogTiming
from pyliqarp.records import Segment, Tagging


def _MapFile(path):
  if not os.path.isfile(path):
    raise IOError('File %s does not exist.' % path)

  logging.debug('Reading file "%s"', path)

  with open(path) as f:
    return mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

def _ArrayFromFile(path, typecode):
  data = array(typecode)
  data.frombytes(_MapFile(path))
  return data 


def PoliqarpSimpleDict(image, i, n):
  """Parses single record of simple dictionary."""
  return image[i: (i+n-1)].decode()


def PoliqarpSubposDict(image, i, n):
  """Parses single record of subpos dictionary."""
  record = struct.unpack('I' * (n >> 2), image[i: (i+n)])

  return [(n & 0xfffff, n >> 20) for n in record]


def ReadPoliqarpDict(parser, path):
  image = _MapFile(path + '.image')
  offsets = _ArrayFromFile(path + '.offset', 'i')

  lengths = [struct.unpack('i', image[(i-4) : i])[0] for i in offsets]
  records = [parser(image, i, n) for i, n in zip(offsets, lengths)]

  logging.info('Dictionary "%s" contains %d records.', os.path.basename(path),
      len(records))

  return records


ReadPoliqarpSimpleDict = partial(ReadPoliqarpDict, PoliqarpSimpleDict)
ReadPoliqarpSubposDict = partial(ReadPoliqarpDict, PoliqarpSubposDict)


def PoliqarpBaseFormDict(base_dict, tag_dict, subpos_dict):
  def UnfoldRecord(subpos):
    return [Tagging(base_dict[i1], tag_dict[i2]) for i1, i2 in subpos]

  return list(map(UnfoldRecord, subpos_dict))


class Corpus(Sequence):
  """Właściwa klasa implementująca słownik korpusu.

  Służy do odczytywania i przechowywania zawartości korpusu Poliqarp.
  
  Zachowuje się jak lista.  Nadaje się do losowych odczytów.
  """

  @classmethod
  def FromPath(cls, path):
    """Znajduje wspólny prefiks wszystkich plików korpusu."""
    files = glob.glob(os.path.join(path, '*'))
    prefix = os.path.commonprefix(files).rstrip('.')
    corpus = cls(prefix)
    corpus.LoadData()
    return corpus

  def __init__(self, prefix):
    """Konstruktor.

    @param prefix: prefiks wszystkich plików korpusu.
    """
    self._prefix = prefix
    self._segments = _MapFile(self._DictPath('corpus.image'))

    logging.info('Corpus "%s" contains %d segments.', os.path.dirname(prefix), len(self))

  def _DictPath(self, name):
    return '{0}.poliqarp.{1}'.format(self._prefix, name)

  def _LoadTaggingData(self, tags, num):
    base = ReadPoliqarpSimpleDict(self._DictPath('base%d' % num))

    try:
      interp = ReadPoliqarpSubposDict(self._DictPath('subpos%d' % num))
    except IOError:
      interp = ReadPoliqarpSubposDict(self._DictPath('interp%d' % num))

    return PoliqarpBaseFormDict(base, tags, interp)

  @LogTiming('Loading auxiliary dictionaries')
  def LoadData(self):
    """Wczytaj słowniki pomocnicze."""
    self._orth = ReadPoliqarpSimpleDict(self._DictPath('orth'))

    tags = ReadPoliqarpSimpleDict(self._DictPath('tag'))

    self._disamb = self._LoadTaggingData(tags, 1)

    # Otagowania przed ujednoznacznieniem
    # self._amb = self._LoadTaggingData(tags, 2)

  def Split(self, k):
    """Split the corpus into k equally sized ranges."""
    n = len(self)
    start = range(0, n, ceil(n / k))
    end = list(start[1:]) + [n]
    return [range(first, last) for first, last in zip(start, end)]

  def _CreateSegment(self, i, n):
    separated = bool(n & 1)

    # 21 bitowe indeksy
    ai = int((n >> 1) & 0x1FFFFF)

    # Indeks do ujednoznacznionej listy otagowań
    bi = int((n >> 22) & 0x1FFFFF)

    # Indeks do listy pierwotnych otagowań
    # ci = int((n >> 43) & 0x1FFFFF)

    return Segment(i, separated, self._orth[ai], self._disamb[bi])

  def __len__(self):
    return int(self._segments.size() / 8)

  def __getitem__(self, i):
    j = i * 8
    n = struct.unpack('q', self._segments[j:j+8])[0]
    return self._CreateSegment(i, n)

  def __iter__(self):
    for i in range(len(self)):
      yield self[i]


class SegmentRange(Sequence):
  """Klasa służąca do efektywnego przeglądania fragmentu korpusu."""

  def __init__(self, corpus, first=None, last=None):
    self._corpus = corpus
    self._first = first or 0
    self._last = last or len(corpus)
    self._range = None

    indexRange = range(len(corpus) + 1)

    if ((self._first not in indexRange) or (self._last not in indexRange) or
        (self._first >= self._last)):
      raise IndexError

    self._Load()

  @LogTiming('Loading segments from corpus')
  def _Load(self):
    """Wczytaj segmenty."""
    self._range = array('Q')
    self._range.frombytes(self._corpus._segments[self._first*8:self._last*8])

    logging.info('Loaded %d segments from the corpus.', len(self))

  def __len__(self):
    return len(self._range)

  def __getitem__(self, i):
    return self._corpus[i]

  def __iter__(self):
    for i, n in enumerate(self._range, start=self._first):
      yield self._corpus._CreateSegment(i, n)
