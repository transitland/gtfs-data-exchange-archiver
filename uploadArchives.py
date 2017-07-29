import os
import requests
import re
import glob
import sys
import csv

# global variables per folder, requests
url = 'http://54.144.84.97/api/v1/feed_versions'
auth_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyMTksImV4cCI6MTUwMTM1MzEyN30.jlqHtZoR5h4z6wu3ys03w_n6O0p3RRl_zVveOsav8qc'

# goes through one folder; iterates through all files to make requests
def makeFolderRequests(folderName, feed_onestop_id): 
	errorFileStringName = 'errorFile' + folderName + '.csv'
	errorFile = csv.writer(open(errorFileStringName, 'w'))

	owd = os.getcwd()
	changedirectory = './' + folderName
	os.chdir(changedirectory)
	url = 'http://54.144.84.97/api/v1/feed_versions'

	fileNames = retrieveFileNames(folderName)

	for name in fileNames: 
		response = makeOneRequest(name, folderName, url, feed_onestop_id, auth_token)
		# failed request printed out here for debugging purposes 
		if response.status_code != 200: 
			array = [folderName, feed_onestop_id, response.status_code, response.text]
			errorFile.writerow(array)
			print response.status_code
			print response.text

	os.chdir(owd)

# makes one request per file 
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

# returns only the zipped folders 
def retrieveFileNames(folderName):
	return glob.glob('*.zip')

def main(): 
	# arguments match folder from GTFS feed to feed_onestop_id
	folderName = sys.argv[1]
	feed_onestop_id = sys.argv[2]
	makeFolderRequests(folderName, feed_onestop_id)


if __name__ == "__main__":
    main()