#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Program / Library used to find duplicate files

__author__ = 'Jérôme Carretero <cJ-deduppy@zougloub.eu>'

__copyright__ = """
Copyright (c) 2012 Jérôme Carretero.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  * Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

  * Neither the name of the author nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sys, os, optparse, pickle, pprint

BLOCKSIZE = 1024 * 8

verbose = 0

def printf(x):
	if verbose > 0:
		sys.stdout.write(x)
		sys.stdout.flush()

class File(object):
	""" Simple file descriptor wrapper """
	def __init__(self, _file=None, _pos=None):
		self.file = _file
		self.pos = _pos

class Files(object):
	"""
		File cache, which can hold a certain amount
		of open file descriptors
	"""
	def __init__(self, max_files=None):
		self._files = {} # name -> handle dictionary
		self._open_files = 0
		if not max_files:
			import resource
			max_files = resource.getrlimit(resource.RLIMIT_OFILE)[0] - 3
		self._max_open_files = max_files

	def open(self, fn):
		if fn in self._files:
			f = self._files[fn]
			if f.file is not None:
				return f.file
			pos = f.pos
		else:
			pos = 0

		# not in cache, open the file + cache it

		if self._open_files == self._max_open_files:
			self.close_a_file()

		fh = open(fn, 'rb')
		if pos:
			fh.seek(pos)
		self._files[fn] = File(fh, pos)

		self._open_files += 1

		return fh

	def close(self, fn, remove=False):
		f = self._files[fn]
		fh = f.file
		if fh and not fh.closed:
			pos = fh.tell()
			fh.close()
			self._open_files -= 1
		else :
			remove = True

		if remove or pos == 0:
			del self._files[fn]
		else :
			f.pos = pos
			f.file = None

	def close_a_file(self):
		for k,v in self._files.items():
			if v.file is not None:
				self.close(k)
				return

class DupFinder(object):

	def __init__(self,dirs=None):
		self._files = {} # files, by size
		self._inodes = set()
		self._file_handles = Files()
		self._dirs = []
		self._bytes_read = 0
		self._num_files = 0
		if dirs:
			self.add_dirs(dirs)

	def add_dirs(self, dirs):
		for d in dirs:
			p = os.path.abspath(d)
			if p not in self._dirs:
				self._dirs.append(p)

	def _add_file(self, fn):
		if os.path.islink(fn):
			return
		stat = os.stat(fn)
		size = stat.st_size
		tup = stat.st_dev, stat.st_ino
		if tup in self._inodes:
			return
		self._inodes.add(tup)
		self._files.setdefault(size,[]).append(fn)

	def _walk_dir(self, dir):
		for path, dirs, files in os.walk(dir):
			for f in files:
				fn = os.path.join(path, f)
				self._add_file(fn)
				self._num_files += 1

	def _build_flist(self):
		printf("Building file list...")
		for d in self._dirs:
			printf("(%s)..." % d)
			self._walk_dir(d)
		printf("OK\n")

	def _clear_singles(self):
		"""
			remove self._files entries which have only one file
		"""
		printf("Clearing singles...")
		singles = [size for size, files in self._files.items() if len(files) == 1]
		for size in singles:
			self._files.pop(size)
		printf("OK\n")

	def _clear_small(self):
		"""
			remove self._files entries which have too small sizes
		"""
		printf("Clearing too small...")
		smalls = [size for size, files in self._files.items() if size < 10]
		for size in smalls:
			self._files.pop(size)
		printf("OK: %d items\n" % len(smalls))

	def is_dup(self, size, files):
		"""
			Returns the list of identical files in the files file list
		"""
		groups = [files]

		eof = False
		while not eof:
			if groups == []:
				break
			n_groups = []

			for group in groups:
				chunks = {}

				for fn in group:
					f = self._file_handles.open(fn)
					chunk = f.read(BLOCKSIZE)
					self._bytes_read += BLOCKSIZE
					chunks.setdefault(chunk,[]).append(fn)

				for matches in chunks.values():
					if len(matches) == 1:
						# file has been singled out, forget it
						fn = matches[0]
						self._file_handles.close(fn, remove=True)
					else:
						#matches - a list of filenames, are possibly duplicates
						n_groups.append(matches)

				if b'' in chunks:
					eof = True

			groups = n_groups

		for g in groups:
			for f in g:
				self._file_handles.close(f, remove=True)

		return groups

	def find_dups(self):
		self._build_flist()
		self._clear_singles()
		self._clear_small()

		#printf("Potential duplicates at this point: %s\n" % self._files)

		ngroups = len(self._files.keys())
		group = 1

		dupes = []
		for size, files in sorted(self._files.items()):
			printf("\rChecking for dupes of size %d (%d/%d)..." % (size, group, ngroups))
			same = self.is_dup(size, files)
			if same != []:
				dupes.append((size, same))
			printf("OK")
			group += 1
		printf("\n")

		assert(self._file_handles._open_files == 0)
		return dupes

def main():

	global verbose

	parser = optparse.OptionParser(
	 usage="%prog [options] <dirs>\n%prog --help for details",
	 version="%prog 1.0.0"
	)

	parser.add_option(
	 "-q", "--quiet",
	 action="store_false",
	 dest="verbose",
	 default=True,
	 help="don't print status messages to stdout"
	)

	parser.add_option(
	 "", "--hardlink",
	 action="store_true",
	 dest="hardlink",
	 help="hard-link identical files",
	)

	parser.add_option(
	 "", "--dump",
	 dest="dump",
	 help="dump list of dupes to file",
	)

	parser.add_option(
	 "", "--load",
	 dest="load",
	 help="load list of dupes from file",
	)

	options, args = parser.parse_args()

	if args == []:
		parser.print_version()
		parser.print_usage()
		os._exit(1)

	verbose = 1 if options.verbose else 0

	if options.load:
		printf("Loading dupe list from file...")
		with open(options.load, "rb") as f:
			alldupes = pickle.load(f)
		printf("OK\n")
	else:
		d = DupFinder()

		printf("Looking for duplicates in %s\n" % args)

		d.add_dirs(args)
		alldupes = d.find_dups()

		if options.verbose:
			printf("Total files: %d\n" % d._num_files)
			printf("Bytes read: %d\n" % d._bytes_read)

	if options.dump:
		with open(options.dump, "wb") as f:
			pickle.dump(alldupes, f)

	#print("Alldupes=%s" % pprint.pformat(alldupes, depth=150, width=10000))
	#return

	if options.verbose:
		print("Report:")

	for size, dupes in sorted(alldupes):
		if options.verbose:
			sys.stdout.write("- size %s\n" % size)

		for files in dupes:
			if options.hardlink:
				orig = files[0]
				for f in files[1:]:
					printf("Link %s <- %s ..." % (orig, f))
					if not os.path.exists(f) or not os.path.exists(orig):
						continue
					os.rename(f, f + ".dupe")
					os.link(orig, f)
					os.unlink(f + ".dupe")
					printf("OK\n")
			else:
				for f in files:
					printf("\t%s" % f) #pprint.pprint(f, depth=150, width=1000))
			printf("\n")

if __name__ == "__main__":
	main()

