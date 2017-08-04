import os 
import sys 
import csv

def parseFile(filePath):

	with open(filePath, 'rU') as f:
		reader = csv.reader(f)
		for row in reader:
			feed_onestop_id = row[0]
			command = 'python findAverage.py '+ feed_onestop_id
			os.system(command)

def main(): 
	filePath = sys.argv[1] 
	parseFile(filePath)



if __name__ == "__main__":
    main()