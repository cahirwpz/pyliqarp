#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging


def LogTiming(desc=None):
  """Decorator generator that logs the time it takes a function to execute."""
  def decorator(func):
    def wrapper(*args, **kwargs):
        nonlocal desc

        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        logging.debug('%s took %.3fs.' % (desc or func.__name__, elapsed))

        return result

    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    return wrapper
  return decorator
