import sys
import os 
import datetime
import requests
import re
import csv
import json

def findAverageType(listOfDates, qualifier, value, sha1):
	count = 0 
	sumHours = 0


	for date in listOfDates:
		meetsCriteria = int(date[0].month)

		if qualifier == 'week':
			meetsCriteria = date[0].weekday()


		if meetsCriteria == value:
			count = count + 1
			sumHours = sumHours + int(date[1])

	if count == 0:
		return count

	return float(sumHours)/count

# will return an array representing days of week, sha1
def findAverageDaysOfWeek(listOfDates, sha1): 
	dayOfWeekArray = []
	for dayOfWeek in xrange(0, 7):
		average = findAverageType(listOfDates, 'week', dayOfWeek, sha1)
		dayOfWeekArray.append(average)
	
	return dayOfWeekArray

def findAverageMonth(listOfDates, sha1): 
	monthArray = []
	for eachMonth in xrange(1, 13):
		average = findAverageType(listOfDates, 'month', eachMonth, sha1)
		monthArray.append(average)

	return monthArray 

def convertToDateList(searchJSON, startDate, sha1): 
	scheduledService = searchJSON['data']['scheduled_service']

	# retrieve: 2 properties. 
	listOfDates = []
	for date in scheduledService: 
		officialDate = datetime.datetime.strptime(str(date), '%Y-%m-%d')
		listOfDates.append((officialDate, scheduledService[date]))

	weeklyHours = findAverageDaysOfWeek(listOfDates, sha1)
	monthlyHours = findAverageMonth(listOfDates, 'month')

	row = [startDate] + weeklyHours + monthlyHours

	return row

def getScheduledService(sha1, onestop_id, averageFileWriter): 
	# making request here 
	params = (
	    ('feed_version_sha1', sha1),
	)
	print sha1

	r = requests.get('http://transit.land/api/v1/feed_version_infos/', params=params)
	rJSON = json.loads(r.text)

	sortJSON = sorted(rJSON['feed_version_infos'], key = lambda x: x['type'], reverse=False)
	
	print sortJSON[0]['data']
	if (sortJSON[0] and sortJSON[0]['data'] and sortJSON[0]['data']['feedStatistics']):
		startDate = sortJSON[0]['data']['feedStatistics']['startDate']

	else:
		print "Unsuccessful."
		print sortJSON[0]['data']

	return convertToDateList(sortJSON[1], startDate, sha1)

	

# optional, only saves arrays with changes
def cleanArray(array):
	prevRow = array[1]
	newArray = []

	for i, row in enumerate(array): 
		if i == 0 or i == 1:
			newArray.append(prevRow)
			continue

		if array[i] != prevRow:
			prevRow = array[i]
			newArray.append(array[i])
			continue

	return newArray
		
def makeRequest(onestop_id): 
	params = (
    	('feed_onestop_id', onestop_id),
	)

	r = requests.get('https://transit.land/api/v1/feed_versions', params=params)
	rJSON = json.loads(r.text)
	
	averageFileName = "Avgs3-"+onestop_id+".csv"
	averageFileWriter = csv.writer(open(averageFileName, "w"))
	
	first_row = ['sha1', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	averageFileWriter.writerow(first_row + months)
	array = []
	
	print "Testing here for RJSON"
	print rJSON['feed_versions']
	for element in rJSON['feed_versions']:
		array.append(getScheduledService(element['sha1'], onestop_id, averageFileWriter))


	array = sorted(array, key = lambda x: x[0], reverse=False)
	
	# array = cleanArray(array)
	for row in array: 
		averageFileWriter.writerow(row)

def main(): 
	onestop_id = sys.argv[1]
	makeRequest(onestop_id)



if __name__ == "__main__":
    main()