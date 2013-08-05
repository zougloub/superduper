#!/usr/bin/env python

APPNAME="deduppy"
VERSION="0.1"

from waflib import Utils

def options(opt):
	opt.load("gnu_dirs")

def configure(conf):
	conf.load("gnu_dirs")

def build(bld):
	bld.install_as("${BINDIR}/deduppy", "deduppy.py", chmod=Utils.O755)
	bld.install_files("${DOCDIR}", ["README"])
