#!/usr/bin/python

import itertools
import sys
import os

# Helper methods
# Check the result in the log and print a summary
def checkResult(logDirName):
	extractResult = open(logDirName, "r")
	result = "other errors--PLEASE CHECK!"
	
	for line in extractResult:
		if "no errors detected" in line:
			result = "no conflict"
			break
		elif "java.lang.RuntimeException: Conflict found between the two apps." in line:
			result = "conflict"
			break
		# TODO: We are now detecting Direct-Direct interaction in the analysis
		#elif "Direct-Direct Interaction detected:" in line:
		#	result = "direct-direct"
		#	break
	
	return result

# Extract the error from specific error logs
def extractError():
	err = ""
	if os.path.exists("appCreationError.log"):
		extractError = open("appCreationError.log", "r")
		for line in extractError:
			err = err + line
		extractError.close()
		os.system("rm appCreationError.log")
	return err

# Write error log to the log directory
# In this case we skip running JPF
# e.g., in the case of having a direct-direct interaction pair
def writeErrorLog(jpfLogDir, logName, error):
	writeError = open(jpfLogDir + logName, "w+")
	writeError.write(error)
	writeError.close()

# Activate and deactivate certain options in main.jpf
def changeOption(newString, oldString):
	print("==> Changing option...\n")
	fin = open("../jpf-core/main.jpf", "rt")
	config = fin.read()
	config = config.replace(oldString, newString)
	#print(config)
	fin.close()
	fin = open("../jpf-core/main.jpf", "wt")
	fin.write(config)
	fin.close

# Insert pair name into moreStatistics
def insertPairName(pairName):
	print("==> Insert pair name into moreStatistics...\n")
	fin = open("../jpf-core/moreStatistics", "rt")
	config = fin.read()
	config += '\n' + pairName + '\n'
	#print(config)
	fin.close()
	fin = open("../jpf-core/moreStatistics", "wt")
	fin.write(config)
	fin.close

# Input parameters:
# - JPF directory
# - JPF logs directory
# - app directory
# - list #1
# - run with DPOR?
# - include conflict detection when running DPOR?

# Index 0 is always for the Python script itself
jpfDir = sys.argv[1]
jpfLogDir = sys.argv[2]
appDir = sys.argv[3]
isDPOR = sys.argv[4]
isConflictDetectionActive = sys.argv[5]
firstList = sys.argv[6]

# PART 1: Generate the permutations of app pairs
print("PHASE 1: Extracting the app pairs from the app lists ...\n")
appList1 = []
appList2 = []
# Extract the first list
extractAppList = open(firstList, "r")
for app in extractAppList:
	if '#' not in app:
		appList1.append(app.strip())
extractAppList.close()

# Try to create pairs
appPairs = []
useSecondList = False
# Extract the second list if provided (this is for combinations between two lists)
if (len(sys.argv) == 8):
	secondList = sys.argv[7]
	extractAppList = open(secondList, "r")
	for app in extractAppList:
		if '#' not in app:
			appList2.append(app.strip())
	extractAppList.close()
	useSecondList = True
# Just copy the first list to the second list
else:
	appList2 = appList1

if useSecondList is False:
	# Generate the permutations of pairs
	for i in range(len(appList1)):
		for j in range(i + 1, len(appList2)):
			appPairs.append((appList1[i], appList2[j]))
else:
	# Generate pairs from 2 lists
	for i in range(len(appList1)):
		for j in range(len(appList2)):
			# Skip if both are the same
			if appList1[i] == appList2[j]:
				continue
			appPairs.append((appList1[i], appList2[j]))

		
# PART 2: 
print("PHASE 2: Running JPF ...\n")
# List down all the log file names
writeLogList = open(jpfLogDir + "logList", "w+")
for item in appPairs:

	# Copy apps into Extractor/App1 and Extractor/App2
	print("==> First app: %s" % item[0])
	print("==> Second app: %s" % item[1])
	os.system("cp " + appDir + item[0] + " Extractor/App1/App1.groovy")
	os.system("cp " + appDir + item[1] + " Extractor/App2/App2.groovy")
	
	# Run Runner.py to extract things and create main.groovy, then compile it
	print("==> Compiling the apps ...\n")
	os.system("make Runner")
	error = extractError()
	pairName = item[0] + "--" + item[1]
	# Insert pair name into moreStatistics
	insertPairName(pairName)
	logName = pairName + ".log"
	if error == "":
		# Compile
		os.system("make main")
		# Call JPF
		print("==> Calling JPF and generate logs ...\n")
		# Change options in main.jpf
		changeOption('# These are JPF listeners',
				     '# This is the listener that can detect variable write-after-write conflicts')
		if isDPOR == 'true':
			# activate_state_reduction=true
			changeOption('listener=gov.nasa.jpf.listener.ConflictTracker\n' \
						 'listener=gov.nasa.jpf.listener.DPORStateReducerWithSummary\n\n# Options for DPORStateReducerWithSummary\nprintout_state_transition=true\n#activate_state_reduction=false\nfile_output=moreStatistics\n',
						 'listener=gov.nasa.jpf.listener.ConflictTracker')
		else:
			# activate_state_reduction=false
			changeOption('listener=gov.nasa.jpf.listener.ConflictTracker\n' \
						 'listener=gov.nasa.jpf.listener.DPORStateReducerWithSummary\n\n# Options for DPORStateReducerWithSummary\nprintout_state_transition=true\nactivate_state_reduction=false\nfile_output=moreStatistics\n',
						 'listener=gov.nasa.jpf.listener.ConflictTracker')
		# Deactivate conflict detection
		if isConflictDetectionActive == 'false':
			changeOption('#listener=gov.nasa.jpf.listener.ConflictTracker',
						 'listener=gov.nasa.jpf.listener.ConflictTracker')
		# Change timeout to 2 hours (120 minutes)
		changeOption('timeout=120',
				     'timeout=30')
		os.system("cd " + jpfDir + ";./run.sh " + jpfLogDir + logName + " main.jpf")
	else:
		# This is for specific error, e.g., direct-direct interaction that we need to skip
		writeErrorLog(jpfLogDir, logName, error)
	result = checkResult(jpfLogDir + logName)

	writeLogList.write(logName + "\t\t" + result + "\n")

writeLogList.close()