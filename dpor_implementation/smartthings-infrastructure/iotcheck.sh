#!/bin/bash

# Function to print usage
print_usage()
{
	echo ""
	echo "Usage:	iotcheck.sh [options]"
	echo ""
	echo -e "\t-h\t(print this usage info)"
	echo ""
	echo -e "\t-e\texampleDPOR"
	echo -e "\t\texampleNoDPOR"
	echo ""
	echo -e "\t-d\tacfanheaterSwitches [-dpor]"
	echo -e "\t\talarms"
	echo -e "\t\tcameras"
	echo -e "\t\tcameraSwitches"
	echo -e "\t\tdimmers"
	echo -e "\t\thueLights"
	echo -e "\t\tlightSwitches"
	echo -e "\t\tlocks"
	echo -e "\t\tmusicPlayers"
	echo -e "\t\tnonHueLights"
	echo -e "\t\trelaySwitches"
	echo -e "\t\tspeeches"
	echo -e "\t\tswitches"
	echo -e "\t\tthermostats"
	echo -e "\t\tvalves"
	echo -e "\t\tventfanSwitches"
	echo ""
	echo -e "\t-g\tglobalStateVariables [-dpor]"
	echo ""
	exit 1
}

# Execute IoTCheck for examples
execute_iotcheck_example()
{
	if [[ $1 == 'exampleDPOR' ]]
	then
		cp ../jpf-core/main-locks.jpf ../jpf-core/main.jpf
		python3 ModelCheck_DPOR.py ../jpf-core/ ../logs/$1/ ../smartapps/ true false appLists/examples/exampleDPORAppList appLists/examples/exampleDPORAppList2
	elif [[ $1 == 'exampleNoDPOR' ]]
	then
		cp ../jpf-core/main-locks.jpf ../jpf-core/main.jpf
		python3 ModelCheck_DPOR.py ../jpf-core/ ../logs/$1/ ../smartapps/ false false appLists/examples/exampleDPORAppList appLists/examples/exampleDPORAppList2
	else
		print_usage	
	fi
}

# Execute IoTCheck for device interaction
execute_iotcheck_device()
{
	
	if [[ $1 == 'acfanheaterSwitches' ]] || 
	   [[ $1 == 'alarms' ]] ||
	   [[ $1 == 'cameras' ]] ||
	   [[ $1 == 'cameraSwitches' ]] ||
	   [[ $1 == 'dimmers' ]] ||
	   [[ $1 == 'hueLights' ]] ||
	   [[ $1 == 'lightSwitches' ]] ||
	   [[ $1 == 'locks' ]] ||
	   [[ $1 == 'musicPlayers' ]] ||
	   [[ $1 == 'nonHueLights' ]] ||
	   [[ $1 == 'relaySwitches' ]] ||
	   [[ $1 == 'speeches' ]] ||
	   [[ $1 == 'switches' ]] ||
	   [[ $1 == 'thermostats' ]] ||
	   [[ $1 == 'valves' ]] ||
	   [[ $1 == 'ventfanSwitches' ]]
	then
		cp ../jpf-core/main-$1.jpf ../jpf-core/main.jpf
		cp Extractor/Extractor_device-interaction.groovy Extractor/Extractor.groovy
		if [[ $2 == '-dpor' ]]
		then
			python3 ModelCheck_DPOR.py ../jpf-core/ ../logs/$1/ ../smartapps/ true true appLists/device-interaction/$1AppList appLists/device-interaction/$1AppList2
		else
			python3 ModelCheck.py ../jpf-core/ ../logs/$1/ ../smartapps/ appLists/device-interaction/$1AppList appLists/device-interaction/$1AppList2
		fi
	else
		print_usage
	fi
}

# Execute IoTCheck for global-variable interaction
execute_iotcheck_global()
{
	if [[ $1 == 'globalStateVariables' ]]
	then	
		cp ../jpf-core/main-$1.jpf ../jpf-core/main.jpf
		cp Extractor/Extractor_global-variable-interaction.groovy Extractor/Extractor.groovy
		if [[ $2 == '-dpor' ]]
		then
			python3 ModelCheck_DPOR.py ../jpf-core/ ../logs/$1/ ../smartapps/ true true appLists/global-state-variable-interaction/$1AppList appLists/global-state-variable-interaction/$1AppList2
		else 
			python3 ModelCheck.py ../jpf-core/ ../logs/$1/ ../smartapps/ appLists/global-state-variable-interaction/$1AppList appLists/global-state-variable-interaction/$1AppList2
		fi
	else
		print_usage
	fi
}

###
# Main body of script
###
# Get input argument and execute the right function
if [[ $1 == '-e' ]]
then
	execute_iotcheck_example $2
elif [[ $1 == '-d' ]]
then
	execute_iotcheck_device $2 $3

elif [[ $1 == '-g' ]]
then
	execute_iotcheck_global $2 $3
else
	# Print usage info if there is any mistake
	print_usage
fi
