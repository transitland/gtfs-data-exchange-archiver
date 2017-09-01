import time
import sys
import requests
import json
import datetime
import re
import csv

## threshold for detecting a tail
THRESHOLD = 0.15
APIKEY = sys.argv[1]

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
		official_date = toDateTime(date)
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
def interpretSchedule(feedVersion, element):
	if 'data' in element and not 'error' in element['data']:
		sha1 = element['feed_version_sha1']
		print "interpret:", sha1

		scheduled_service = element['data']['scheduled_service']

		updatedScheduledService = convertToDateTime(scheduled_service)
		averageServiceHours = findAverageServiceHours(updatedScheduledService)
		start, end = findStartAndEndDates(updatedScheduledService)

		updatedStart = cleanTails(updatedScheduledService, False)
		updatedEnd = cleanTails(updatedScheduledService, True)

		if not feedVersion.get('fetched_at'):
			print "\tno fetched_at, skipping"
			return
		fetchedAt = toDateTime(feedVersion['fetched_at'][:10])
		if (fetchedAt - updatedStart).days > 30:
			print "\tset updatedStart %s to fetchedAt %s"%(updatedStart, fetchedAt)
			updatedStart = fetchedAt

		print "\tfetchedAt:", fetchedAt
		print "\toriginalStart:", start
		print "\tupdatedStart:", updatedStart
		print "\tstart shift:", (updatedStart - start).days
		print "\toriginalEnd:", end
		print "\tupdatedEnd:", updatedEnd
		print "\tend shift:", (updatedEnd - end).days
		print "\toriginal duration:", (end - start).days
		print "\tupdated duration:", (updatedEnd - updatedStart).days

		rowInfo = {
			"currentSha1": sha1,
			"originalStart": start,
			"originalEnd": end,
			"updatedStart": updatedStart,
			"updatedEnd": updatedEnd,
			"fetchedAt": fetchedAt
		}

		if (sha1, updatedStart, updatedEnd):
			return rowInfo


def toDateTime(value):
	return datetime.datetime.strptime(str(value), '%Y-%m-%d')

def writeToCSV (filename, status, header=None):
	header = header or status[0].keys()
	with open(filename, 'w') as f:
		writer = csv.DictWriter(f, fieldnames=header)
		writer.writeheader()
		for elem in status:
			writer.writerow(elem)

# find overlaps and gaps in feed versions
def findOverlap2(interpretedSchedule):
	interpretedSchedule = sorted(interpretedSchedule, key = lambda x: (x['fetchedAt']))
	status = []
	for current,next_ in zip(interpretedSchedule[:-1], interpretedSchedule[1:]):
		print "compare %s -> %s"%(current['currentSha1'], next_['currentSha1'])
		print "\tcurrent:"
		print current
		print "\tnext:"
		print next_

		overlapDays = (current['updatedEnd'] - next_['updatedStart']).days
		totalTime = (next_['updatedEnd'] - current['updatedStart']).days
		overlapPercent = float(overlapDays) / float(totalTime)
		print "\toverlapDays:", overlapDays
		print "\ttotalTime:", totalTime
		print "\toverlapPercent:", overlapPercent

		overlapObject = {
			"currentSha1": current['currentSha1'],
			"nextSha1": next_['currentSha1'],
			"originalStart": current['originalStart'].strftime('%Y-%m-%d'),
			"originalEnd": current['originalEnd'].strftime('%Y-%m-%d'),
			"updatedStart": current['updatedStart'].strftime('%Y-%m-%d'),
			"updatedEnd": current['updatedEnd'].strftime('%Y-%m-%d'),
			"overlap": overlapDays,
			"startDifference": (next_['updatedStart'] - current['updatedStart']).days,
			"fetchedDifference": (next_['fetchedAt'] - current['fetchedAt']).days,
			"overlapPercent": overlapPercent,
		}
		status.append(overlapObject)

	return status

def findOverlap (interpretedSchedule):

	interpretedSchedule = sorted(interpretedSchedule, key = lambda x: (x['fetchedAt']))

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
def getFeedVersions (onestop_id):
	print "===== %s ====="%(onestop_id)
	params = (
	    ('feed_onestop_id', onestop_id),
	    ('type', 'FeedVersionInfoStatistics'),
		('per_page', 'false'),
		('apikey', APIKEY)
	)

	time.sleep(0.125)
	feedVersionInfos = requests.get('https://transit.land/api/v1/feed_version_infos/', params=params).json()['feed_version_infos']

	data = []
	for feedVersionInfo in feedVersionInfos:
		sha1 = feedVersionInfo['feed_version_sha1']
		print "sha1:", sha1
		params = {'apikey': APIKEY}

		time.sleep(0.125)
		feedVersion = requests.get('https://transit.land/api/v1/feed_versions/%s'%sha1, params=params).json()
		if feedVersion is None:
			print "\tno feed_version"
			continue
		if feedVersionInfo is None:
			print "\tno feed_version_info"
			continue
		if feedVersion.get('tags') and feedVersion['tags'].get('gtfs_data_exchange'):
			print "\tgtfs_data_exchange feed; skipping"
			continue
		data.append([feedVersion, feedVersionInfo])

	return data

def processFeed(onestop_id):
	# Get feed_versions and feed_version_infos
	fvs = getFeedVersions(onestop_id)

	# Interpret and adjust the schedules
	interpretedSchedules = []
	for feedVersion, feedVersionInfo in fvs:
		schedule = interpretSchedule(feedVersion, feedVersionInfo)
		if schedule:
			interpretedSchedules.append(schedule)
		else:
			print "\terror processing schedule; skipping"
			continue

	# Calculate overlap statistics
	overlaps = findOverlap2(interpretedSchedules)
	overlapPercentAverage = sum(i['overlapPercent'] for i in overlaps) / float(len(overlaps))
	fetchedAtDifferenceAverage = sum(i['fetchedDifference'] for i in overlaps) / float(len(overlaps))

	return {
		'onestop_id': onestop_id,
		'overlapPercentAverage': overlapPercentAverage,
		'fetchedAtDifferenceAverage': fetchedAtDifferenceAverage
	}
	# status, overlapAverage, gapAverage, startDifferenceAverage = findOverlap(interpretedSchedule)
	#
	# header = ['ID', 'currentSha1', 'nextSha1', 'originalStart', 'originalEnd', 'updatedStart', 'updatedEnd', 'overlapStart',
	# 'overlapEnd', 'overlapDifference', 'gapStart', 'gapEnd', 'gapDifference', 'startDifference']
	# writeToCSV("%s.csv"%onestop_id, status, header=header)
	# with open('%s.json'%onestop_id, 'w') as f:
	# 	f.write(json.dumps(status, default=lambda x:str(x)))
	#
	# averageOneStopInformation = {
	# 	'onestop_id': onestop_id,
	# 	'overlapAverage': overlapAverage,
	# 	'gapAverage': gapAverage,
	# 	'startDifferenceAverage': startDifferenceAverage
	# }
	#
	# print overlapAverage
	# print gapAverage
	# print startDifferenceAverage
	# return averageOneStopInformation


# call function with onestop_id as parameter
def main():
	params = {
		'per_page': 1,
		'bbox': '-123.321533,36.826875,-120.786438,38.629745',
		'apikey': APIKEY
	}
	time.sleep(0.125)
	feeds = requests.get('https://transit.land/api/v1/feeds', params=params).json()['feeds']
	allFeedsInformation = []
	for feed in feeds:
		allFeedsInformation.append(processFeed(feed['onestop_id']))
	filename = 'allFeeds4.csv'
	writeToCSV(filename, allFeedsInformation)


if __name__ == "__main__":
    main()
