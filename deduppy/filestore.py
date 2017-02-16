#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# file store base classes

class File(object):
	"""
	Simple file wrapper
	"""
	def __init__(self, store=None, relpath=None, stat=None):
		self.store = store
		self.relpath = relpath
		self.stat = stat

	def open(self):
		return self.store.file_open(self.relpath)

	def close(self):
		return self.store.file_close(self.relpath)

	def read(self, pos, size):
		return self.store.file_read(self.relpath, pos, size)

	def __str__(self):
		return self.url()
		return "(file store=%s relpath=%s size=%d)" \
		 % (self.store, self.relpath, self.stat.st_size)

	__repr__ = __str__

	def url(self):
		return self.store.url() + self.relpath

class FileStore(object):
	"""
	ABC for file store
	"""
	def __init__(self, path):
		pass

	def file_open(self, relpath):
		raise NotImplementedError()

	def file_read(self, relpath, pos, size):
		raise NotImplementedError()

	def file_close(self, relpath):
		raise NotImplementedError()

	def walk(self, dir_recurse_func=None):
		raise NotImplementedError()

	def __str__(self):
		raise NotImplementedError()

	__repr__ = __str__

	def url(self):
		return 'unknown://'
