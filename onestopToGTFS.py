import os 
import csv
import re
import sys

def searchForMatchSource(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page):
	position = gtfs_page.find(sourceOfFeed)

	if position != -1: 
		substring = gtfs_page[position - 300: position]
		gtfs_html_group = re.match('(.+?)/agency/(.+)/">', substring)

		if gtfs_html_group: 
			return gtfs_html_group.group(2)
		else:
			return "Failed."
	else: 
		return "Failed."

def searchForMatchName(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page):
	search = ">" + operatorName + "<"
	position = gtfs_page.find(search)

	if position != -1:
		substring = gtfs_page[position - 300: position + 1]
		gtfs_html_group = re.match('(.+?)/agency/(.+)/">', substring)

		if gtfs_html_group: 
			return gtfs_html_group.group(2)
		else:
			print "Failure, Round 2."

def parseFile(gtfs_page):
	count = 0
	total_count = 0
	source_count = 0
	name_count = 0

	with open('feeds.csv', 'rU') as f:
		reader = csv.reader(f)
		for row in reader:
			if len(row) == 8:
				total_count = total_count + 1
				continue
			else:
				feed_onestop_id = row[0]
				groups = re.match('(.+)\/((.+).zip)', row[1])
				sourceOfFeed = ''
				operatorName = row[5]

				if groups:
					sourceOfFeed = groups.group(1)
				else:
					sourceOfFeed = row[1]

				match = searchForMatchSource(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page)
				
				if match and match != "Failed.": 
					source_count = source_count + 1
					# print "Source Match: ", operatorName
					# print "SRC: ", match
					

				total_count = total_count + 1

				if match == "Failed.":
					match = searchForMatchName(feed_onestop_id, operatorName, sourceOfFeed, gtfs_page)
					if match:
						name_count = name_count + 1

				if match:
					row.append(match)
					count = count + 1

	print "Source Count ", source_count
	print "name_count ", name_count
	print "Successful Count: ", count
	print "Total Count: ", total_count

def main(): 
	parse = './' + sys.argv[1]
	print parse
	gtfs_page = open(parse, 'r').read().replace('\n', '')
	parseFile(gtfs_page)


if __name__ == "__main__":
    main()