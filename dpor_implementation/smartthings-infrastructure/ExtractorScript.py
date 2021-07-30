import os
readyToReturn = 0
ToReturn = ""
eventList = []
eventAppList = [] # This list maps App1 or App2 to a specific event
eventVarMap = {}
eventVarCounterMap = {}
capabilityMap = {}
capabilityList = []
app1Capabilities = []
app2Capabilities = []
app1Subscribe = False
app2Subscribe = False

# Mapping for event type and number of events
# e.g., switch has 2 events: on and off
eventTypeCounterMap =  {'lock': 2,
						'nfcTouch' : 1,
						'app' : 1,
						'button' : 2,
						'water' : 2,
						'water.dry' : 1,
						'water.wet' : 1,
						'presence' : 2,
						'doorState' : 2,
						'motion' : 2,
						'smoke' : 3,
						'carbonMonoxide' : 3,
						'battery' : 1,
						'thermostatMode' : 5,
						'thermostatFanMode' : 5,
						'thermostatOperatingState' : 5,
						'switch' : 2,
						'location' : 3,
						'mode' : 3,
						'sunset' : 1,
						'sunsetTime' : 1,
						'sunrise' : 1,
						'sunriseTime' : 1,
						'acceleration' : 2,
						'sleeping' : 2,
						'goal' : 2,
						'steps' : 2,
						'color' : 1,
						'colorTemperature' : 1,
						'hue' : 1,
						'saturation' : 1,
						'energy' : 1,
						'power' : 2,
						'illuminance' : 2,
						'humidity' : 2,
						'alarm' : 4,
						'contact' : 2,
						'status' : 3,
						'level' : 1,
						'trackDescription' : 1,
						'trackData' : 1,
						'mute' : 2,
						'temperature' : 2,
						'heatingSetpoint' : 1,
						'coolingSetpoint' : 1,
						'thermostatSetpoint' : 1,
						'threeAxis' : 1,
						'carbonDioxide' : 1,
						'consumableStatus' : 1,
						'pH' : 1,
						'pressure': 1,
						'shock': 1,
						'lqi': 1,
						'rssi': 1,
						'schedule': 1,
						'sound': 1,
						'soundPressureLevel' : 1,
						'tamper' : 1,
						'ultravioletIndex': 1,
						'voltage': 1,
						'windowShade': 1,
						'touched': 1,
						'alarm.both': 1,
						'alarm.siren' : 1,
						'alarm.strobe' : 1,
						'alarm.off' : 1,
						'contact.open' : 1,
						'contact.closed' : 1,
						'tamper.tampered' : 2,
						'doorState.open' : 1,
						'doorState.closed' : 1,
						'position' : 3,
						'mode' : 3,
						'mode.away' : 1,
						'mode.home' : 1,
						'mode.night' : 1,
						'lock.locked' : 1,
						'lock.unlocked' : 1,
						'motion.active' : 1,
						'motion.inactive' : 1,
						'status.playing' : 1,
						'status.stopped' : 1,
						'status.paused' : 1,
						'mute.muted' : 1,
						'mute.unmuted' : 1,
						'presence.present' : 1,
						'presence.not present' : 1,
						'presence.not' : 1,
						'smoke.detected' : 1,
						'smoke.clear' : 1,
						'smoke.tested' : 1,
						'carbonMonoxide.detected' : 1,
						'carbonMonoxide.clear' : 1,
						'carbonMonoxide.tested' : 1,
						'thermostatMode.cool' : 1,
						'thermostatMode.auto' : 1,
						'thermostatMode.emergencyHeat' : 1,
						'thermostatMode.heat' : 1,
						'thermostatMode.off' : 1,
						'thermostatFanMode.auto' : 1,
						'thermostatFanMode.fanCirculate' : 1,
						'thermostatFanMode.circulate' : 1,
						'thermostatFanMode.fanOn' : 1,
						'thermostatFanMode.on' : 1,
						'fanMode' : 5,
						'fanMode.auto' : 1,
						'fanMode.fanCirculate' : 1,
						'fanMode.circulate' : 1,
						'fanMode.fanOn' : 1,
						'fanMode.on' : 1,
						'switch.on' : 1,
						'switch.off' : 1,
						'button.pushed' : 1,
						'button.held' : 1,
						'acceleration.active' : 1,
						'acceleration.inactive' : 1,
						'sleeping.sleeping' : 1,
						'sleeping.not sleeping' : 1,
						'water.dry' : 1,
						'water.wet' : 1
						}

def GetToken(f):
	global readyToReturn
	global ToReturn
	Skip = ['\n', '\t', ' ']
	Special = ["(", "\"", ":", ",", "{", "}", ")", "/", "*"]
	S = ""
	if (readyToReturn):
		readyToReturn = 0
		return ToReturn
	ToReturn = ""
	c = f.read(1)
	while(True):
		if (c in Special):
			if (S != ""):
				readyToReturn = 1
				ToReturn = c
				return S
			else:
				return c
		elif (c in Skip):
			if (S != ""):
				return S	
			else:
				c = f.read(1)
				continue
		S += c
		c = f.read(1)
		if not c:
			return "EOF"

def ExtractFunctions(F, appName):
	global eventList
	global eventAppList
	global app1Subscribe
	global app2Subscribe
	Temp = GetToken(F)
	while (Temp != "EOF"):
		if (Temp == "def" or Temp == "private"):
			Temp = GetToken(F)
			if (Temp == "def" or Temp == "private"):
				Temp = GetToken(F)
			NameofFunc = Temp
			if (GetToken(F) == "("): #We have a function to create object for
				if (appName == "App1"):
					extractedFunctionsApp1.write("//Global Object for functions in subscribe method!\n")	
					extractedFunctionsApp1.write("def %s = this.&" % NameofFunc)
					extractedFunctionsApp1.write("%s\n" % NameofFunc)
				else:
					extractedFunctionsApp2.write("//Global Object for functions in subscribe method!\n")	
					extractedFunctionsApp2.write("def %s = this.&" % NameofFunc)
					extractedFunctionsApp2.write("%s\n" % NameofFunc)
		
		#Check subscribed events
		if (Temp == "initialize" or Temp == "installed"):
			Temp = GetToken(F)
			Temp = GetToken(F)
			Temp = GetToken(F)
			# If it is a schedule function, then extract the scheduled method and put it as one of the events
			if (Temp == "schedule"):
				eventList.append("schedule")
				if (appName == "App1"):
					eventAppList.append("App1")
				else:
					eventAppList.append("App2")
				while Temp != ",":
					Temp = GetToken(F)
				Temp = GetToken(F)
				# If this is a " then get the next one still---we are interested in the scheduled function name
				if (Temp == "\""):
					Temp = GetToken(F)
				# Insert function name into the map
				if "schedule" in eventVarMap.keys():
					listOfEvents = eventVarMap["schedule"]
					listOfEvents.append(Temp)
				else:
					eventVarMap["schedule"] = [Temp]
		
		#Check input capability
		if (Temp == "input"):
			while Temp != "\"":
				Temp = GetToken(F)
			variable = GetToken(F)
			Temp = GetToken(F) #Get '"'
			Temp = GetToken(F) #Get ','
			while Temp != "\"":
				Temp = GetToken(F)
			capability = GetToken(F)
			capabilityMap[variable] = capability
		
		#Check subscribed events
		if (Temp == "subscribe"):
			if (appName == "App1"):
				app1Subscribe = True
			else:
				app2Subscribe = True
			Temp = GetToken(F)
			if (Temp == "("):
				Temp = GetToken(F)
			variable = Temp
			while (Temp != "\"" and Temp != "app" and Temp != "location"):
				Temp = GetToken(F)
			if Temp == "location":
				# See if we have another case for location
				Temp = GetToken(F) # Get ','
				Temp = GetToken(F) # Get '"'
				if Temp == "\"":
					Temp = GetToken(F)			
				else:
					# This is the special case where we will see, e.g., sunset, sunrise, etc.
					Temp = "location"
			if Temp == "\"":
				Temp = GetToken(F)

			#print "DEBUG: %s - %s" % (variable, Temp)
			#print capabilityMap
			#print "DEBUG: location variable: %s" % Temp	

            #This is a bogus event, just skip it...
			if Temp == "unlock":
				continue
			if Temp == "app" or Temp == "location" or Temp == "position" or Temp == "mode" or Temp == "mode.away" or Temp == "mode.home" or Temp == "mode.night" or \
				Temp == "sunset" or Temp == "sunrise" or Temp == "sunsetTime" or Temp == "sunriseTime":
				if Temp not in eventList:
					eventList.append(Temp)
					if (appName == "App1"):
						eventAppList.append("App1")
					else:
						eventAppList.append("App2")
			elif Temp not in eventList or (variable in capabilityMap.keys() and capabilityMap[variable] not in capabilityList):
				# We do not repeat the same capability twice
				capability = capabilityMap[variable]
				capabilityList.append(capability)
				eventList.append(Temp)
				if (appName == "App1"):
					eventAppList.append("App1")
				else:
					eventAppList.append("App2")
				if Temp in eventVarMap.keys():
					listOfEvents = eventVarMap[Temp]
					listOfEvents.append(variable)
				else:
					eventVarMap[Temp] = [variable]
			#print "DEBUG: %s - %s" % (variable, Temp)
			#print capabilityMap
			#print eventList

		#Check and analyze capabilities for physical interaction
		AnalyzeCapabilities(Temp, appName, F)

		Temp = GetToken(F)
	
	#Warn if there is a potential for physical interaction
	AnalyzePhysicalInteraction(app1Capabilities, app2Capabilities)
	AnalyzePhysicalInteraction(app2Capabilities, app1Capabilities)

def AnalyzeCapabilities(Temp, appName, F):
			#Illuminance related
	if (Temp == "capability.switch" or
			Temp == "capability.switchLevel" or
			Temp == "capability.illuminanceMeasurement" or
			Temp == "capability.colorControl" or
			Temp == "capability.colorTemperature" or
			#Motion related
			Temp == "capability.motionSensor" or
			Temp == "capability.accelerationSensor" or
			#Water related
			Temp == "capability.valve" or
			Temp == "capability.waterSensor" or
			#Sound related
			Temp == "capability.musicPlayer" or
			Temp == "capability.alarm" or
			Temp == "capability.speechSynthesis" or
			Temp == "capability.soundSensor"):
		if (appName == "App1"):
			app1Capabilities.append(Temp)
		else:
			app2Capabilities.append(Temp)
	if (Temp == "capability"):
		Temp = GetToken(F) #Get '"'
		Temp = GetToken(F) #Get 'Music'
		Temp = Temp + GetToken(F) #Get 'Player'
		if (Temp == "MusicPlayer"):
			if (appName == "App1"):
				app1Capabilities.append("capability.musicPlayer")
			else:
				app2Capabilities.append("capability.musicPlayer")
			
def AnalyzePhysicalInteraction(app1Capab, app2Capab):
	#Light
	if ("capability.illuminanceMeasurement" in app1Capab) and ("capability.switch" in app2Capab or 
			"capability.switchLevel" in app2Capab or "capability.colorControl" or "capability.colorTemperature" in app2Capab):
		print ("\nWARNING: Potential PHYSICAL CONFLICT (light) detected between App1 and App2!\n")
	#Motion
	# TODO: Technically this is not entirely precise since we need to be able to detect that the other app creates motion
	if ("capability.motionSensor" in app1Capab) or ("capability.accelerationSensor" in app1Capab):
		print ("\nWARNING: Potential PHYSICAL CONFLICT (motion) detected between App1 and App2!\n")		
	#Water
	if ("capability.waterSensor" in app1Capab) and ("capability.valve" in app2Capab or 
			"capability.switch" in app2Capab):
		print ("\nWARNING: Potential PHYSICAL CONFLICT (water) detected between App1 and App2!\n")
	#Sound
	if ("capability.soundSensor" in app1Capab) and ("capability.musicPlayer" in app2Capab or 
			"capability.alarm" in app2Capab or "capability.speechSynthesis" in app2Capab):
		print ("\nWARNING: Potential PHYSICAL CONFLICT (sound) detected between App1 and App2!\n")

def CountEvents():
	global eventList
	numOfActualEvents = 0
	#print "DEBUG: eventlist: %d" % len(eventList)
	#print "DEBUG: eventlist: %s" % eventList
	for event in eventList:
		print("DEBUG: Event: %s %d" % (event, eventTypeCounterMap[event]))
		numOfActualEvents = numOfActualEvents + eventTypeCounterMap[event]
	return numOfActualEvents

def ExtractEvents(extractedEvents):
	global eventList
	global eventAppList
	global eventVarMap
	global capabilityMap
	global eventVarCounterMap
	# Count the number of events
	numOfActualEvents = CountEvents()
	# Use the following lines to print out numbers of events
	#evtFile = open("numberOfEvents", "a+")
	#evtFile.write(str(numOfActualEvents))
	#evtFile.write("\n")
	#evtFile.close()
	extractedEvents.write("while(true) {\n")
	# We use Verify.getIntFromList() instead of Verify.getInt() since we want to manipulate the
	# choices in the list/set to implement POR
	#extractedEvents.write("\tdef eventNumber = Verify.getInt(0,%d)\n" % (numOfActualEvents - 1))
	extractedEvents.write("\tdef eventNumber = Verify.getIntFromList(0,")
	if (numOfActualEvents == 1):
		extractedEvents.write("1)\n")
	else:
		for x in range (1, numOfActualEvents - 1):
			extractedEvents.write("%d," % x)
		extractedEvents.write("%d)\n" % (numOfActualEvents - 1))
	extractedEvents.write("\tswitch(eventNumber) {\n")
	counter = 0
	indexApp1 = 0
	if "App2" in eventAppList:
		indexApp2 = eventAppList.index("App2")
	else:
		indexApp2 = len(eventList)
	indexApp2Start = indexApp2
	#print "DEBUG: App1: %d" % indexApp1
	#print "DEBUG: App2: %d" % indexApp2
	#print "DEBUG: eventList: %d" % len(eventList)
	#print capabilityMap
	#print eventVarMap
	#print eventAppList
	#print eventList
	if indexApp2Start > 0:
		isApp1 = True
	else:
		isApp1 = False
	while counter < numOfActualEvents:
		# Interleave events from App1 and App2
		if isApp1 is True:
			i = indexApp1
			indexApp1 = indexApp1 + 1
			if indexApp2 < len(eventList):
				isApp1 = False
		else:
			i = indexApp2
			indexApp2 = indexApp2 + 1
			if indexApp1 < indexApp2Start:
				isApp1 = True
		#print "DEBUG: i: %d" % i
		extractedEvents.write("\t\tcase %d:\n" % counter)
		if eventList[i] == "schedule":
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			currentMethod = variable[eventVarCount]
			extractedEvents.write("\t\t\t// Scheduled method in installed() or intialize()\n")
			extractedEvents.write("\t\t\t%s.%s()" % (eventAppList[i].lower(), currentMethod))
		elif eventList[i] == "lock":
			#Write two events subsequently
			event = open("eventSimulator/lockLockedEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/lockUnlockedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "lock.locked":
			event = open("eventSimulator/lockLockedEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "lock.unlocked":
			event = open("eventSimulator/lockUnlockedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "nfcTouch":
			event = open("eventSimulator/nfcTouchEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "app": #Case for Touched event
			event = open("eventSimulator/appTouchEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "button":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write two events subsequently
			if capability == "capability.button":
				event = open("eventSimulator/buttonHeldEvent.groovy", "r")
			elif capability == "device.aeonKeyFob":
				event = open("eventSimulator/aeonKeyFobHeldEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			if capability == "capability.button":
				event = open("eventSimulator/buttonPushedEvent.groovy", "r")
			elif capability == "device.aeonKeyFob":
				event = open("eventSimulator/aeonKeyFobPushedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "button.pushed":
			event = open("eventSimulator/buttonPushedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "button.held":
			event = open("eventSimulator/buttonHeldEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "water":
			#Write two events subsequently
			event = open("eventSimulator/waterDryEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/waterWetEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "water.dry":
			event = open("eventSimulator/waterDryEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "water.wet":
			event = open("eventSimulator/waterWetEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "presence":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write two events subsequently
			if capability == "capability.presenceSensor":
				event = open("eventSimulator/presencePresentEvent.groovy", "r")
			elif capability == "capability.beacon":
				event = open("eventSimulator/beaconPresentEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			if capability == "capability.presenceSensor":
				event = open("eventSimulator/presenceLeftEvent.groovy", "r")
			elif capability == "capability.beacon":
				event = open("eventSimulator/beaconLeftEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "presence.present":
			event = open("eventSimulator/presencePresentEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "presence.not present" or eventList[i] == "presence.not":
			event = open("eventSimulator/presenceLeftEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()			
		elif eventList[i] == "doorState":
			#Write two events subsequently
			event = open("eventSimulator/doorOpenEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/doorClosedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "doorState.open":
			event = open("eventSimulator/doorOpenEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "doorState.closed":
			event = open("eventSimulator/doorClosedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "motion":
			#Write two events subsequently
			event = open("eventSimulator/motionActiveEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/motionInactiveEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "motion.active":
			event = open("eventSimulator/motionActiveEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "motion.inactive":
			event = open("eventSimulator/motionInactiveEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "smoke":
			#Write three events subsequently
			event = open("eventSimulator/smokeClearEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/smokeDetectedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/smokeTestedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "smoke.clear":
			event = open("eventSimulator/smokeClearEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "smoke.detected":
			event = open("eventSimulator/smokeDetectedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "smoke.tested":
			event = open("eventSimulator/smokeTestedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "carbonMonoxide":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write three events subsequently	
			if capability == "capability.smokeDetector":
				event = open("eventSimulator/smokeCarbonMonoxideClearEvent.groovy", "r")
			elif capability == "capability.carbonMonoxideDetector":
				event = open("eventSimulator/carbonMonoxideClearEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			if capability == "capability.smokeDetector":
				event = open("eventSimulator/smokeCarbonMonoxideDetectedEvent.groovy", "r")
			elif capability == "capability.carbonMonoxideDetector":
				event = open("eventSimulator/carbonMonoxideDetectedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			if capability == "capability.smokeDetector":
				event = open("eventSimulator/smokeCarbonMonoxideTestedEvent.groovy", "r")
			elif capability == "capability.carbonMonoxideDetector":
				event = open("eventSimulator/carbonMonoxideTestedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "carbonMonoxide.clear":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write three events subsequently	
			if capability == "capability.smokeDetector":
				event = open("eventSimulator/smokeCarbonMonoxideClearEvent.groovy", "r")
			elif capability == "capability.carbonMonoxideDetector":
				event = open("eventSimulator/carbonMonoxideClearEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "carbonMonoxide.detected":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write three events subsequently	
			if capability == "capability.smokeDetector":
				event = open("eventSimulator/smokeCarbonMonoxideDetectedEvent.groovy", "r")
			elif capability == "capability.carbonMonoxideDetector":
				event = open("eventSimulator/carbonMonoxideDetectedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "carbonMonoxide.tested":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write three events subsequently	
			if capability == "capability.smokeDetector":
				event = open("eventSimulator/smokeCarbonMonoxideTestedEvent.groovy", "r")
			elif capability == "capability.carbonMonoxideDetector":
				event = open("eventSimulator/carbonMonoxideTestedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "battery":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			if capability == "capability.smokeDetector":
				event = open("eventSimulator/smokeDetectorBatteryEvent.groovy", "r")
			elif capability == "capability.battery":
				event = open("eventSimulator/batteryBatteryEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatMode":
			#Write five events subsequently
			event = open("eventSimulator/thermostatAutoModeEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatCoolModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatEmergencyHeatModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatHeatModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatOffModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatMode.cool":
			event = open("eventSimulator/thermostatCoolModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatMode.auto":
			event = open("eventSimulator/thermostatAutoModeEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatMode.emergencyHeat":
			event = open("eventSimulator/thermostatEmergencyHeatModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatMode.heat":
			event = open("eventSimulator/thermostatHeatModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatMode.off":
			event = open("eventSimulator/thermostatOffModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatFanMode" or eventList[i] == "fanMode":
			#Write five events subsequently
			event = open("eventSimulator/thermostatAutoFanModeEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatFanCirculateFanModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatCirculateFanModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatFanOnFanModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatOnFanModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatFanMode.auto" or eventList[i] == "fanMode.auto":
			event = open("eventSimulator/thermostatAutoFanModeEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatFanMode.fanCirculate" or eventList[i] == "fanMode.fanCirculate":
			event = open("eventSimulator/thermostatFanCirculateFanModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatFanMode.circulate" or eventList[i] == "fanMode.circulate":
			event = open("eventSimulator/thermostatCirculateFanModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatFanMode.fanOn" or eventList[i] == "fanMode.fanOn":
			event = open("eventSimulator/thermostatFanOnFanModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatFanMode.on" or eventList[i] == "fanMode.on":
			event = open("eventSimulator/thermostatOnFanModeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatOperatingState":
			#Write five events subsequently
			event = open("eventSimulator/thermostatOperatingStateAutoEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatOperatingStateCoolEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatOperatingStateOffEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatOperatingStateEmergencyHeatEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/thermostatOperatingStateHeatEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "switch":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write two events subsequently
			if capability == "capability.switch":
				event = open("eventSimulator/switchOnEvent.groovy", "r")
			elif capability == "capability.switchLevel":
				event = open("eventSimulator/switchLevelOnEvent.groovy", "r")
			elif capability == "capability.relaySwitch":
				event = open("eventSimulator/relaySwitchOnEvent.groovy", "r")
			elif capability == "capability.colorControl":
				event = open("eventSimulator/colorControlSwitchOnEvent.groovy", "r")
			elif capability == "capability.colorTemperature":
				event = open("eventSimulator/colorTemperatureSwitchOnEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			if capability == "capability.switch":
				event = open("eventSimulator/switchOffEvent.groovy", "r")
			elif capability == "capability.switchLevel":
				event = open("eventSimulator/switchLevelOffEvent.groovy", "r")
			elif capability == "capability.relaySwitch":
				event = open("eventSimulator/relaySwitchOffEvent.groovy", "r")
			elif capability == "capability.colorControl":
				event = open("eventSimulator/colorControlSwitchOffEvent.groovy", "r")
			elif capability == "capability.colorTemperature":
				event = open("eventSimulator/colorTemperatureSwitchOffEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "switch.on":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			if capability == "capability.switch":
				event = open("eventSimulator/switchOnEvent.groovy", "r")
			elif capability == "capability.switchLevel":
				event = open("eventSimulator/switchLevelOnEvent.groovy", "r")
			elif capability == "capability.relaySwitch":
				event = open("eventSimulator/relaySwitchOnEvent.groovy", "r")
			elif capability == "capability.colorControl":
				event = open("eventSimulator/colorControlSwitchOnEvent.groovy", "r")
			elif capability == "capability.colorTemperature":
				event = open("eventSimulator/colorTemperatureSwitchOnEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "switch.off":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			if capability == "capability.switch":
				event = open("eventSimulator/switchOffEvent.groovy", "r")
			elif capability == "capability.switchLevel":
				event = open("eventSimulator/switchLevelOffEvent.groovy", "r")
			elif capability == "capability.relaySwitch":
				event = open("eventSimulator/relaySwitchOffEvent.groovy", "r")
			elif capability == "capability.colorControl":
				event = open("eventSimulator/colorControlSwitchOffEvent.groovy", "r")
			elif capability == "capability.colorTemperature":
				event = open("eventSimulator/colorTemperatureSwitchOffEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "location" or eventList[i] == "position" or eventList[i] == "mode": #Case for Location event
			#Write three events subsequently
			event = open("eventSimulator/locationHomeEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/locationAwayEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/locationNightEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "mode.home":
			event = open("eventSimulator/locationHomeEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "mode.away":
			event = open("eventSimulator/locationAwayEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "mode.night":
			event = open("eventSimulator/locationNightEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "sunrise":
			event = open("eventSimulator/locationSunriseEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "sunset":
			event = open("eventSimulator/locationSunsetEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "sunsetTime":
			event = open("eventSimulator/locationSunsetTimeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "sunriseTime":
			event = open("eventSimulator/locationSunriseTimeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "acceleration":
			#Write two events subsequently
			event = open("eventSimulator/accelerationActiveEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/accelerationInactiveEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "acceleration.active":
			event = open("eventSimulator/accelerationActiveEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "acceleration.inactive":
			event = open("eventSimulator/accelerationInactiveEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "sleeping":
			#Write two events subsequently
			event = open("eventSimulator/sleepSleepingEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/sleepNotSleepingEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "sleeping.sleeping":
			event = open("eventSimulator/sleepSleepingEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "sleeping.not sleeping":
			event = open("eventSimulator/sleepNotSleepingEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "goal":
			#Write two events subsequently
			event = open("eventSimulator/stepGoalHighEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/stepGoalLowEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "steps":
			#Write two events subsequently
			event = open("eventSimulator/stepStepsHighEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/stepStepsLowEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "color":
			event = open("eventSimulator/colorChangeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "colorTemperature":
			event = open("eventSimulator/colorTemperatureEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "hue":
			event = open("eventSimulator/hueChangeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "saturation":
			event = open("eventSimulator/saturationChangeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "energy":
			event = open("eventSimulator/energyMeterEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "power":
			#Write two events subsequently
			event = open("eventSimulator/powerMeterHighPowerEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/powerMeterLowPowerEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "illuminance":
			event = open("eventSimulator/illuminanceMeasurementLowEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/illuminanceMeasurementHighEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "humidity":
			event = open("eventSimulator/humidityHighMeasurementEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/humidityLowMeasurementEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "alarm":
			#Write four events subsequently
			event = open("eventSimulator/alarmBothEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/alarmSirenEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/alarmStrobeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/alarmOffEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "alarm.both":
			event = open("eventSimulator/alarmBothEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "alarm.siren":
			event = open("eventSimulator/alarmSirenEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "alarm.strobe":
			event = open("eventSimulator/alarmStrobeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "alarm.off":
			event = open("eventSimulator/alarmOffEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "contact" or eventList[i] == "tamper.tampered":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write two events subsequently
			if capability == "capability.contactSensor":
				event = open("eventSimulator/contactDefaultClosedEvent.groovy", "r")
			elif capability == "capability.valve":
				event = open("eventSimulator/valveClosedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			if capability == "capability.contactSensor":
				event = open("eventSimulator/contactDefaultOpenEvent.groovy", "r")
			elif capability == "capability.valve":
				event = open("eventSimulator/valveOpenEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "contact.closed":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			if capability == "capability.contactSensor":
				event = open("eventSimulator/contactDefaultClosedEvent.groovy", "r")
			elif capability == "capability.valve":
				event = open("eventSimulator/valveClosedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "contact.open":
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			if capability == "capability.contactSensor":
				event = open("eventSimulator/contactDefaultOpenEvent.groovy", "r")
			elif capability == "capability.valve":
				event = open("eventSimulator/valveOpenEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "status":
			#Write three events subsequently
			event = open("eventSimulator/musicPlayerPlayingEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/musicPlayerStoppedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/musicPlayerPausedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "status.playing":
			event = open("eventSimulator/musicPlayerPlayingEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "status.stopped":
			event = open("eventSimulator/musicPlayerStoppedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "status.paused":
			event = open("eventSimulator/musicPlayerPausedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "level":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			if capability == "capability.musicPlayer":
				event = open("eventSimulator/musicPlayerLevelEvent.groovy", "r")
			elif capability == "capability.switchLevel":
				event = open("eventSimulator/switchLevelEvent.groovy", "r")
			elif capability == "capability.colorControl":
				event = open("eventSimulator/colorLevelChangeEvent.groovy", "r")
			elif capability == "capability.switch":
				event = open("eventSimulator/switchLevelChangeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "trackDescription":
			event = open("eventSimulator/musicPlayerTrackDescriptionEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "trackData":
			event = open("eventSimulator/musicPlayerTrackDataEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "mute":
			#Write two events subsequently
			event = open("eventSimulator/musicPlayerUnmutedEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			event = open("eventSimulator/musicPlayerMutedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "mute.muted":
			event = open("eventSimulator/musicPlayerUnmutedEvent.groovy", "r")			
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "mute.unmuted":
			event = open("eventSimulator/musicPlayerMutedEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "temperature":
			#Check which capability
			variable = eventVarMap[eventList[i]]
			if eventList[i] not in eventVarCounterMap.keys():
				eventVarCounterMap[eventList[i]] = 1
				eventVarCount = 0
			else:
				eventVarCount = eventVarCounterMap[eventList[i]]
				eventVarCounterMap[eventList[i]] = eventVarCount + 1
			capability = capabilityMap[variable[eventVarCount]]
			#Write two events subsequently
			if capability == "capability.thermostat":
				event = open("eventSimulator/temperatureHighEvent.groovy", "r")
			elif capability == "capability.temperatureMeasurement":
				event = open("eventSimulator/temperatureHighMeasurementEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			extractedEvents.write("\n\t\t\tbreak\n")
			counter = counter + 1
			extractedEvents.write("\t\tcase %d:\n" % counter)
			if capability == "capability.thermostat":
				event = open("eventSimulator/temperatureLowEvent.groovy", "r")
			elif capability == "capability.temperatureMeasurement":
				event = open("eventSimulator/temperatureLowMeasurementEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "heatingSetpoint":
			event = open("eventSimulator/heatingSetpointEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "coolingSetpoint":
			event = open("eventSimulator/coolingSetpointEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "thermostatSetpoint":
			event = open("eventSimulator/thermostatSetpointEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "threeAxis":
			event = open("eventSimulator/threeAxisChangeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "carbonDioxide":
			event = open("eventSimulator/carbonDioxideEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "consumableStatus":
			event = open("eventSimulator/consumableStatusEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "pH":
			event = open("eventSimulator/pHEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "pressure":
			event = open("eventSimulator/pressureEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "shock":
			event = open("eventSimulator/shockEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "lqi":
			event = open("eventSimulator/lqiEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "rssi":
			event = open("eventSimulator/rssiEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "sound":
			event = open("eventSimulator/soundEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "soundPressureLevel":
			event = open("eventSimulator/soundPressureLevelEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "tamper":
			event = open("eventSimulator/tamperEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "voltage":
			event = open("eventSimulator/voltageEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "ultravioletIndex":
			event = open("eventSimulator/ultravioletIndexEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
		elif eventList[i] == "windowShade":
			event = open("eventSimulator/windowShadeEvent.groovy", "r")
			for line in event:
				extractedEvents.write(line)
			event.close()
			
		###TODO: Add more events later
		extractedEvents.write("\n\t\t\tbreak\n")
		counter = counter + 1
	extractedEvents.write("\t}\n")
	extractedEvents.write("\tprintln(\"\\nEVENT NUMBER: \" + eventNumber)\n");
	extractedEvents.write("}\n")
	
def CheckIfOnlyTouchEvents():
	#Check and throw an error if it is all touch events
	#This is called Direct-Direct interaction and we do not model-check for this case
	# TODO: Commenting out this code since we do this in the analysis itself
	'''
	onlyTouchEvents = True
	for item in eventList:
		if item != "nfcTouch" and item != "app" and item != "button":
			onlyTouchEvents = False
	if onlyTouchEvents is True and app1Subscribe is True and app2Subscribe is True:
		# Write error log file
		extractError = open("appCreationError.log", "w+")
		extractError.write("Direct-Direct Interaction detected: we are skipping this pair...\n")
		extractError.close()
		raise Exception("\n\nDirect-Direct Interaction detected: we are skipping this pair...\n\n")
	'''

#Extract objects to call functions from App1
F1 = open("Extractor/App1/App1.groovy", "r")
extractedFunctionsApp1 = open("Extractor/App1/extractedFunctionsApp1.groovy", "w+")
ExtractFunctions(F1, "App1")
F1.close()

#Extract objects to call functions from App2
F2 = open("Extractor/App2/App2.groovy", "r")
extractedFunctionsApp2 = open("Extractor/App2/extractedFunctionsApp2.groovy", "w+")
ExtractFunctions(F2, "App2")
F2.close()

#Prepare eventSimulator file while parsing the App1 and App2 files
extractedEvents = open("eventSimulator/eventSimulator.groovy", "w+")
CheckIfOnlyTouchEvents()
ExtractEvents(extractedEvents)
extractedEvents.close()

#Save the extracted methods and app1 in a same file to extract information
extractorFile = open("Extractor/extractorFile.groovy", "w+")
Extractor = open("Extractor/Extractor.groovy", "r")
F1 = open("Extractor/App1/App1.groovy", "r")

extractorFile.write("////////////////////\n")
extractorFile.write("@Field App\n")
extractorFile.write("App = \"App1\"")
extractorFile.write("\n")
for line in Extractor:
	extractorFile.write(line)
extractorFile.write("\n\n")
for line in F1:
	extractorFile.write(line)
extractorFile.close()
Extractor.close()
F1.close()
#Run the file to extract the objects
os.system("groovy -classpath lib/jpf.jar Extractor/extractorFile.groovy")


#Save the extracted methods and app2 in a same file to extract information
extractorFile = open("Extractor/extractorFile.groovy", "w+")
Extractor = open("Extractor/Extractor.groovy", "r")
F2 = open("Extractor/App2/App2.groovy", "r")

extractorFile.write("////////////////////\n")
extractorFile.write("@Field App\n")
extractorFile.write("App = \"App2\"")
extractorFile.write("\n")
for line in Extractor:
	extractorFile.write(line)
extractorFile.write("\n\n")
for line in F2:
	extractorFile.write(line)
#Run the file to extract the objects
extractorFile.close()
Extractor.close()
F2.close()
os.system("groovy -classpath lib/jpf.jar Extractor/extractorFile.groovy")


