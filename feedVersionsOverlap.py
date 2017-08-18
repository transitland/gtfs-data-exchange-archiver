import sys
import requests
import json
import datetime
import re

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
		id = element['id']
		scheduled_service = element['data']['scheduled_service'] 
		
		updatedScheduledService = convertToDateTime(scheduled_service)
		averageServiceHours = findAverageServiceHours(updatedScheduledService)
		updatedStart, updatedEnd = findStartAndEndDates(updatedScheduledService)
		
		updatedStart = cleanTails(updatedScheduledService, False)
		updatedEnd = cleanTails(updatedScheduledService, True)

		if (sha1, id, updatedStart, updatedEnd):
			return (sha1, id, updatedStart, updatedEnd)

# find overlaps and gaps in feed versions 
def findOverlap (interpretedSchedule): 
	
	interpretedSchedule = sorted(interpretedSchedule, key = lambda x: x[2])
	
	currentIndex = 0 
	nextIndex = 1

	status = []
	overlapValues = [0, 0]
	gapValues = [0, 0]

	while True: 
		
		current = interpretedSchedule[currentIndex]

		next = interpretedSchedule[nextIndex]
		start = next[2]
		end = current[3] 

		difference = (end - start).days

		if currentIndex == nextIndex: 
			nextIndex = nextIndex + 1

		elif end > start:

			status.append("Overlap: " + difference + " " + str(start) + " and " + str(end))

			overlapValues[0] += difference
			overlapValues[1] += 1

			nextIndex = nextIndex + 1

		elif start > end:
			status.append("Gap: " + str(start - end) + " " + str(start) + " and " + str(end))
			currentIndex = currentIndex + 1
			if groups:
				gapValues[0] += int(groups[0])
				gapValues[1] += 1

		if nextIndex >= len(interpretedSchedule) - 1: 
			currentIndex = currentIndex + 1
			nextIndex = currentIndex + 1

		if currentIndex >= len(interpretedSchedule) - 1:
			break
			
	for elem in status:
		print elem

	overlapAverage = 0
	gapAverage = 0

	if overlapValues[1]: 
		overlapAverage = overlapValues[0]/overlapValues[1]
	if gapValues[1]: 
		gapAverage = gapValues[0]/gapValues[1]

	return overlapAverage, gapAverage

# get feedversion with scheduled stops, and find overlap and gap averages for each feed 
def getFeedService (onestop_id): 
	params = (
	    ('feed_onestop_id', onestop_id),
	    ('type', 'FeedVersionInfoStatistics'),
	)

	reqService = requests.get('https://transit.land/api/v1/feed_version_infos/', params=params)
	serviceJS = json.loads(reqService.text)
	
	interpretedSchedule = []
	for element in serviceJS['feed_version_infos']:
		schedule = interpretSchedule(element)
		if schedule:
			interpretedSchedule.append(schedule)

	overlapAverage, gapAverage = findOverlap(interpretedSchedule)

	print overlapAverage
	print gapAverage

# jury is still out whether we need this or not; likely not 
# retirives feed versions
def getFeedVersions(onestop_id): 	
	params = (
		('feed_onestop_id', onestop_id), 
	)

	r = requests.get('https://transit.land/api/v1/feed_versions', params=params)
	responseJSON = json.loads(r.text)
	 
# call function with onestop_id as parameter 
def main(): 
	onestop_id = sys.argv[1] 
	# getFeedVersions(onestop_id)
	getFeedService(onestop_id)

if __name__ == "__main__":
    main()