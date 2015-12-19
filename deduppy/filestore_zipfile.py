#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# file store for zip archives, using python zipfile

import zipfile

from . import filestore

class ZipInfoStat(object):
	def __init__(self):
		self.st_size = 0

class FileStore_ZipFile(filestore.FileStore):
	"""
	Files store for zipfile
	"""
	def __init__(self, root, max_files=None):
		self.root = root
		self._files = {} # name -> File
		self._open_files = {} # relpath -> file object
		self._handle = zipfile.ZipFile(self.root, "r")

	def url(self):
		return 'zip://' + self.root + '/'

	def file_open(self, fn):
		fh = self._handle.open(fn, 'r')
		self._open_files[fn] = [fh, 0]
		return fh

	def file_close(self, fn):
		assert fn in self._open_files
		f, _ = self._open_files[fn]
		assert not f.closed
		f.close()
		del self._open_files[fn]

	def file_read(self, fn, pos, size):
		assert fn in self._open_files
		fh, fp = self._open_files[fn]
		if fp != pos:
			self.file_close(fn)
			fh = self.file_open(fn)
			fh.read(pos)
		res = fh.read(size)
		self._open_files[fn][1] += len(res)
		return res

	def walk(self):
		lst = self._handle.infolist()
		for info in lst:
			relpath = info.filename
			stat = ZipInfoStat()
			stat.st_size = info.file_size
			f = filestore.File(self, relpath, stat)
			self._files[relpath] = f
			yield f

	def __str__(self):
		return '(store path="zip://%s")' % (self.root)
