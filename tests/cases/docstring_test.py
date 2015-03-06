import sys
import os
import doctest
from base import TestCase

if __name__ == '__main__':
    finder = doctest.DocTestFinder(verbose=True, recurse=True, exclude_empty=True)
    print finder.find(gaia)
