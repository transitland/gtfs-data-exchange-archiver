import sys
import requests
import json
import datetime
import re
import csv

## threshold for detecting a tail
THRESHOLD = 0.15

# utility methods
def writeToCSV (filename, status, header=None):
	if not status:
		return
	header = header or status[0].keys()
	with open(filename, 'w') as f:
		writer = csv.DictWriter(f, fieldnames=header)
		writer.writeheader()
		for elem in status:
			writer.writerow(elem)

# convert an dictionary of strings to a dictionary of datetime objects
def toDateTime(value):
	return datetime.datetime.strptime(str(value)[:10], '%Y-%m-%d')

def convertToDateTime(scheduled_service):
	updatedScheduledService = {}
	for date in scheduled_service:
		official_date = toDateTime(str(date))
		updatedScheduledService[official_date] = scheduled_service[date]
	return updatedScheduledService

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

# find average service hours
def findAverageServiceHours(updatedScheduledService):
	averageHours = 0
	dateCount = len(updatedScheduledService)
	for date in updatedScheduledService:
		averageHours = averageHours + updatedScheduledService[date]
	return float(averageHours)/dateCount


############################

# find and interpret schedule by
# determining correct start and end dates
# converting to datetime objects
def interpretSchedule(feedVersion, feedVersionInfo):
	print "\ninterpret: %s"%feedVersion['sha1']
	if 'data' in feedVersionInfo and 'error' in feedVersionInfo['data']:
		print "\tfeed_version_info error, skipping: %s"%feedVersionInfo['id']
		return

	sha1 = feedVersion['sha1']
	id_ = feedVersionInfo['id']

	scheduled_service = feedVersionInfo['data']['scheduled_service']
	updatedScheduledService = convertToDateTime(scheduled_service)

	averageServiceHours = findAverageServiceHours(updatedScheduledService)
	print "\taverageServiceHours: %s"%averageServiceHours

	start, end = findStartAndEndDates(updatedScheduledService)
	print "\tstart %s"%start
	print "\tend %s"%end

	updatedStart = cleanTails(updatedScheduledService, False)
	if updatedStart != start:
		print "\tstart %s updatedStart %s"%(start, updatedStart)

	updatedEnd = cleanTails(updatedScheduledService, True)
	if updatedEnd != end:
		print "\tend %s updatedEnd %s"%(end, updatedEnd)

	fetchedAt = toDateTime(feedVersion['fetched_at'])
	if (fetchedAt - updatedStart).days > 7:
		print "\tset updatedStart %s to fetchedAt %s"%(updatedStart, fetchedAt)
		updatedStart = fetchedAt

	# if (updatedStart == start and updatedEnd == end):
	# 	updatedStart = None
	# 	updatedEnd = None
	rowInfo = {
		"id": id_,
		"fetchedAt": fetchedAt,
		"currentSha1": sha1,
		"originalStart": start,
		"originalEnd": end,
		"updatedStart": updatedStart,
		"updatedEnd": updatedEnd
	}
	return rowInfo

# find overlaps and gaps in feed versions
def findOverlap (interpretedSchedule):
	interpretedSchedule = sorted(interpretedSchedule, key = lambda x: (x['fetchedAt']))
	status = []
	for current,next_ in zip(interpretedSchedule[:-1], interpretedSchedule[1:]):
		print "\n\n"
		print "current:"
		print current
		print "next:"
		print next_

		overlapDays = (current['updatedEnd'] - next_['updatedStart']).days
		totalTime = (next_['updatedEnd'] - current['updatedStart']).days
		overlapPercent = float(overlapDays) / float(totalTime)

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
		print "overlapObject:"
		print overlapObject
		status.append(overlapObject)
	return status

# get feedversion with scheduled stops, and find overlap and gap averages for each feed
def getFeedService (onestop_id):
	params = {
		'feed_onestop_id': onestop_id,
		'type': 'FeedVersionInfoStatistics',
		'per_page': 'false'
	}
	feedVersionInfos = requests.get('https://transit.land/api/v1/feed_version_infos/', params=params).json().get('feed_version_infos', [])
	interpretedSchedules = []
	data = []
	for feedVersionInfo in feedVersionInfos:
		sha1 = feedVersionInfo['feed_version_sha1']
		print sha1
		feedVersion = requests.get('https://transit.land/api/v1/feed_versions/%s'%sha1).json()
		if feedVersion is None:
			print "no feed_version"
			continue
		if feedVersion.get('tags') and feedVersion['tags'].get('gtfs_data_exchange'):
			print "gtfs_data_exchange feed; skipping"
			continue
		if feedVersion and feedVersionInfo:
			data.append((feedVersion, feedVersionInfo))
	return data

# call function with onestop_id as parameter
def main():
	params = {'per_page': 'false', 'bbox': '-123.321533,36.826875,-120.786438,38.629745'}
	# params = {'onestop_id': 'f-9q9-caltrain'}
	feeds = requests.get('https://transit.land/api/v1/feeds', params=params).json()['feeds']
	results = []
	for feed in feeds:
		print "===== %s ====="%feed['onestop_id']
		onestop_id = feed['onestop_id']
		data = getFeedService(onestop_id)
		data = sorted(data, key=lambda a: a[0]['fetched_at'])
		interpretedSchedules = [interpretSchedule(a,b) for a,b in data]
		overlaps = findOverlap(interpretedSchedules)
		overlapPctAverage = sum(i['overlapPercent'] for i in overlaps) / float(len(overlaps))
		fetchedDifferenceAverage = sum(i['fetchedDifference'] for i in overlaps) / float(len(overlaps))

		print "FINAL RESULT:"
		print "overlapPctAverage", overlapPctAverage
		print "fetchedDifferenceAverage", fetchedDifferenceAverage
		results.append({'onestop_id':onestop_id, 'overlapPctAverage':overlapPctAverage, 'fetchedDifferenceAverage':fetchedDifferenceAverage})

	writeToCSV('results.csv', results)



if __name__ == "__main__":
    main()
