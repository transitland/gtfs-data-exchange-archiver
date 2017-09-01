import sys
import os 
import datetime
import requests
import re
import csv
import json

## threshold for detecting a tail
THRESHOLD = 0.15

def findAverageType(listOfDates, qualifier, value, sha1):
	count = 0 
	sumHours = 0

	for date in listOfDates.keys():
		meetsCriteria = int(date.month)

		if qualifier == 'week':
			meetsCriteria = date.weekday()


		if meetsCriteria == value:
			count = count + 1
			sumHours = sumHours + int(listOfDates[date])

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

# remove tail end
def cleanTails(updatedScheduledService, end):
	# TODO: Swap out names here ... to updatedScheduledService
	listOfDates = updatedScheduledService

	averageServiceHours = findAverageServiceHours(updatedScheduledService)
	listOfDates = sorted(updatedScheduledService.keys())

	if end:
		listOfDates.reverse()

	tailDate = listOfDates[0]
	tailValue = 0

	# updatd start may not reflect actual start, could also be end.
	updatedStart = tailDate

	for i, date in enumerate(listOfDates):
		tailValue = updatedScheduledService[date]
		if tailValue < THRESHOLD * averageServiceHours:
			del listOfDates[i]
		else:
			updatedStart = date
			break

	return updatedStart

# convert an dictionary of strings to a dictionary of datetime objects
def convertToDateTime(scheduled_service):
	updatedScheduledService = {}
	for date in scheduled_service:
		official_date = datetime.datetime.strptime(str(date), '%Y-%m-%d')
		updatedScheduledService[official_date] = scheduled_service[date]

	return updatedScheduledService

# find average service hours
def findAverageServiceHours(updatedScheduledService):
	averageHours = 0
	dateCount = len(updatedScheduledService)

	for date in updatedScheduledService:
		averageHours = averageHours + updatedScheduledService[date]

	return float(averageHours)/dateCount

def findStartAndEndDates(updatedScheduledService):
	startDate = datetime.datetime.max
	endDate = datetime.datetime.min

	for date in updatedScheduledService:
		if date > endDate:
			endDate = date
		if date < startDate:
			startDate = date

	return startDate, endDate

def interpretSchedule(scheduled_service, sha1): 
	updatedScheduledService = convertToDateTime(scheduled_service)
	averageServiceHours = findAverageServiceHours(updatedScheduledService)
	start, end = findStartAndEndDates(updatedScheduledService)

	updatedStart = cleanTails(updatedScheduledService, False)
	updatedEnd = cleanTails(updatedScheduledService, True)

	weeklyHours = findAverageDaysOfWeek(updatedScheduledService, sha1)
	# monthlyHours = findAverageMonth(updatedScheduledService, sha1)

	row = [updatedEnd.date()]  + [updatedStart.date()] + weeklyHours

	return row 



# searches through a JSON element, and returns the item in the dictionary that matches this.
def retrieveElementInList (searchKey, searchValue, searchList): 
	for dictionary in searchList: 
		if dictionary[searchKey] == searchValue:
			return dictionary

	return None

# get the scheduled service of a specific feed version 
def getScheduledService(sha1, onestop_id, averageFileWriter): 
	# making request here 
	params = (
	    ('feed_version_sha1', sha1),
	)

	r = requests.get('http://transit.land/api/v1/feed_version_infos/', params=params)
	if r:
		rJSON = json.loads(r.text)

		sortJSON = retrieveElementInList('type', 'FeedVersionInfoStatistics', rJSON['feed_version_infos'])

		if sortJSON['data'].get('error'):
			print sortJSON['data'].get('error')
		else: 
			return interpretSchedule(sortJSON['data']['scheduled_service'], sha1)

	

# optional, only saves array rows with changes because some data is the exact same information. 
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
	
# make request to retrieve all sha1s for each feed version for a onestop_id 
# opens up CSV document to write all this information
def makeRequest(onestop_id): 
	params = (
    	('feed_onestop_id', onestop_id),
	)

	r = requests.get('https://transit.land/api/v1/feed_versions', params=params)
	rJSON = json.loads(r.text)
	
	averageFileName = "Avgs-"+onestop_id+".csv"
	averageFileWriter = csv.writer(open(averageFileName, "w"))
	
	# start date is put second so you can easily make CSV graphs
	first_row = ['End Date', 'Start Date', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

	averageFileWriter.writerow(first_row)
	array = []

	for element in rJSON['feed_versions']:
		print element['sha1']
		appendedElement = getScheduledService(element['sha1'], onestop_id, averageFileWriter)
		if appendedElement:
			array.append(appendedElement)


	array = sorted(array, key = lambda x: (x[1], x[0]), reverse=False)
	array = cleanArray(array)

	for row in array: 
		averageFileWriter.writerow(row)

def main(): 
	onestop_id = sys.argv[1]
	makeRequest(onestop_id)



if __name__ == "__main__":
    main()