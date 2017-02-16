#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# PYTHON_ARGCOMPLETE_OK

import deduppy.filestore

import io, sys, os, time, subprocess

try:
	import re2 as re
except ImportError:
	import re
else:
	re.set_fallback_notification(re.FALLBACK_WARNING)

class RelpathSearchRegexp(object):
	def __init__(self, pat):
		self._pat = re.compile(pat)

	def __call__(self, relpat):
		m = re.search(self._pat, relpat)
		return m


class ContentSearchFullText(object):
	def __init__(self, pat):
		self._pat = re.compile(pat)

	def __call__(self, f):
		if f.relpath.endswith(".pdf"):
			path = os.path.join(f.store.root, f.relpath)
			if os.path.exists(path):
				cmd = [
				 "pdftotext",
				 path,
				 "/dev/stdout",
				]
				data = subprocess.check_output(cmd)
			else:
				data = b""
		else:
			s = f.stat.st_size
			f.open()
			data = f.read(0, s)
			f.close()
		res = [x for x in re.finditer(self._pat, data)]
		#print(res)
		return res


class ContentSearchAny(object):
	def __init__(self):
		pass

	def __call__(self, f):
		return True

class FileSearcher(object):
	def __init__(self, store_arg,
	 dir_recurse_func=None,
	 filename_func=None,
	 contents_func=None,
	):
		if dir_recurse_func is None:
			dir_recurse_func = lambda x: True
		if filename_func is None:
			filename_func = lambda x: True
		if contents_func is None:
			contents_func = lambda x: True

		self._store = deduppy.filestore.create(store_arg)
		self._path_func = filename_func
		self._contents_func = contents_func
		self._dir_recurse_func = dir_recurse_func

	def walk(self):
		for f in self._store.walk(dir_recurse_func=self._dir_recurse_func):
			#print(f)
			res = self._path_func(f.relpath)
			if res is None:
				yield res, f
				continue

			res = self._contents_func(f)
			yield res, f


def ContentSearchFactory(name):
	if name.startswith("rebytes:"):
		pat = name[len("rebytes:"):].encode()
		return ContentSearchFullText(pat)

	if name.startswith("any:"):
		return ContentSearchAny()

	raise NotImplementedError(name)


def RelpathSearchFactory(name):
	if name.startswith("re:"):
		pat = name[len("re:"):]
		return RelpathSearchRegexp(pat)

	raise NotImplementedError(name)



if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(
	 description="reStructuredText helper",
	)

	subparsers = parser.add_subparsers(
	 help='the command; type "%s COMMAND -h" for command-specific help' % sys.argv[0],
	 dest='command',
	)

	parser_search = subparsers.add_parser(
	 'search',
	 help="Search in files only",
	)

	parser_search.add_argument("--relpath-spec",
	 help="File names to consider",
	 type=RelpathSearchFactory,
	 default=lambda x: True,
	)

	parser_search.add_argument("--contents-spec",
	 help="Spec for file contents matching (eg. fts_re://<re>",
	 type=ContentSearchFactory,
	)

	parser_search.add_argument("--folder",
	 help="Folder to search in (default .)",
	 default=".",
	 nargs="+",
	)

	parser_search.add_argument("--dont-enter-into",
	 help="Folder to search in (default .)",
	 nargs="+",
	 default=[".git", "build"],
	)


	try:
		import argcomplete
		argcomplete.autocomplete(parser)
	except:
		pass

	args = parser.parse_args()

	def printf(x):
		sys.stdout.write(x)

	class Printer():
		def __init__(self):
			self._state = 1
			self.verbose = True

		def debug(self, x):
			if not self.verbose:
				return
			if self._state == 1:
				printf('\x1b[?25l')
				self._state = 0
			for c in x:
				if c == '\n':
					printf("\r\x1b[K")
					continue
				printf(c)

		def printf(self, x):
			if self._state == 0:
				printf("\r\x1b[K")
				printf("\x1b[?25h")
				self._state = 1
			printf(x)

	if args.command == 'search':

		ts_a = time.time()
		total_size = 0
		p = Printer()

		known_useless_basenames = set(args.dont_enter_into)

		for folder in args.folder:

			orig_dev = os.stat(folder).st_dev
			def dir_recurse_fun(path):
				path_dev = os.stat(path).st_dev
				if path_dev != orig_dev:
					return False
				basename = os.path.basename(path)
				if basename in known_useless_basenames:
					return False
				return True

			finder = FileSearcher(folder,
			 dir_recurse_func=dir_recurse_fun,
			 filename_func=args.relpath_spec,
			 contents_func=args.contents_spec,
			)

			try:
				for matches, f in finder.walk():
					p.debug("%s..." % (f.relpath))
					if matches is None:
						p.debug("no\n")
						continue
					if matches != []:
						p.debug("yes\n")

						for match_p in matches:
							gotit = False
							try:
								m = match_p
								p.printf("\x1B[32m%s: %s %s\x1B[0m\n" % (f, m.groups(), m.groupdict()))
								gotit = True
							except:
								pass

							if not gotit:
								p.printf("\x1B[32m%s\x1B[0m\n" % (f))
					else:
						p.debug("no\n")
			finally:
				printf("\x1b[?25h")
