#!/usr/bin/env python
#coding: utf-8

from distutils.core import setup

setup(
      name = "python-chain"
    , author = "Stephen Moore"
    , author_email = "stephen@delfick.com"
    , version = "1.0"
    , license = "WTFPL"
    , description = "Class for making any object have a chainable API."
    , py_modules = ["chain"]
    , extras_require = {
          'tests' : [
              'https://bitbucket.org/delfick/nose-of-yeti/src'
            , 'https://delfick@github.com/delfick/pinocchio.git'
            , 'should-dsl'
            , 'fudge'
            ]
        }
    )
