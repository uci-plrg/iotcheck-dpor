# IoTCheck DPOR
This is the repository that contains the DPOR implementation for IoTCheck. Please read the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home) and [Github/Wiki](https://github.com/uci-plrg/iotcheck) and our IoTCheck DPOR implementation paper before using this repository.

**Stateful Dynamic Partial Order Reduction for Model Checking Event-Driven Applications that Do Not Terminate**
Rahmadi Trimananda, Weiyu Luo, Brian Demsky, Guoqing Harry Xu

## Getting Started
Our DPOR implementation runs on IoTCheck that was built on top of [Java Pathfinder (JPF)](https://github.com/javapathfinder). Thus, this repository contains the files that are necessary to enable DPOR when running IoTCheck. First, please [install IoTCheck as per these instructions](https://github.com/uci-plrg/iotcheck/blob/master/README.md#getting-started). We can use the [Vagrant-packaged IoTCheck](https://github.com/uci-plrg/iotcheck-vagrant) to handle all the required applications that enable IoTCheck or any Linux-based system/VM. IoTCheck was developed on Ubuntu 16.04.6 LTS (Xenial Xerus).

To understand the background, design, and implementation of IoTCheck, please read the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home) and the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home). 
To see IoTCheck in action, please [run the examples provided on the IoTCheck Github](https://github.com/uci-plrg/iotcheck/blob/master/README.md#examples) to make sure that your IoTCheck installation is good.

## Our DPOR Implementation
After making sure that the IoTCheck installation is good, we can then use the files provided in this repository to run DPOR on IoTCheck. Our DPOR algorithm is basically implemented as a [JPF listener](https://github.com/javapathfinder/jpf-core/wiki/Listeners).

The list of additional files provided in this repository to enable DPOR on the original IoTCheck implementation is the following.
### Files for jpf-core
1. **DPORStateReducerWithSummary.java:** this is the JPF listener that contains our DPOR implementation for IoTCheck---this version contains the traversal optimization described in Appendix D in our DPOR paper.
2. **NumberChoiceFromList.java:** this file replaces the original NumberChoiceFromList class implementation by JPF. The main difference is [these new lines of code](https://github.com/uci-plrg/iotcheck-dpor/blob/652f448e55f7423c2a7b3f663a3ba203f2f6a609/dpor_implementation/jpf-core/NumberChoiceFromList.java#L265) that allow the DPORStateReducerWithSummary class to manipulate [JPF's ChoiceGenerator class](https://github.com/javapathfinder/jpf-core/wiki/ChoiceGenerators). This way DPORStateReducerWithSummary can perform the DPOR permutations of orders of events.  
3. **moreStatistics:** this is an additional file into which DPORStateReducerWithSummary will write more statistics (i.e., state reduction mode, number of events, transitions, and unique transitions).
4. **run.sh:** this is a slightly different version of [the run script provided in the original IoTCheck](https://github.com/uci-plrg/iotcheck/wiki/IoTCheck-JPF#run-script)---the Java command line has an additional option `-XX:-UseCompressedOops`.
