import os 
import csv
import sys

# calls commands to import zipped folders and upload to Transitland using 
# uploadArchives.py 
def extract(feed_onestop_id, gtfs_name):
	print "Importing from GTFS Archives", gtfs_name
	command = 'python gtfsdx.py '+ gtfs_name
	os.system(command)

	uploadInfo = 'python uploadArchives.py ' + gtfs_name + ' ' + feed_onestop_id
	os.system(uploadInfo)


# goes through CSV file, extracts zipped folder from GTFS Archive and imports 
# into Transitland using information of feed_onestop_id and gtfs_name from 
# the CSV file 
def parseFile(filePath):
	with open(filePath, 'rU') as f:
		reader = csv.reader(f)
		for row in reader:
			# if not correct length, print out for debugging purposes 
			if len(row) != 8:
				print len(row)
				continue
			else:
				feed_onestop_id = row[0]
				gtfs_name = row[7]
				if gtfs_name != '':
					extract(feed_onestop_id, gtfs_name)

def main(): 
	# filePath is CSV file to be interpreted 
	filePath = sys.argv[1] 
	# filePath_default = 'feeds_CA.csv'
	parseFile(filePath)


if __name__ == "__main__":
    main()