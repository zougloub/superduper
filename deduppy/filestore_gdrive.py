#!/usr/bin/env python
# -*- coding: utf-8 vi:noet
# file store for Google Drive

import io
import httplib2
import apiclient.discovery
import apiclient.http
import apiclient.errors
import oauth2client.client

from . import filestore

class GoogleDriveInfoStat(object):
	def __init__(self):
		self.st_size = 0
		self.st_id = None

class FileStore_GoogleDrive(filestore.FileStore):
	"""
	Files store for Google Drive
	"""
	def __init__(self, credentials_json, root, max_files=None):
		credentials = oauth2client.client.OAuth2Credentials.new_from_json(credentials_json)
		self._http = http = httplib2.Http()
		credentials.authorize(http)
		self.root = root
		self._files = {} # name -> File
		self._open_files = {} # relpath -> file object
		self._drive_service = apiclient.discovery.build('drive', 'v3', http=http)

	def url(self):
		if self.root == "/":
			return 'gdrive://'
		else:
			return 'gdrive://' + self.root + '/'

	def file_open(self, fn):
		drive_service = self._drive_service
		fh = self._files[fn]
		request = drive_service.files().get(
		 fileId=self._files[fn].stat.st_id,
		 fields='mimeType',
		)
		response = request.execute()
		if response.get('mimeType') in ('application/vnd.google-apps.document', 'application/vnd.google-apps.spreadsheet'):
			return None
		self._open_files[fn] = fh
		return response

	def file_close(self, fn):
		assert fn in self._open_files
		del self._open_files[fn]

	def file_read(self, fn, pos, size):
		drive_service = self._drive_service
		assert fn in self._open_files
		request = drive_service.files().get_media(
		 fileId=self._files[fn].stat.st_id,
		)
		fh = io.BytesIO()
		downloader = apiclient.http.MediaIoBaseDownload(fh, request)
		downloader._progress = pos
		downloader._chunksize = size
		status, done = downloader.next_chunk()
		res = fh.getvalue()
		return res

	def walk(self):
		drive_service = self._drive_service

		# first get list of folders
		foldername_dict = {}
		parent_dict = {}
		page_token = None
		while True:
			response = drive_service.files().list(
			 q="mimeType='application/vnd.google-apps.folder'",
			 spaces='drive',
			 fields='nextPageToken, files(parents, id, name)',
			 pageToken=page_token).execute()
			for f in response.get('files', []):
				_id = f.get('id')
				parent_dict[_id] = f.get('parents')
				foldername_dict[_id] = f.get('name')
			page_token = response.get('nextPageToken', None)
			if page_token is None:
				break;

		page_token = None
		while True:
			response = drive_service.files().list(
			 spaces='drive',
			 fields='nextPageToken, files(parents, mimeType, size, id, name)',
			 pageToken=page_token).execute()
			for file in response.get('files', []):
				_id = file.get('id')
				if _id in parent_dict:
					continue

				if file.get('mimeType') in (
				 'application/vnd.google-apps.document',
				 'application/vnd.google-apps.spreadsheet',
				 'application/vnd.google-apps.presentation',
				 'application/vnd.google-apps.form',
				 ):
					continue

				name = file.get('name')
				try:
					size = int(file.get('size'))
				except TypeError:
					raise NotImplementedError("Not implemented: %s" % str(file))
				except ValueError:
					raise NotImplementedError("Not implemented: %s" % str(file))

				fullpath = [name]
				parents = file.get('parents')
				while True:
					if not parents:
						break
					daddy = parents[0]
					if daddy not in foldername_dict:
						#print("Cannot find %s" % daddy)
						#for k, v in sorted(foldername_dict.items(), key = lambda x: x[1]):
						#	print("%s: %s" % (v, k))
						break
					fullpath.insert(0, foldername_dict[daddy])
					parents = parent_dict[daddy]

				relpath = "/".join(fullpath)
				stat = GoogleDriveInfoStat()
				stat.st_size = size
				stat.st_id = _id
				f = filestore.File(self, relpath, stat)
				self._files[relpath] = f
				yield f

			page_token = response.get('nextPageToken', None)
			if page_token is None:
				break;

	def __str__(self):
		return '(store path="gdrive://%s")' % (self.root)

