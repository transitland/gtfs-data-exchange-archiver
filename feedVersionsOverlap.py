import sys
import requests
import json
import datetime
import re
import csv

## threshold for detecting a tail
THRESHOLD = 0.15

# remove tail end
def cleanTails(updatedScheduledService, end):
	averageServiceHours = findAverageServiceHours(updatedScheduledService)
	listOfDates = sorted(updatedScheduledService.keys())

	if end:
		listOfDates.reverse()

	tailDate = listOfDates[0]
	tailValue = 0

	# updatd start may not reflect actual start, could also be end.
	updatedStart = tailDate

	for date in listOfDates:
		tailValue = updatedScheduledService[date]
		if tailValue < THRESHOLD * averageServiceHours:
			continue
		else:
			updatedStart = date
			break

	return updatedStart


# we can also get this from earliest start date amd end date, use this to cross-check.
# retrieve start and end dates
def findStartAndEndDates(updatedScheduledService):
	startDate = datetime.datetime.max
	endDate = datetime.datetime.min

	for date in updatedScheduledService:
		if date > endDate:
			endDate = date
		if date < startDate:
			startDate = date

	return startDate, endDate

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

# find and interpret schedule by
# determining correct start and end dates
# converting to datetime objects
def interpretSchedule(element):
	if 'data' in element and not 'error' in element['data']:
		sha1 = element['feed_version_sha1']
		identification = element['id']

		scheduled_service = element['data']['scheduled_service']

		updatedScheduledService = convertToDateTime(scheduled_service)
		averageServiceHours = findAverageServiceHours(updatedScheduledService)
		start, end = findStartAndEndDates(updatedScheduledService)

		updatedStart = cleanTails(updatedScheduledService, False)
		updatedEnd = cleanTails(updatedScheduledService, True)

		# if (updatedStart == start and updatedEnd == end):
		# 	updatedStart = None
		# 	updatedEnd = None

		rowInfo = {
			"ID": identification,
			"currentSha1": sha1,
			"originalStart": start,
			"originalEnd": end,
			"updatedStart": updatedStart,
			"updatedEnd": updatedEnd,
		}

		if (sha1, id, updatedStart, updatedEnd):
			return rowInfo

def writeToCSV (filename, status):

	headerRow = ['ID', 'currentSha1', 'nextSha1', 'originalStart', 'originalEnd', 'updatedStart', 'updatedEnd', 'overlapStart',
	'overlapEnd', 'overlapDifference', 'gapStart', 'gapEnd', 'gapDifference', 'startDifference']
	with open(filename, 'w') as f:
		writer = csv.DictWriter(f, fieldnames=headerRow)
		writer.writeheader()
		for elem in status:
			writer.writerow(elem)


# find overlaps and gaps in feed versions
def findOverlap (interpretedSchedule):

	interpretedSchedule = sorted(interpretedSchedule, key = lambda x: (x['updatedStart'], x['updatedEnd']))

	currentIndex = 0
	nextIndex = 1

	status = []
	overlapValues = [0, 0]
	gapValues = [0, 0]

	# while True:
	# 	current = interpretedSchedule[currentIndex]
	# 	next = interpretedSchedule[nextIndex]
	for current,next in zip(interpretedSchedule[:-1], interpretedSchedule[1:]):
		start = next['updatedStart']
		end = current['updatedEnd']

		difference = abs((end - start).days)

		if currentIndex == nextIndex:
			nextIndex = nextIndex + 1

		elif end > start:

			# status.append("Overlap: " + str(difference) + " " + str(start) + " and " + str(end))

			overlapObject = {
				"ID": current['ID'],
				"currentSha1": current['currentSha1'],
				"nextSha1": next['currentSha1'],
				"originalStart": current['originalStart'].strftime('%Y-%m-%d'),
				"originalEnd": current['originalEnd'].strftime('%Y-%m-%d'),
				"updatedStart": current['updatedStart'].strftime('%Y-%m-%d'),
				"updatedEnd": current['updatedEnd'].strftime('%Y-%m-%d'),
				"overlapStart": end.strftime('%Y-%m-%d'),
				"overlapEnd": start.strftime('%Y-%m-%d'),
				"overlapDifference": difference,
				"gapStart": '',
				"gapEnd": '',
				"gapDifference":'',
				"startDifference": (next['updatedStart'] - current['updatedStart']).days
			}

			status.append(overlapObject)

			overlapValues[0] += difference
			overlapValues[1] += 1

			nextIndex = nextIndex + 1

		elif start > end:
			# status.append("Gap: " + str(difference) + " " + str(start) + " and " + str(end))

			gapObject = {
				"ID": current['ID'],
				"currentSha1": current['currentSha1'],
				"nextSha1": next['currentSha1'],
				"originalStart": current['originalStart'].strftime('%Y-%m-%d'),
				"originalEnd": current['originalEnd'].strftime('%Y-%m-%d'),
				"updatedStart": current['updatedStart'].strftime('%Y-%m-%d'),
				"updatedEnd": current['updatedEnd'].strftime('%Y-%m-%d'),
				"gapStart": end.strftime('%Y-%m-%d'),
				"gapEnd": start.strftime('%Y-%m-%d'),
				"gapDifference": difference,
				'overlapStart': '',
				'overlapEnd': '',
				'overlapDifference': '',
				"startDifference": (next['updatedStart'] - current['updatedStart']).days
			}

			status.append(gapObject)

			currentIndex = currentIndex + 1

			gapValues[0] += difference
			gapValues[1] += 1

		if nextIndex >= len(interpretedSchedule) - 1:
			currentIndex = currentIndex + 1
			nextIndex = currentIndex + 1

		if currentIndex >= len(interpretedSchedule) - 1:
			pass # break

	overlapAverage = 0
	gapAverage = 0
	startDifferenceAverage = sum(i['startDifference'] for i in status) / float(len(status)-1)

	if overlapValues[1]:
		overlapAverage = float(overlapValues[0])/overlapValues[1]
	if gapValues[1]:
		gapAverage = float(gapValues[0])/gapValues[1]

	return status, overlapAverage, gapAverage, startDifferenceAverage

# get feedversion with scheduled stops, and find overlap and gap averages for each feed
def getFeedService (onestop_id):
	params = (
	    ('feed_onestop_id', onestop_id),
	    ('type', 'FeedVersionInfoStatistics'),
		('per_page', 'false')
	)

	reqService = requests.get('https://transit.land/api/v1/feed_version_infos/', params=params)
	serviceJS = json.loads(reqService.text)

	interpretedSchedule = []

	for element in serviceJS['feed_version_infos']:
		schedule = interpretSchedule(element)

		if schedule:
			interpretedSchedule.append(schedule)

	status, overlapAverage, gapAverage, startDifferenceAverage = findOverlap(interpretedSchedule)
	writeToCSV("%s.csv"%onestop_id, status)
	with open('%s.json'%onestop_id, 'w') as f:
		f.write(json.dumps(status, default=lambda x:str(x)))

	averageOneStopInformation = {
		'onestop_id': onestop_id,
		'overlapAverage': overlapAverage,
		'gapAverage': gapAverage,
		'startDifferenceAverage': startDifferenceAverage
	}

	print overlapAverage
	print gapAverage
	print startDifferenceAverage

	return averageOneStopInformation



# call function with onestop_id as parameter
def main():
	per_page = int(sys.argv[1])
	feeds = requests.get('https://transit.land/api/v1/feeds', params={'per_page': per_page}).json()['feeds']
	allFeedsInformation = []
	for feed in feeds:
		print feed['onestop_id']
		allFeedsInformation.append(getFeedService(feed['onestop_id']))

	filename = 'allFeeds4.csv'
	headerRow = ['onestop_id', 'overlapAverage', 'gapAverage', 'startDifferenceAverage']

	with open(filename, 'w') as f:
		writer = csv.DictWriter(f, fieldnames=headerRow)
		writer.writeheader()
		for elem in allFeedsInformation:
			writer.writerow(elem)

	


if __name__ == "__main__":
    main()