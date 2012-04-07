#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple


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
