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
def parseFile(gtfs_page, debugger):
	SUCCESS_COUNT = 0
	TOTAL_COUNT = 0
	SOURCE_COUNT = 0
	NAME_COUNT = 0
	newCSVFolder = open("NewFeeds.csv", "w+")

	with open('feeds.csv', 'rU') as f:
		reader = csv.reader(f)

		for row in reader:
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

				match = searchForMatchSource(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page, debugger)
				
				if match and match != "Failed.": 
					SOURCE_COUNT = SOURCE_COUNT + 1 
				else: 
					match = searchForMatchName(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page, debugger)
					if match:
						NAME_COUNT = NAME_COUNT + 1
		
				if match:
					row.append(match)
					newCSVFolder.write(row[0] + "," + row[1] + "," + row[2] + "," + row[3] + 
						"," + row[4] + "," + row[5] + "," + row[6] + "," + row[7] + "\n")
					SUCCESS_COUNT = SUCCESS_COUNT + 1 


	print "Source Count ", SOURCE_COUNT
	print "Name Count ", NAME_COUNT
	print "Successful Count: ", SUCCESS_COUNT
	print "Total Count: ", TOTAL_COUNT

def main(): 
	parse = './' + sys.argv[1]
	debugger = sys.argv[2] == 'ON'
	# open up gtfs HTML and removes all newlines 
	gtfs_page = open(parse, 'r').read().replace('\n', '')
	parseFile(gtfs_page, debugger)


if __name__ == "__main__":
    main()