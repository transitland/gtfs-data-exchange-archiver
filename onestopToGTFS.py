import os 
import csv
import re
import sys

# from the CSV file, looks for a URL (sourceOfFeed) that matches an entity in the 
# html GTFS Page. If found, returns the GTFS name. If not, returns "Failed."
def searchForMatchSource(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page, debugger):
	position = gtfs_page.find(sourceOfFeed)

	if position != -1: 
		substring = gtfs_page[position - 300: position]
		gtfs_html_group = re.match('(.+?)/agency/(.+)/">', substring)

		if gtfs_html_group: 
			return gtfs_html_group.group(2)
		elif debugger:
			print "Failed: No regex match.", operatorName
	elif debugger: 
		print "Failed: No match.", operatorName
	# if nothing is returned (false value) then "Failed." is printed.

# From CSV file from Transitland, looks for a matching name in the html GTFS page. 
# If found, returns the GTFS id name. 
# Example: operatorName = NAME 
# Search for: >NAME< --> and uses regex to find GTFS id name. 
def searchForMatchName(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page, debugger):
	search = ">" + operatorName + "<"
	position = gtfs_page.find(search)

	if position != -1:
		substring = gtfs_page[position - 300: position + 1]
		gtfs_html_group = re.match('(.+?)/agency/(.+)/">', substring)

		if gtfs_html_group: 
			return gtfs_html_group.group(2)
		elif debugger:
			print "Failure 2: Regex matches none.", operatorName
	elif debugger: 
		print "Failure 2: No match.", operatorName
	# if nothing is returned (false) then "Failure." is printed 

# goes through CSV file, makes 1-2 calls to attempt to find a match in GTFS
# HTML document.
def parseFile(gtfs_page, debugger, start_index, end_index):
	SUCCESS_COUNT = 0
	TOTAL_COUNT = 0
	SOURCE_COUNT = 0
	NAME_COUNT = 0
	currentIndex = 0

	# newCSVFolder = open("NameFirstNewFeeds.csv", "w+")
	newCSVDocument = csv.writer(open("CSVNewFeedNames.csv", "w"))

	with open('feeds.csv', 'rU') as f:
		reader = csv.reader(f)

		for row in reader:
			if currentIndex < start_index:
				continue
			if currentIndex > end_index:
				break

			TOTAL_COUNT = TOTAL_COUNT + 1
			if len(row) == 8:
				continue

			else:
				feed_onestop_id = row[0]
				groups = re.match('(.+)\/((.+).zip)', row[1])
				sourceOfFeed = row[1]
				operatorName = row[5]

				if groups:
					sourceOfFeed = groups.group(1)

				match = searchForMatchName(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page, debugger)
				
				if match and match != "Failed.": 
					NAME_COUNT = NAME_COUNT + 1 
				else: 
					match = searchForMatchSource(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page, debugger)
					if match:
						SOURCE_COUNT = SOURCE_COUNT + 1
		
				if match:
					row.append(match)
					newCSVDocument.writerow(row)
					SUCCESS_COUNT = SUCCESS_COUNT + 1 


	print "Source Count ", SOURCE_COUNT
	print "Name Count ", NAME_COUNT
	print "Successful Count: ", SUCCESS_COUNT
	print "Total Count: ", TOTAL_COUNT

def main(): 
	parse = './' + sys.argv[1]
	debugger = sys.argv[2] == 'ON'
	start_index = int(sys.argv[3])
	end_index = int(sys.argv[4])
	
	print start_index
	print end_index
	# open up gtfs HTML and removes all newlines 
	gtfs_page = open(parse, 'r').read().replace('\n', '')
	parseFile(gtfs_page, debugger, 0, 850)


if __name__ == "__main__":
    main()