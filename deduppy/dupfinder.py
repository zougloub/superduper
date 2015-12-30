#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# deduppy - duplicate finder

class DupFinder(object):
	def __init__(self, ignore_exc=None, ignore_smaller_than=1, file_read_max=-1, blocksize=1024*8):
		self._files = {} # files, by size
		self._bytes_read = 0
		self._num_files = 0
		self._cfg_ignore_smaller_than = ignore_smaller_than
		self._ignore_exc = ignore_exc
		self._file_read_max = file_read_max
		self._blocksize = blocksize

	def printf(self, x):
		pass

	def add(self, a_file):
		size = a_file.stat.st_size
		self._files.setdefault(size,[]).append(a_file)

	def _clear_singles(self):
		"""
		remove entries which have only one file
		"""
		self.printf("Clearing singles...")
		singles = [size for size, files in self._files.items() if len(files) == 1]
		for size in singles:
			self._files.pop(size)
		self.printf("OK\n")

	def _clear_small(self):
		"""
		remove entries which have too small sizes
		"""
		self.printf("Clearing too small...")
		smalls = [x for x in self._files.keys() if x < self._cfg_ignore_smaller_than]
		for size in smalls:
			self._files.pop(size)
		self.printf("OK: %d items\n" % len(smalls))

	def get_duplicate_groups(self, size, files):
		"""
		Returns the list of identical files in the file list
		:param size: group size
		:param files: files that are candidate
		:return: a list of lists of files that are identical between themselves
		"""
		groups = [files]

		pos = 0
		eof = False
		while not eof:
			if groups == []:
				break

			if self._file_read_max > -1 and pos >= self._file_read_max:
				break

			n_groups = [] # next groups

			for group in groups:
				chunks = {}

				sz = None
				for idx_f, f in enumerate(group):
					try:
						f.open()
					except:
						if self._ignore_exc is None:
							raise
						elif not self._ignore_exc():
							raise
						else:
							del group[idx_f]
							continue

					chunk = f.read(pos, self._blocksize)
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
		for size, files in sorted(self._files.items(), reverse=True):
			self.printf("\rChecking for dupes of size %d (%d/%d)..." % (size, group, ngroups))
			same = self.get_duplicate_groups(size, files)
			if same != []:
				dupes.append((size, same))
			self.printf("OK")
			group += 1
		self.printf("\n")

		return dupes
