# IoTCheck DPOR
This is the repository that contains the DPOR implementation for IoTCheck. Please read the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home) and [Github/Wiki](https://github.com/uci-plrg/iotcheck) and our IoTCheck DPOR implementation paper before using this repository.

**Stateful Dynamic Partial Order Reduction for Model Checking Event-Driven Applications that Do Not Terminate**
Rahmadi Trimananda, Weiyu Luo, Brian Demsky, Guoqing Harry Xu

## Getting Started
Our DPOR implementation runs on IoTCheck that was built on top of [Java Pathfinder (JPF)](https://github.com/javapathfinder). Thus, this repository contains the files that are necessary to enable DPOR when running IoTCheck. First, please [install IoTCheck as per these instructions](https://github.com/uci-plrg/iotcheck/blob/master/README.md#getting-started). For the purpose of this tutorial, let us create a directory called `my_iotcheck` and download IoTCheck into it.

To understand the background, design, and implementation of IoTCheck, please read the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home) and the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home). 
To see IoTCheck in action, please [run the examples provided on the IoTCheck Github](https://github.com/uci-plrg/iotcheck/blob/master/README.md#examples) to make sure that your IoTCheck installation is good.

## Our DPOR Implementation
After making sure that the IoTCheck installation is good, we can then use the files provided in this repository to run DPOR on IoTCheck. Our DPOR algorithm is basically implemented as a [JPF listener](https://github.com/javapathfinder/jpf-core/wiki/Listeners).

The list of additional files provided in this repository to enable DPOR on the original IoTCheck implementation is the following (see the [dpor_implementation folder](https://github.com/uci-plrg/iotcheck-dpor/tree/main/dpor_implementation)).

### Files for jpf-core
1. **DPORStateReducerWithSummary.java:** this is the JPF listener that contains our DPOR implementation for IoTCheck---this version contains the traversal optimization described in Appendix D in our DPOR paper.
2. **NumberChoiceFromList.java:** this file replaces the original NumberChoiceFromList class implementation by JPF. The main difference is [these new lines of code](https://github.com/uci-plrg/iotcheck-dpor/blob/652f448e55f7423c2a7b3f663a3ba203f2f6a609/dpor_implementation/jpf-core/NumberChoiceFromList.java#L265) that allow the DPORStateReducerWithSummary class to manipulate [JPF's ChoiceGenerator class](https://github.com/javapathfinder/jpf-core/wiki/ChoiceGenerators). This way DPORStateReducerWithSummary can perform the DPOR permutations of orders of events.  
3. **moreStatistics:** this is an additional file into which DPORStateReducerWithSummary will write more statistics (i.e., state reduction mode, number of events, transitions, and unique transitions).
4. **run.sh:** this is a slightly different version of [the run script provided in the original IoTCheck](https://github.com/uci-plrg/iotcheck/wiki/IoTCheck-JPF#run-script)---the Java command line has an additional option `-XX:-UseCompressedOops`.

### Files for smartthings-infrastructure
1. **ExtractorScript.py:** this version of ExtractorScript.py contains a more fine-grained implementation of event selection in [this while-loop](https://github.com/uci-plrg/iotcheck-dpor/blob/ed6d392ecf1162299ba012facb1be4ab4431d89d/dpor_implementation/smartthings-infrastructure/ExtractorScript.py#L397)---this is an improvement on [the original IoTCheck implementation](https://github.com/uci-plrg/iotcheck/wiki/IoTCheck-Infrastructure#iotcheck-configuration-and-preprocessing).
2. **ModelCheck_DPOR.py:** this is a different version of ModelCheck.py that is suitable for DPOR, e.g., our DPOR implementation is built on top of the [JPF's DFSearch strategy](https://github.com/javapathfinder/jpf-core/wiki/Search-Strategies), whereas [the original IoTCheck's ModelCheck.py](https://github.com/uci-plrg/iotcheck/wiki/IoTCheck-Infrastructure#iotcheck-configuration-and-preprocessing) runs both DFSearch and RandomHeuristic strategies to find conflicts.
3. **exampleDPORAppList and exampleDPORAppList2:** these lists facilitate [pair forming](https://github.com/uci-plrg/iotcheck#forming-pairs) to execute example cases to reproduce our experimental results.
4. **iotcheck.sh** this version of iotcheck.sh changes [the original iotcheck.sh](https://github.com/uci-plrg/iotcheck#experiments) by providing new command line options to run our DPOR examples---it also allows IoTCheck to run conflict detection (as per the original paper) with our DPOR implementation.

## Running the DPOR Implementation
In order to run our DPOR implementation, we need to execute the following steps. We assume that the original IoTCheck has been downloaded, installed, and tested to run correctly as per [the above instructions](https://github.com/uci-plrg/iotcheck-dpor#getting-started).

1. Download this repository into the same directory that contains the original IoTCheck (e.g., `iotcheck`). For example, we have `iotcheck` in a directory called `my_iotcheck`
```
my_iotcheck $ git clone https://github.com/uci-plrg/iotcheck-dpor
```

2. Run the [`setup.sh`](https://github.com/uci-plrg/iotcheck-dpor/blob/main/setup.sh) script to copy the DPOR-related files described above into their corresponding paths.
```
my_iotcheck $ ./setup.sh
```

3. We can then go into the `smartthings-infrastructure` folder and run the examples. First, let us run the new `iotcheck.sh` to see the new options.
```
my_iotcheck $ cd iotcheck/smartthings-infrastructure
my_iotcheck/iotcheck/smartthings-infrastructure $ ./iotcheck.sh

Usage:	iotcheck.sh [options]

	-h	(print this usage info)

	-e	exampleDPOR
		exampleNoDPOR

	-d	acfanheaterSwitches [-dpor]
		alarms
		cameras
		cameraSwitches
		dimmers
		hueLights
		lightSwitches
		locks
		musicPlayers
		nonHueLights
		relaySwitches
		speeches
		switches
		thermostats
		valves
		ventfanSwitches

	-g	globalStateVariables [-dpor]
```

4. First, let us run the `exampleDPOR` option. This will take about 30 minutes to around 1 hour depending on the machine's processing power.
```
my_iotcheck/iotcheck/smartthings-infrastructure $ ./iotcheck.sh -e exampleDPOR
```
This command will give us the log files shown in the `sample_logs/exampleDPOR` folder in this repository. The `logList` and the other `.log` files can be found in `my_iotcheck/iotcheck/logs/exampleDPOR`. The `moreStatistics` file can be found in `my_iotcheck/iotcheck/jpf-core`.

For the purpose of this example, we run our DPOR implementation for 8 pairs. The following 6 pairs can be found in Appendix Table 2.
```
Number 28: medicine-management-temp-motion--initial-state-event-sender
Number 29: medicine-management-temp-motion--initialstate-smart-app-v1.2.0
Number 30: medicine-management-temp-motion--unbuffered-event-sender
Number 39: medicine-management-contact-sensor--initial-state-event-sender
Number 40: medicine-management-contact-sensor--initialstate-smart-app-v1.2.0
Number 43: medicine-management-contact-sensor--unbuffered-event-sender
```
The following 2 pairs can be found in Appendix Table 3.
```
Number 42: medicine-management-temp-motion--circadian-daylight
Number 60: medicine-management-contact-sensor--circadian-daylight
```
Let us take a look at an example to reconcile the log files and the tables the report the experimental results in our paper. Let us open [the log file of medicine-management-temp-motion--initial-state-event-sender](https://github.com/uci-plrg/iotcheck-dpor/blob/main/sample_logs/exampleDPOR/medicine-management-temp-motion.groovy--initial-state-event-sender.groovy.log). We will see the following.
```
...
====================================================== statistics
elapsed time:       00:04:37
states:             new=939,visited=3613,backtracked=3893,end=0
search:             maxDepth=663,constraints=0
choice generators:  thread=1 (signal=0,lock=1,sharedRef=0,threadApi=0,reschedule=0), data=939
heap:               new=3046180,released=2745649,maxLive=132538,gcCycles=4552
instructions:       548545481
max memory:         9060MB
loaded code:        classes=856,methods=23516

====================================================== search finished: 7/28/21 8:01 AM
```
From this log file, we collect some information. In Table 2 number 28 under the column **With DPOR**, we will see `939` in column **States** that was taken from the above line `states:             new=939 ...`, and `275` in column **Time** that was taken from the above line `elapsed time:       00:04:37` written in seconds (the actual elapsed time may vary a bit for every run).
Next, let us also open [the `moreStatistics` file](https://github.com/uci-plrg/iotcheck-dpor/blob/main/sample_logs/exampleDPOR/moreStatistics) and focus on [the following lines](https://github.com/uci-plrg/iotcheck-dpor/blob/feff258204f90485a4fe49cea0c38d358a228b8e/sample_logs/exampleDPOR/moreStatistics#L30).
```
...
medicine-management-temp-motion.groovy--initial-state-event-sender.groovy
==> DEBUG: State reduction mode                : true
==> DEBUG: Number of events                    : 79
==> DEBUG: Number of transitions               : 2751
==> DEBUG: Number of unique transitions (DPOR) : 2277
...
```
Here, we collect some more information printed by our DPORStateReducerWithSummary class. In Table 2 number 28, we will see `79` in column **Evt.** (i.e., number of events) and under the column **With DPOR**, we will see under **Trans.** the number `2,277` which is the number of unique transitions for DPOR (please keep in mind that a transition can be revisited in our algorithm).
For the other 7 pairs, we can also check the numbers obtained in these files and reconcile them with the ones shown in Tables 2 and 3 in our paper.

5. Then, let us run the `exampleNoDPOR` option. This will take about 4 to 5 hours depending on the machine's processing power. The longer runtimes are caused by full state explorations for all 8 pairs when model-checked without our DPOR algorithm. Before running `iotcheck.sh`, we need to clean up the `moreStatistics` file.
```
my_iotcheck/iotcheck/smartthings-infrastructure $ echo "" > ../jpf-core/moreStatistics 
my_iotcheck/iotcheck/smartthings-infrastructure $ ./iotcheck.sh -e exampleNoDPOR
``` 
After this command line finishes executing, we can observe the log files. The `logList` and the other `.log` files can be found in `my_iotcheck/iotcheck/logs/exampleDPOR`. The `moreStatistics` file can be found in `my_iotcheck/iotcheck/jpf-core`. Finally, we can check the numbers obtained in these files and reconcile them with the ones shown in Tables 2 and 3 in our paper by following the description in step 4 above.

There are 2 exceptions for the `moreStatistics` file:
1. There will be no numbers below the names of 6 pairs because [they did not finish running (i.e., `JPF out of memory`)](https://github.com/uci-plrg/iotcheck-dpor/blob/main/sample_logs/exampleNoDPOR/medicine-management-contact-sensor.groovy--initial-state-event-sender.groovy.log).
2. It will show `0` for `Number of events` and `Number of unique transitions (DPOR)` for 2 pairs because they finished running, but we did not run the DPORStateReducerWithSummary class that is supposed to report those numbers. Thus, we only take the `Number of transitions` from this file and put it under the column **Without DPOR** (under **Trans.**), e.g., `10,500` for the pair `medicine-management-temp-motion--circadian-daylight` (number 42 in Table 3).

**NOTE:** The above examples exclude the conflict detection feature that the original IoTCheck performs for every pair. We can also run `iotcheck.sh` with our DPOR implementation for conflict detection. For example, we can try the following command.
```
my_iotcheck/iotcheck/smartthings-infrastructure $ ./iotcheck.sh -d	acfanheaterSwitches -dpor
```
This will give us the log files in `my_iotcheck/iotcheck/acfanheaterSwitches` reporting the conflict detection results.
