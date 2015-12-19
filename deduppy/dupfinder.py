#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# deduppy - duplicate finder

BLOCKSIZE = 1024 * 8

class DupFinder(object):
	def __init__(self):
		self._files = {} # files, by size
		self._bytes_read = 0
		self._num_files = 0
		self._cfg_ignore_smaller_than = 1

        def printf(self, x):
            pass

	def add(self, a_file):
		size = a_file.stat.st_size
		self._files.setdefault(size,[]).append(a_file)

	def _clear_singles(self):
		"""
			remove self._files entries which have only one file
		"""
		self.printf("Clearing singles...")
		singles = [size for size, files in self._files.items() if len(files) == 1]
		for size in singles:
			self._files.pop(size)
		self.printf("OK\n")

	def _clear_small(self):
		"""
			remove self._files entries which have too small sizes
		"""
		self.printf("Clearing too small...")
		smalls = filter(lambda size: size < self._cfg_ignore_smaller_than, self._files.keys())
		for size in smalls:
			self._files.pop(size)
		self.printf("OK: %d items\n" % len(smalls))

	def get_duplicate_groups(self, size, files):
		"""
			Returns the list of identical files in the files file list
		"""
		groups = [files]

		pos = 0
		eof = False
		while not eof:
			if groups == []:
				break
			n_groups = []

			for group in groups:
				chunks = {}

				sz = None
				for f in group:
					f.open()
					chunk = f.read(pos, BLOCKSIZE)
					sz = len(chunk)
					self._bytes_read += sz
					chunks.setdefault(chunk,[]).append(f)
				pos += sz

				for matches in chunks.values():
					if len(matches) == 1:
						# file has been singled out, forget it
						fn = matches[0]
						fn.close()
					else:
						#matches - a list of filenames, are possibly duplicates
						n_groups.append(matches)

				if b'' in chunks:
					eof = True

			groups = n_groups

		for g in groups:
			for f in g:
				f.close()

		return groups

	def execute(self):
		self._clear_singles()
		self._clear_small()

		self.printf("Potential duplicates at this point:\n")
		for k, v in sorted(self._files.items()):
			self.printf("- % 12d: %s\n" % (k, v))

		ngroups = len(self._files.keys())
		group = 1

		dupes = []
		for size, files in sorted(self._files.items()):
			self.printf("\rChecking for dupes of size %d (%d/%d)..." % (size, group, ngroups))
			same = self.get_duplicate_groups(size, files)
			if same != []:
				dupes.append((size, same))
			self.printf("OK")
			group += 1
		self.printf("\n")

		return dupes
