import sys
import os 
import datetime
import requests
import re
import csv

def findAverageType(listOfDates, qualifier, value, sha1):
	count = 0 
	sumHours = 0

	# use this to debug any given feed 
	debug = '3f8e768f71d4de93cb0fce130e52bca3efbc4601' == sha1
	if debug:
		print sha1

	for date in listOfDates:
		meetsCriteria = int(date[0].month)

		if qualifier == 'week':
			meetsCriteria = date[0].weekday()


		if meetsCriteria == value:
			count = count + 1
			sumHours = sumHours + int(date[1])


	if count == 0:
		return count

	return sumHours/count

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

def convertToDateList(search_text, startDate, sha1): 
	operation_hours_per_day = re.findall("([0-9]{4}-[0-9]{2}-[0-9]{2})\":([0-9]+)", search_text)
	
	# retrieve: 2 properties. 
	listOfDates = []
	for date in operation_hours_per_day: 
		official_date = datetime.datetime.strptime(str(date[0]), '%Y-%m-%d')
		listOfDates.append((official_date, date[1]))

	weeklyHours = findAverageDaysOfWeek(listOfDates, sha1)
	monthlyHours = findAverageMonth(listOfDates, 'blah')

	row = [startDate] + weeklyHours + monthlyHours

	return row

def getScheduledService(sha1, onestop_id, averageFileWriter): 
	# making request here 
	params = (
	    ('feed_version_sha1', sha1),
	)

	r = requests.get('http://transit.land/api/v1/feed_version_infos/', params=params)

	# retrieve start date 
	start_date = re.findall("\"startDate\":\"([0-9]{4}-[0-9]{2}-[0-9]{2})", r.text)
	if not start_date:
		print "No Start Date!", sha1
	# retrieving the scheduled service
	start_position = r.text.find('scheduled_service')

	# create search text 
	truncated_search_text = r.text[start_position:len(r.text)]
	return convertToDateList(truncated_search_text, start_date[0], sha1)

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

	regex_groups = re.findall("{\"sha1\":\"([0-9A-Za-z]+)\"", r.text)
	
	
	averageFileName = "Avgs2-"+onestop_id+".csv"
	averageFileWriter = csv.writer(open(averageFileName, "w"))
	
	first_row = ['sha1', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
	months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	averageFileWriter.writerow(first_row + months)
	array = []
	
	for sha1 in regex_groups:
		array.append(getScheduledService(sha1, onestop_id, averageFileWriter))

	array = sorted(array, key = lambda x: x[0], reverse=False)
	
	# array = cleanArray(array)
	for row in array: 
		print row
		averageFileWriter.writerow(row)

def main(): 
	onestop_id = sys.argv[1]
	makeRequest(onestop_id)



if __name__ == "__main__":
    main()