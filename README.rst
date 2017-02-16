.. -*- coding: utf-8; indent-tabs-mode:nil; -*-

##########
SuperDuper
##########

.. role:: menu(literal)
.. role:: path(literal)
.. role:: cmd(literal)
.. role:: term(literal)
.. role:: var(literal)
.. role:: envar(var)
.. role:: doc(emphasis)
.. role:: repo(literal)
.. role:: product(literal)
.. role:: msg(literal)
.. role:: class(literal)

SuperDuper is yet another duplicate finder tool, but also much more.
It's designed to be a python library that can crawl through folder-like stuff,
for any purposes.


Design
######

A collection of files is loaded in memory (limitation).
The collection is filtered.

- :class:`Store`

  Represents a location from which files are found.

- :class:`File`

  Files have:

  - a reference to their :class:`Store`
  - a path
  - a size
  - a handle (used to read the data)

- :class:`DupFinder` eats Files and identifies duplicates


Installation
############


Usage
#####

Front-end tools are available:

- :path:`filesearcher.py`

TODO
####

- Count number of readdir()
- Count number of stat()
- Count number of bytes read
- Limit number of bytes read per file
- Count time

