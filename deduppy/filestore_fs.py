#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# file store for filesystem trees

__author__ = 'Jérôme Carretero <cJ-deduppy@zougloub.eu>'

import sys, os, resource, stat

from . import filestore

class FileStore_FS(filestore.FileStore):
	"""
	Filesystem files store.

	It can hold a certain amount of open file descriptors
	"""
	def __init__(self, root, max_files=None):
		self.root = root
		self._files = {} # name -> File
		self._open_files = {} # relpath -> file object
		if not max_files:
			max_files = resource.getrlimit(resource.RLIMIT_OFILE)[0] - 3
		self._max_open_files = max_files

	def url(self):
		return 'file://' + self.root + '/'

	def file_open(self, fn):
		if fn in self._open_files:
			return

		if len(self._open_files) == self._max_open_files:
			self.close_a_file()

		path = os.path.join(self.root, fn)
		fh = open(path, 'rb')
		self._open_files[fn] = fh

	def file_close(self, fn):
		if fn not in self._open_files:
			return

		f = self._open_files[fn]
		assert not f.closed

		f.close()
		del self._open_files[fn]

	def file_read(self, fn, pos, size):
		if not fn in self._open_files:
			file_open(fn)

		fh = self._open_files[fn]
		fh.seek(pos)
		return fh.read(size)

	def close_a_file(self):
		k = self._open_files.keys()[0]
		fh = self._open_files[k]
		fh.close()
		del self._open_files[k]

	def walk(self):
		for cwd, dirs, files in os.walk(self.root):
			dirs.sort()
			files.sort()
			for f in files:
				path = os.path.join(cwd, f)
				relpath = os.path.relpath(path, self.root)

				st = os.lstat(path)
				size = st.st_size
				tup = st.st_dev, st.st_ino

				if not stat.S_ISREG(st.st_mode):
					continue

				#if tup in self._inodes:
				#	return
				#self._inodes.add(tup)

				f = filestore.File(self, relpath, st)

				self._files[relpath] = f
				yield f

	def __str__(self):
		return '(store path="file://%s")' % (self.root)


if __name__ == '__main__':

	def printf(x):
		sys.stdout.write(x)
		sys.stdout.flush()

	s = FileStore_FS("..")
	s.printf = printf

	for f in s.walk():
		print(f)


