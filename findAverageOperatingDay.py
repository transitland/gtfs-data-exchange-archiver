import requests 
import os 
import sys
import json
import re
import datetime
import csv

weekdayDictionary = {
	'0': [0, 0], '1': [0, 0], '2': [0, 0], '3': [0, 0], '4': [0, 0], '5': [0, 0], '6': [0, 0]
}

monthDictionary = {
	'12': [0, 0], '1': [0, 0], '2': [0, 0], '3': [0, 0], '4': [0, 0], '5': [0, 0],
	'6': [0, 0],'7': [0, 0], '8': [0, 0], '9': [0, 0], '10': [0, 0], '11': [0, 0]
}

def updateWeeklyDictionary(weekDay, date, operatingHours, weekdayDictionary):
	weekdayDictionary[weekDay][0] = weekdayDictionary[weekDay][0] + int(operatingHours)
	weekdayDictionary[weekDay][1] = weekdayDictionary[weekDay][1] + 1
	# if (weekDay == '6'):
	# 	print weekdayDictionary[weekDay]
	# 	print operatingHours
	return weekdayDictionary
	
def updateMonthlyDictionary(month, date, operatingHours, monthDictionary): 
	monthDictionary[month][0] = monthDictionary[month][0] + int(operatingHours)
	monthDictionary[month][1] = monthDictionary[month][1] + 1
	return monthDictionary

def findAverages(weekdayDictionary, monthDictionary):
	weekdayAverages = {} 
	for thisDay in weekdayDictionary:
		day = weekdayDictionary[thisDay]
		weekdayAverages[thisDay] = day[0]/day[1]

	monthAverages = {}
	for thisMonth in monthDictionary:
		month = monthDictionary[thisMonth]
		if month[1] == 0:
			print "Month", month
			continue
		monthAverages[thisMonth] = month[0]/month[1]

	return weekdayAverages, monthAverages

def writeFile (sha1, weekdayAverages, monthAverages, averageFileWriter): 
	row = [sha1]
	for weekday in xrange(0, 7): 
		row.append(weekdayAverages[str(weekday)])

	
	print row
	averageFileWriter.writerow(row)

def updateInformation(sha1, operation_hours_per_day, averageFileWriter):
	weekdayDictionary = {
		'0': [0, 0], '1': [0, 0], '2': [0, 0], '3': [0, 0], '4': [0, 0], '5': [0, 0], '6': [0, 0]
	}

	monthDictionary = {
		'12': [0, 0], '1': [0, 0], '2': [0, 0], '3': [0, 0], '4': [0, 0], '5': [0, 0],
		'6': [0, 0],'7': [0, 0], '8': [0, 0], '9': [0, 0], '10': [0, 0], '11': [0, 0]
	}

	for date in operation_hours_per_day:
		official_date = datetime.datetime.strptime(str(date[0]), '%Y-%m-%d')
		weekdayDictionary = updateWeeklyDictionary(str(official_date.weekday()), official_date, int(date[1]), weekdayDictionary)
		monthDictionary = updateMonthlyDictionary(str(official_date.month), official_date, int(date[1]), monthDictionary)

	weekdayAverages, monthAverages = findAverages(weekdayDictionary, monthDictionary)
	return weekdayAverages, monthAverages

	

def getScheduledService(sha1, onestop_id, averageFileWriter): 
	params = (
	    ('feed_version_sha1', sha1),
	    ('type', 'FeedVersionInfoStatistics'),
	)

	r = requests.get('http://transit.land/api/v1/feed_version_infos/', params=params)
	start_position = r.text.find('scheduled_service')
	end_position = r.text.find('feed_version_sha1')
	
	truncated_search_text = r.text[start_position:end_position]
	operation_hours_per_day = re.findall("([0-9]{4}-[0-9]{2}-[0-9]{2})\":([0-9]+)", truncated_search_text)
	weekdayAverages, monthAverages = updateInformation(sha1, operation_hours_per_day, averageFileWriter)
	writeFile(sha1, weekdayAverages, monthAverages, averageFileWriter)


	

def makeRequest(onestop_id): 
	params = (
    	('feed_onestop_id', onestop_id),
	)

	r = requests.get('https://transit.land/api/v1/feed_versions', params=params)

	regex_groups = re.findall("{\"sha1\":\"([0-9A-Za-z]+)\"", r.text)
	averageFileName = "Averages-"+onestop_id+".csv"
	averageFileWriter = csv.writer(open(averageFileName, "w"))
	first_row = ['sha1', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	
	averageFileWriter.writerow(first_row)
	for sha1 in regex_groups:
		getScheduledService(sha1, onestop_id, averageFileWriter)

def main(): 
	onestop_id = sys.argv[1]
	makeRequest(onestop_id)



if __name__ == "__main__":
    main()