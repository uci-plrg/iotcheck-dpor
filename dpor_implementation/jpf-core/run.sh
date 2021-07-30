#!/bin/bash
java -Xmx28g -XX:-UseCompressedOops -classpath build/jpf.jar gov.nasa.jpf.JPF +classpath=examples:lib/groovy-dateutil-2.5.7:lib/groovy-2.5.7:lib/groovy-json-2.5.7:../smartthings-infrastructure/bin/main/ +report.console.file=$1 $2
#java -Xmx20g -classpath build/jpf.jar gov.nasa.jpf.JPF +classpath=examples:lib/groovy-dateutil-2.5.7:lib/groovy-2.5.7:lib/groovy-json-2.5.7:../smartthings-infrastructure/bin/main/ +report.console.file=$1 $2
#java -Xmx40g -classpath build/jpf.jar gov.nasa.jpf.JPF +classpath=examples:lib/groovy-dateutil-2.5.7:lib/groovy-2.5.7:../smartthings-infrastructure/bin/main/ $1
#java -classpath build/jpf.jar gov.nasa.jpf.JPF +classpath=examples:examples/groovy-2.5.7:../smartthings-infrastructure/bin/main/ +listener=.listener.SearchStats $1
#java -classpath build/jpf.jar gov.nasa.jpf.JPF +classpath=examples:examples/groovy-2.5.7:../smartthings-infrastructure/bin/main/ $1
#java -Xmx1024m -classpath build/jpf.jar gov.nasa.jpf.JPF +classpath=examples:examples/groovy-2.5.7:../smartthings-infrastructure/bin/main/ $1
