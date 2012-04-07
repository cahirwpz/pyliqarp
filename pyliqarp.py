#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

###############################################################################
#
# Poliqarp Access Module
#
# autorzy:	Krystian Bacławski <krystian.baclawski@gmail.com>
# 			Rafał Jasicki <szamanvv@gmail.com>
#
# licencja:	GPLv2
#
# uwagi:	Testowane pod 'Debian GNU/Linux Etch'.
#			Wymagane kodowanie łańcuchów znakowych UTF-8.
#
###############################################################################

from types import *
from array import *
from collections import namedtuple
from itertools import izip
from functools import partial
from UserList import UserList

import struct
import socket
import sys
import os
import mmap
import stat
import struct

###############################################################################

class DerivedWord(namedtuple('DerivedWord', 'base tags')):
    """Klasa pomocnicza przechowująca otagowanie i formę bazową.

    Potrzebna kiedy słowo nie daje się jednoznacznie otagować i występuje w
    kilku formach.
    """
    __slots__ = ()

    @classmethod
    def Create(cls, base, tags):
        return cls(base, frozenset(tags.split(':')))

    def __contains__(self, tag):
        return (tag in self.tags)

    def pretty(self):
        return "[\033[1;37m%s\033[0m|\033[1;33m%s\033[0m]" % (self.base, ':'.join(sorted(self.tags)))


class PoliqarpWord(object):
    """ Klasa przechowująca słowo wraz z jego wszystkimi niejednoznacznymi
    otagowaniami.

    @field orth 		- słowo
    @field base 		- pierwotna forma bazowa
    @field tags 		- pierwotne otagowanie
    @field baseforms	- lista PoliqarpWord.Ambiguation

    @method pretty		- wydrukowanie z kolorkami
    """

    def __init__(self, orth, baseforms):
        """
        @param orth 		- słowo
        @param baseforms	- lista par (forma bazowa, tagi)
        """
        assert (type(orth) is StringType) and orth

        self.__baseforms = [DerivedWord.Create(base, tags) for base, tags in baseforms]
        self.__orth		 = orth

    @property
    def orth(self):
        return self.__orth

    @property
    def base(self):
        return self.__baseforms[0].base

    @property
    def tags(self):
        return self.__baseforms[0].tags

    @property
    def baseforms(self):
        return self.__baseforms

    def __contains__(self, tag):
        return (tag in self.tags)

    def __str__(self):
        return "%s %s" % (self.orth, self.__baseforms[0])

    def pretty(self):
        return "\033[1;31m%s\033[0m %s" % (self.orth, self.__baseforms[0].pretty())


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


def PoliqarpSubposDict(image, i, n):
    """Parses single record of subpos dictionary."""
    record = array('i', struct.unpack("H" * (n >> 1), image[i: (i+n)]))

    return [(record[i], record[i+1] >> 4)
            for i in xrange(0, len(record), 2)]


ReadPoliqarpSimpleDict = partial(ReadPoliqarpDict, PoliqarpSimpleDict)
ReadPoliqarpSubposDict = partial(ReadPoliqarpDict, PoliqarpSubposDict)


def PoliqarpBaseFormDict(base_dict, tag_dict, subpos_dict):
    def UnfoldRecord(subpos):
        return [(base_dict[i1], tag_dict[i2]) for i1, i2 in subpos]

    return map(UnfoldRecord, subpos_dict)


class PoliqarpCorpus(object):
    """
        Właściwa klasa implementująca słownik korpusu. Implementuje interator i
        operator indeksowania (można odczytywać poszczególne słowa, jak z listy).
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
                ReadPoliqarpSimpleDict(prefix, "tag"),
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

        return PoliqarpWord(self.orth_dict[ai], self.baseform_dict[bi])


class PoliqarpDaemonClient:
	"""
		Klasa umożliwiająca wykonywanie zapytań do serwera poliqarpd. Więcej na
		temat formatu zapytań w dokumentacji do poliqarp'a.
	"""

	def __init__(self):
		pass
	
	def connect(self, host = "localhost", port = 4567):
		"""
			Łączenie z serwerem poliqarpd.

			@param host	- komputer, z którym się łączyć (domyślnie: localhost)
			@param port	- port połączenia (domyślnie: 4567)
		"""
		self.__conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		try:
			self.__conn.connect((host, port))
		except socket.error, (code, error):
			print error
			return False
		
		self.__conn.settimeout(1.0)

		return True
	
	def close(self):
		"""	Zamknięcie połączenia. """
		self.__conn.close()

	def __command(self, cmd, expected = 0):
		self.__conn.send(cmd + "\n")

		buffer	= ""
		lines	= []
		status	= None

		while (len(lines) < expected) or status == None:
			try:	l = self.__conn.recv(4096)
			except:
				l = ""
				print ".", 

			if l.startswith("R OK"):
				l = l[4:]
				status = True

			if l.startswith("R ERR"):
				l = l[5:]
				status = False

			buffer += l

			if buffer.endswith("\n"):
				lines += buffer.strip().splitlines()
				buffer = ""

		res = [ l.split() for l in lines ]

		if not status:
			res = False
		elif status and res == []:
			res = True

		return res

	def session_begin(self):
		"""	Otwarcie sesji z serwerem. """
		return self.__command("MAKE-SESSION CLIENT")

	def session_configure(self, dict, lctx_width = 5, rctx_width = 5):
		"""
			Konfiguracja sesji.

			@param dict 		- słownik do zadawania zapytań
			@param lctx_width	- szerokość lewego kontekstu
			@param rctx_width	- szerokość prawego kontekstu

			@returns True jeśli się powiodło, w p.p. False
		"""
		self.__command("SET left-context-width %d" % lctx_width)
		self.__command("SET right-context-width %d" % rctx_width)
		self.__command("SET wide-context-width 50")
		self.__command("SET retrieve-lemmata 0110")
		self.__command("SET retrieve-tags 0110")
		self.__command("SET query-flags 0011")
		self.__command("SET disamb 1")

		if self.__command("OPEN " + dict, 1)[0][1] == "OPENFAIL":
			print "%s: no such dictionary." % dict
			return False

		self.__command("METADATA-TYPES", 1)

		return True

	def query(self, query, bufsize = 1000):
		"""
			Zadawanie zapytania do poliqarpd.

			@param query 	- zapytanie w postaci tekstowej
			@param bufsize	- maksymalna ilość odpowiedzi (ograniczenie poliqarpd)

			@returns lista obiektów PoliqarpDaemonClient.Answer
		"""
		assert (type(bufsize) is IntType) and (type(query) is StringType)

		if not self.__command("MAKE-QUERY " + query):
			print "Query \'%s\' is not valid." % query
			return []

		self.__command("BUFFER-RESIZE %d" % bufsize)

		res = self.__command("RUN-QUERY %d" % bufsize, 1)

		occurences = int(res[0][2])

		if not occurences:
			return []

		output 	= []
		begin	= 0
		end		= 10

		while begin < occurences:
			if end >= occurences:
				end = occurences - 1

			res = self.__command("GET-RESULTS %d %d" % (begin, end))

			res = [ res[i][1] for i in range(len(res)) ]

			for i in range(end - begin + 1):
				# lewy kontekst
				n_lctx	= int(res.pop(0))
				lctx 	= res[0 : n_lctx]

				del res[0: n_lctx]

				# segmenty
				assert int(res.pop(0)) == 0

				n_segs	= int(res.pop(0))
				segs	= []

				# dla każdego segmentu
				for s in range(n_segs):
					orth 		= res.pop(0)
					baseforms 	= []
					
					# ilość niejednoznacznych otagowań
					n_tags = int(res.pop(0))

					# pobierz pary (forma bazowa, tagi)
					for t in range(n_tags):
						baseforms.append((res.pop(0), res.pop(0)))

					# dopisz kolejny segment
					segs.append(PoliqarpWord(orth, baseforms))

				# prawy kontekst
				n_rctx	= int(res.pop(0))
				rctx 	= res[0 : n_rctx]
				
				del res[0: n_rctx]

				# dodaj wynik do listy
				output.append(PoliqarpDaemonClient.Answer(lctx, segs, rctx))

			begin	+= 10
			end		+= 10

		return output

	class Answer:
		"""
			Klasa przechowująca informację o pojedyńczym wyniku zapytania do
			serwera poliqarpd. Implementuje iterator i operator indeksowania
			po wszystkich segmentach.

			@field lctx	- lista słów kontekstu po lewej stronie segmentów
			@field rctx	- lista słów kontekstu po prawej stronie segmentów
		"""

		def __init__(self, lctx, segs, rctx):
			self.__lctx = lctx
			self.__segs = segs
			self.__rctx = rctx

			self.__iter_index = 0
		
		def __getattr__(self, name):
			if name == "lctx":
				return self.__lctx
			elif name == "rctx":
				return self.__rctx
			else:
				raise AttributeError(name)

		def __len__(self):
			return len(self.__segs)

		def __getitem__(self, key):
			if (type(key) is not IntType) or (key < 0) or (key >= len(self)):
				raise IndexError

			return self.__segs[key]

		def __iter__(self):
			self.__iter_index = 0
			return self

		def next(self):
			if self.__iter_index == len(self):
				raise StopIteration

			r = self[self.__iter_index] 

			self.__iter_index += 1

			return r

###############################################################################

def PoliqarpCorpusTest():
    """ Przykładowe użycie klasy PoliqarpCorpus. """
    corpus = PoliqarpCorpus("../frek/frek")
    #corpus = PoliqarpCorpus("../sample/sample")

    for word in corpus:
        if word.base == 'bogaty':
            print word.pretty()

# -----------------------------------------------------------------------------

def PoliqarpDaemonClientTest():
    """ Przykładowe użycie klasy PoliqarpDaemonClientTest. """
    if len(sys.argv) != 2:
        print "Usage:", sys.argv[0], "\"query\""
        sys.exit(0)

    corpus = PoliqarpDaemonClient()

    if not corpus.connect("localhost", 4567):
        sys.exit(0)

    corpus.session_begin()

    if corpus.session_configure("../frek/frek"):
        answers = corpus.query(sys.argv[1], 20000)

        print "Got %d answers for query \'%s\':\n" % (len(answers), sys.argv[1])

        for i in range(len(answers)):
            answer = answers[i]

            print "%d: \033[1;32m%s\033[0m %s \033[1;32m%s\033[0m\n" % (i + 1, join(answer.lctx), join([answer[j].pretty() for j in range(len(answer))]) , join(answer.rctx))

    corpus.close()

###############################################################################

if __name__ == "__main__":
	#PoliqarpDaemonClientTest()
	PoliqarpCorpusTest()

# vim: sw=4 ts=4
