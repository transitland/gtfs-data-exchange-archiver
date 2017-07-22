import os
import requests
import re
import glob
import sys

url = 'http://54.144.84.97/api/v1/feed_versions'
auth_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMTksImV4cCI6MTUwMDc1ODI4NH0.Dj6cvb1zgxsfx7TbKzA7NZkEGoJa87bhGBa-QrHhG3o'
feed_onestop_id = 'f-r3dp-wwwactionactgovau'
folderName = 'action'

def makeFolderRequests(folderName): 
	owd = os.getcwd()
	changedirectory = './' + folderName
	os.chdir(changedirectory)
	url = 'http://54.144.84.97/api/v1/feed_versions'

	fileNames = retrieveFileNames(folderName)

	for name in fileNames: 
		response = makeOneRequest(name, folderName, url, feed_onestop_id, auth_token)
		if response.status_code != 200: 
			print response.status_code
			print response.text

	os.chdir(owd)

def makeOneRequest(fileName, folderName, url, feed_onestop_id, auth_token): 
	print "Running", fileName

	headers = {
	    'Authorization': 'Bearer ' + auth_token
	}
	files = [
	    ('feed_version[file]', ('current.zip', open(fileName, 'rb'), 'application/zip'))
	]

	data = {
		'feed_version[feed_onestop_id]': feed_onestop_id
	}

	r = requests.post(url, headers=headers, files=files, data=data)
	return r


def iterateFolders(): 
	rootdir = './transit_feeds'
	for filename in os.listdir(rootdir):
		print filename

def retrieveFileNames(folderName):
	return glob.glob('*.zip')


def main(): 
	folderName = sys.argv[1]
	feed_onestop_id = sys.argv[2]
	makeFolderRequests(folderName)


if __name__ == "__main__":
    main()