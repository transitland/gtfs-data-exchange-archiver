import os 
import csv

def extract(feed_onestop_id, gtfs_name):
	print "Importing", gtfs_name
	command = 'python gtfsdx.py '+ gtfs_name
	os.system(command)
	uploadInfo = 'python uploadArchives.py ' + gtfs_name + ' ' + feed_onestop_id
	os.system(uploadInfo)


def parseFile(filePath):

	with open('feeds_CA.csv', 'rU') as f:
		reader = csv.reader(f)
		for row in reader:
			if len(row) != 8:
				print len(row)
				continue
			else:
				feed_onestop_id = row[0]
				gtfs_name = row[7]
				if gtfs_name != '':
					extract(feed_onestop_id, gtfs_name)

def main(): 
	filePath = './feeds_CA.txt'
	parseFile(filePath)


if __name__ == "__main__":
    main()