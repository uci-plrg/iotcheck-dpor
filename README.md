# IoTCheck DPOR
This is the repository that contains the DPOR implementation for IoTCheck. Please read the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home) and [Github/Wiki](https://github.com/uci-plrg/iotcheck) and our IoTCheck DPOR implementation paper before using this repository.

**Stateful Dynamic Partial Order Reduction for Model Checking Event-Driven Applications that Do Not Terminate**
Rahmadi Trimananda, Weiyu Luo, Brian Demsky, Guoqing Harry Xu

## Getting Started
Our DPOR implementation runs on IoTCheck that was built on top of [Java Pathfinder (JPF)](https://github.com/javapathfinder). Thus, this repository contains the files that are necessary to enable DPOR when running IoTCheck. First, please [install IoTCheck as per these instructions](https://github.com/uci-plrg/iotcheck/blob/master/README.md#getting-started). We can use the [Vagrant-packaged IoTCheck](https://github.com/uci-plrg/iotcheck-vagrant) to handle all the required applications that enable IoTCheck or any Linux-based system/VM. IoTCheck was developed on Ubuntu 16.04.6 LTS (Xenial Xerus).

To understand the background, design, and implementation of IoTCheck, please read the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home) and the [IoTCheck paper](https://2020.esec-fse.org/details/fse-2020-papers/16/Understanding-and-Automatically-Detecting-Conflicting-Interactions-between-Smart-Home). 
To see IoTCheck in action, please [run the examples provided on the IoTCheck Github](https://github.com/uci-plrg/iotcheck/blob/master/README.md#examples) to make sure that your IoTCheck installation is good.

## Running the DPOR Implementation
After making sure that the IoTCheck installation is good, we can then use the files provided in this repository to run DPOR on IoTCheck. Our DPOR algorithm is basically implemented as a [JPF listener](https://github.com/javapathfinder/jpf-core/wiki/Listeners).
