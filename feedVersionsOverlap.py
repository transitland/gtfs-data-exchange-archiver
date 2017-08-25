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


############################

# find and interpret schedule by
# determining correct start and end dates
# converting to datetime objects
def interpretSchedule(feedVersion, element):
	if 'data' in element and not 'error' in element['data']:
		sha1 = element['feed_version_sha1']
		id_ = element['id']

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
			"id": id_,
			"currentSha1": sha1,
			"originalStart": start,
			"originalEnd": end,
			"updatedStart": updatedStart,
			"updatedEnd": updatedEnd,
		}

		if (sha1, id_, updatedStart, updatedEnd):
			return rowInfo

def writeToCSV (filename, status, header=None):
	if not status:
		return
	header = header or status[0].keys()
	with open(filename, 'w') as f:
		writer = csv.DictWriter(f, fieldnames=header)
		writer.writeheader()
		for elem in status:
			writer.writerow(elem)

# find overlaps and gaps in feed versions
def findOverlap (interpretedSchedule):
	interpretedSchedule = sorted(interpretedSchedule, key = lambda x: (x['updatedStart'], x['updatedEnd']))

	status = []
	for current,next_ in zip(interpretedSchedule[:-1], interpretedSchedule[1:]):
		start = next_['updatedStart']
		end = current['updatedEnd']
		overlap = (end - start).days
		# status.append("Overlap: " + str(difference) + " " + str(start) + " and " + str(end))
		overlapObject = {
			"id": current['id'],
			"currentSha1": current['currentSha1'],
			"nextSha1": next_['currentSha1'],
			"originalStart": current['originalStart'].strftime('%Y-%m-%d'),
			"originalEnd": current['originalEnd'].strftime('%Y-%m-%d'),
			"updatedStart": current['updatedStart'].strftime('%Y-%m-%d'),
			"updatedEnd": current['updatedEnd'].strftime('%Y-%m-%d'),
			"overlapStart": end.strftime('%Y-%m-%d'),
			"overlapEnd": start.strftime('%Y-%m-%d'),
			"overlap": overlap,
			"startDifference": (next_['updatedStart'] - current['updatedStart']).days
		}
		status.append(overlapObject)
	return status

def getAverages (status):
	overlapAverage = 0.0
	gapAverage = 0.0
	startDifferenceAverage = 0.0

	startDifferences = [i['startDifference'] for i in status]
	overlaps = [i['overlap'] for i in status if i['overlap'] >= 0]
	gaps = [i['overlap'] for i in status if i['overlap'] < 0]

	print "startDifferences:", startDifferences
	if startDifferences:
		startDifferenceAverage = sum(i['startDifference'] for i in status) / float(len(startDifferences))

	print "overlaps:", overlaps
	if overlaps:
		overlapAverage = sum(overlaps) / float(len(overlaps))

	print "gaps:", gaps
	if gaps:
		gapAverage = sum(gaps) / float(len(gaps))

	print "overlapAverage:", overlapAverage
	print "gapAverage:", gapAverage
	print "startDifferenceAverage:", startDifferenceAverage
	return {
		'overlapAverage': overlapAverage,
		'gapAverage': gapAverage,
		'startDifferenceAverage': startDifferenceAverage
	}

# get feedversion with scheduled stops, and find overlap and gap averages for each feed
def getFeedService (onestop_id):
	params = {
		'feed_onestop_id': onestop_id,
		'type': 'FeedVersionInfoStatistics',
		'per_page': 'false'
	}
	feedVersionInfos = requests.get('https://transit.land/api/v1/feed_version_infos/', params=params).json().get('feed_version_infos', [])

	interpretedSchedule = []
	for feedVersionInfo in feedVersionInfos:
		sha1 = feedVersionInfo['feed_version_sha1']
		print sha1
		feedVersion = requests.get('https://transit.land/api/v1/feed_versions/%s'%sha1).json()
		if feedVersion is None:
			print "no feed_version"
			next
		if feedVersion['tags'] and feedVersion['tags'].get('gtfs_data_exchange'):
			print "gtfs_data_exchange feed; skipping"
			next
		schedule = interpretSchedule(feedVersion, feedVersionInfo)
		if schedule:
			interpretedSchedule.append(schedule)

	status = findOverlap(interpretedSchedule)
	averages = getAverages(status)

	writeToCSV("%s.csv"%onestop_id, status)
	with open('%s.json'%onestop_id, 'w') as f:
		f.write(json.dumps(status, default=lambda x:str(x)))

# call function with onestop_id as parameter
def main():
	# params = {'per_page': 'false', 'bbox': '-123.321533,36.826875,-120.786438,38.629745'}
	params = {'onestop_id': 'f-9q9-caltrain'}
	feeds = requests.get('https://transit.land/api/v1/feeds', params=params).json()['feeds']
	for feed in feeds:
		print "===== %s ====="%feed['onestop_id']
		getFeedService(feed['onestop_id'])

if __name__ == "__main__":
    main()
