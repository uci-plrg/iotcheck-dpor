#!/bin/bash

# Copy patches
cp dpor_implementation/jpf-core/moreStatistics ../iotcheck/jpf-core/
cp dpor_implementation/jpf-core/DPORStateReducerWithSummary.java ../iotcheck/jpf-core/src/main/gov/nasa/jpf/listener/
cp dpor_implementation/jpf-core/NumberChoiceFromList.java ../iotcheck/jpf-core/src/main/gov/nasa/jpf/vm/choice/NumberChoiceFromList.java
cp dpor_implementation/jpf-core/run.sh ../iotcheck/jpf-core/
cp dpor_implementation/smartthings-infrastructure/exampleDPORAppList ../iotcheck/smartthings-infrastructure/appLists/examples/
cp dpor_implementation/smartthings-infrastructure/exampleDPORAppList2 ../iotcheck/smartthings-infrastructure/appLists/examples/
cp dpor_implementation/smartthings-infrastructure/ExtractorScript.py ../iotcheck/smartthings-infrastructure/Extractor/ExtractorScript.py
cp dpor_implementation/smartthings-infrastructure/ModelCheck_DPOR.py ../iotcheck/smartthings-infrastructure/
cp dpor_implementation/smartthings-infrastructure/iotcheck.sh ../iotcheck/smartthings-infrastructure/iotcheck.sh

# Compile JPF
cd ../iotcheck/jpf-core/
./gradlew

# Log directory for DPOR examples
cd ..
mkdir logs/exampleDPOR
mkdir logs/exampleNoDPOR
cd ..
