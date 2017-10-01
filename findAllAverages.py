import os 
import sys 
import csv
import requests
import os.path

def parseFile(onestop_id):

	feed_onestop_id = onestop_id
	command = 'python findAverage.py '+ feed_onestop_id
	averageFileName = "Avgs-"+onestop_id+".csv"
	if not os.path.isfile(averageFileName):
		os.system(command)

def main(): 
	per_page = 900
	feeds = requests.get('https://transit.land/api/v1/feeds', params={'per_page': per_page}).json()['feeds']
	for feed in feeds:
		print 'Processing', feed['onestop_id']
		parseFile(feed['onestop_id'])



if __name__ == "__main__":
    main()