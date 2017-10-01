import sys
import os 
import datetime
import requests
import re
import csv
import json
import glob 

globalDictionary = {} 
globalHeaderRow = ['startDate']

def retrieveFileNames():
	return glob.glob('Avgs-*.csv')

def updateGlobalDictionary(average, onestop_id): 
	dateString = str(average[0])
	print average[1]

	if dateString in globalDictionary.keys():
		globalDictionary[dateString][onestop_id] = average[1]
	else:
		globalDictionary[dateString] = {
			onestop_id: average[1]
		}

def openNewFile(fileName):
	response = re.findall('Avgs-(.*)\.csv', fileName)
	print response
	globalHeaderRow.append(response[0])

	with open(fileName, 'rU') as f:
		reader = csv.reader(f)

		for i, row in enumerate(reader):
			if i == 0:
				continue
			average = findTotalAverage(row)
			updateGlobalDictionary(average, response[0])

def findTotalAverage(row): 
	print row
	total = float(0)  
	weeklySums = row[2:]
	for hours in weeklySums: 
		total += float(hours)

	return (row[1], total/len(weeklySums)) 

def reformatDictionary(globalDictionary): 
	array = []
	for element in globalDictionary.keys():
		singleDictionary = globalDictionary[element]
		singleDictionary['startDate'] = element
		array.append(singleDictionary)

	return array

def createCSVDocument(globalDictionary): 

	filename = 'allFeedsAverage.csv'

	reformattedDictionary = reformatDictionary(globalDictionary)
	reformattedDictionary = sorted(reformattedDictionary, key = lambda x: x['startDate'], reverse=False)
	
	with open(filename, 'w') as f:
		writer = csv.DictWriter(f, fieldnames=globalHeaderRow)
		writer.writeheader()
		for elem in reformattedDictionary:
			writer.writerow(elem)

def main(): 
	fileNames = retrieveFileNames()
	print fileNames

	for nameOfFile in fileNames:
		openNewFile(nameOfFile)

	createCSVDocument(globalDictionary)


if __name__ == "__main__":
    main()