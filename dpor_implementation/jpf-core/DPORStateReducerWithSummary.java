/*
 * Copyright (C) 2014, United States Government, as represented by the
 * Administrator of the National Aeronautics and Space Administration.
 * All rights reserved.
 *
 * The Java Pathfinder core (jpf-core) platform is licensed under the
 * Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0.
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package gov.nasa.jpf.listener;

import gov.nasa.jpf.Config;
import gov.nasa.jpf.JPF;
import gov.nasa.jpf.ListenerAdapter;
import gov.nasa.jpf.jvm.bytecode.INVOKEINTERFACE;
import gov.nasa.jpf.jvm.bytecode.JVMFieldInstruction;
import gov.nasa.jpf.report.Publisher;
import gov.nasa.jpf.search.Search;
import gov.nasa.jpf.vm.*;
import gov.nasa.jpf.vm.bytecode.ReadInstruction;
import gov.nasa.jpf.vm.bytecode.WriteInstruction;
import gov.nasa.jpf.vm.choice.IntChoiceFromSet;
import gov.nasa.jpf.vm.choice.IntIntervalGenerator;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.*;
import java.util.logging.Logger;

/**
 * This a DPOR implementation for event-driven applications with loops that create cycles of state matching
 * In this new DPOR algorithm/implementation, each run is terminated iff:
 * - we find a state that matches a state in a previous run, or
 * - we have a matched state in the current run that consists of cycles that contain all choices/events.
 */
public class DPORStateReducerWithSummary extends ListenerAdapter {

  // Information printout fields for verbose mode
  private long startTime;
  private long timeout;
  private boolean verboseMode;
  private boolean stateReductionMode;
  private final PrintWriter out;
  private PrintWriter fileWriter;
  private String detail;
  private int depth;
  private int id;
  private Transition transition;

  // DPOR-related fields
  // Basic information
  private Integer[] choices;
  private Integer[] refChoices; // Second reference to a copy of choices (choices may be modified for fair scheduling)
  private int choiceCounter;
  private int maxEventChoice;
  // Data structure to track the events seen by each state to track cycles (containing all events) for termination
  private HashMap<Integer,Integer> currVisitedStates; // States visited in the current execution (maps to frequency)
  private HashSet<Integer> justVisitedStates;   // States just visited in the previous choice/event
  private HashSet<Integer> prevVisitedStates;   // States visited in the previous execution
  private HashSet<ClassInfo> nonRelevantClasses;// Class info objects of non-relevant classes
  private HashSet<FieldInfo> nonRelevantFields; // Field info objects of non-relevant fields
  private HashSet<FieldInfo> relevantFields;    // Field info objects of relevant fields
  private HashMap<Integer, HashSet<Integer>> stateToEventMap;       // Map state ID to events
  // Data structure to analyze field Read/Write accesses and conflicts
  private HashMap<Integer, LinkedList<BacktrackExecution>> backtrackMap;  // Track created backtracking points
  private PriorityQueue<Integer> backtrackStateQ;                 // Heap that returns the latest state
  private Execution currentExecution;                             // Holds the information about the current execution
  private HashMap<Integer, HashSet<Integer>> doneBacktrackMap;    // Record state ID and trace already constructed
  private MainSummary mainSummary;                                // Main summary (M) for state ID, event, and R/W set
  private HashMap<Integer, PredecessorInfo> stateToPredInfo;      // Predecessor info indexed by state ID
  private HashMap<Integer, RestorableVMState> restorableStateMap; // Maps state IDs to the restorable state object
  private RGraph rGraph;                                          // R-Graph for past executions

  // Boolean states
  private boolean isBooleanCGFlipped;
  private boolean isEndOfExecution;
  private boolean isNotCheckedForEventsYet;

  // Statistics
  private int numOfTransitions;
  private HashMap<Integer, HashSet<Integer>> stateToUniqueTransMap;

  public DPORStateReducerWithSummary(Config config, JPF jpf) {
    verboseMode = config.getBoolean("printout_state_transition", false);
    stateReductionMode = config.getBoolean("activate_state_reduction", true);
    if (verboseMode) {
      out = new PrintWriter(System.out, true);
    } else {
      out = null;
    }
    String outputFile = config.getString("file_output");
    if (!outputFile.isEmpty()) {
      try {
        fileWriter = new PrintWriter(new FileWriter(outputFile, true), true);
      } catch (IOException e) {
      }
    }
    isBooleanCGFlipped = false;
    isNotCheckedForEventsYet = true;
    mainSummary = new MainSummary();
    numOfTransitions = 0;
    nonRelevantClasses = new HashSet<>();
    nonRelevantFields = new HashSet<>();
    relevantFields = new HashSet<>();
    restorableStateMap = new HashMap<>();
    stateToPredInfo = new HashMap<>();
    stateToUniqueTransMap = new HashMap<>();
    initializeStatesVariables();

    // Timeout input from config is in minutes, so we need to convert into millis
    timeout = config.getInt("timeout", 0) * 60 * 1000;
    startTime = System.currentTimeMillis();
  }

  @Override
  public void stateRestored(Search search) {
    if (verboseMode) {
      id = search.getStateId();
      depth = search.getDepth();
      transition = search.getTransition();
      detail = null;
      out.println("\n==> DEBUG: The state is restored to state with id: " + id + " -- Transition: " + transition +
              " and depth: " + depth + "\n");
    }
  }

  @Override
  public void searchStarted(Search search) {
    if (verboseMode) {
      out.println("\n==> DEBUG: ----------------------------------- search started" + "\n");
    }
  }

  @Override
  public void stateAdvanced(Search search) {
    if (verboseMode) {
      id = search.getStateId();
      depth = search.getDepth();
      transition = search.getTransition();
      if (search.isNewState()) {
        detail = "new";
      } else {
        detail = "visited";
      }

      if (search.isEndState()) {
        out.println("\n==> DEBUG: This is the last state!\n");
        detail += " end";
      }
      out.println("\n==> DEBUG: The state is forwarded to state with id: " + id + " with depth: " + depth +
              " which is " + detail + " Transition: " + transition + "\n");
    }
    if (stateReductionMode) {
      updateStateInfo(search);
    }
  }

  @Override
  public void stateBacktracked(Search search) {
    if (verboseMode) {
      id = search.getStateId();
      depth = search.getDepth();
      transition = search.getTransition();
      detail = null;

      out.println("\n==> DEBUG: The state is backtracked to state with id: " + id + " -- Transition: " + transition +
              " and depth: " + depth + "\n");
    }
    if (stateReductionMode) {
      updateStateInfo(search);
    }
  }

  static Logger log = JPF.getLogger("report");

  @Override
  public void searchFinished(Search search) {
    if (verboseMode) {
      int summaryOfUniqueTransitions = summarizeUniqueTransitions();
      out.println("\n==> DEBUG: ----------------------------------- search finished");
      out.println("\n==> DEBUG: State reduction mode                : " + stateReductionMode);
      if (choices != null) {
        out.println("\n==> DEBUG: Number of events                    : " + choices.length);
      } else {
        // Without DPOR we don't have choices being assigned with a CG
        out.println("\n==> DEBUG: Number of events                    : 0");
      }
      out.println("\n==> DEBUG: Number of transitions               : " + numOfTransitions);
      out.println("\n==> DEBUG: Number of unique transitions (DPOR) : " + summaryOfUniqueTransitions);
      out.println("\n==> DEBUG: ----------------------------------- search finished" + "\n");

      fileWriter.println("==> DEBUG: State reduction mode                : " + stateReductionMode);
      if (choices != null) {
        fileWriter.println("==> DEBUG: Number of events                    : " + choices.length);
      } else {
        // Without DPOR we don't have choices being assigned with a CG
        fileWriter.println("==> DEBUG: Number of events                    : 0");
      }
      fileWriter.println("==> DEBUG: Number of transitions               : " + numOfTransitions);
      fileWriter.println("==> DEBUG: Number of unique transitions (DPOR) : " + summaryOfUniqueTransitions);
      fileWriter.println();
      fileWriter.close();
    }
  }

  @Override
  public void choiceGeneratorRegistered(VM vm, ChoiceGenerator<?> nextCG, ThreadInfo currentThread, Instruction executedInstruction) {
    if (isNotCheckedForEventsYet) {
      // Check if this benchmark has no events
      if (nextCG instanceof IntChoiceFromSet) {
        IntChoiceFromSet icsCG = (IntChoiceFromSet) nextCG;
        Integer[] cgChoices = icsCG.getAllChoices();
        if (cgChoices.length == 2 && cgChoices[0] == 0 && cgChoices[1] == -1) {
          // This means the benchmark only has 2 choices, i.e., 0 and -1 which means that it has no events
          stateReductionMode = false;
        }
        isNotCheckedForEventsYet = false;
      }
    }
    if (stateReductionMode) {
      // Initialize with necessary information from the CG
      if (nextCG instanceof IntChoiceFromSet) {
        IntChoiceFromSet icsCG = (IntChoiceFromSet) nextCG;
        // Tell JPF that we are performing DPOR
        icsCG.setDpor();
        if (!isEndOfExecution) {
          // Check if CG has been initialized, otherwise initialize it
          Integer[] cgChoices = icsCG.getAllChoices();
          // Record the events (from choices)
          if (choices == null) {
            choices = cgChoices;
            // Make a copy of choices as reference
            refChoices = copyChoices(choices);
            // Record the max event choice (the last element of the choice array)
            maxEventChoice = choices[choices.length - 1];
          }
          icsCG.setNewValues(choices);
          icsCG.reset();
          // Use a modulo since choiceCounter is going to keep increasing
          int choiceIndex = choiceCounter % choices.length;
          icsCG.advance(choices[choiceIndex]);
        } else {
          // Set done all CGs while transitioning to a new execution
          icsCG.setDone();
        }
      }
    }
  }

  @Override
  public void choiceGeneratorAdvanced(VM vm, ChoiceGenerator<?> currentCG) {
    if (stateReductionMode) {
      // Check the boolean CG and if it is flipped, we are resetting the analysis
      if (currentCG instanceof BooleanChoiceGenerator) {
        if (!isBooleanCGFlipped) {
          isBooleanCGFlipped = true;
        } else {
          // Allocate new objects for data structure when the boolean is flipped from "false" to "true"
          initializeStatesVariables();
        }
      }
      // Check every choice generated and ensure fair scheduling!
      if (currentCG instanceof IntChoiceFromSet) {
        IntChoiceFromSet icsCG = (IntChoiceFromSet) currentCG;
        // If this is a new CG then we need to update data structures
        resetStatesForNewExecution(icsCG, vm);
        // If we don't see a fair scheduling of events/choices then we have to enforce it
        ensureFairSchedulingAndSetupTransition(icsCG, vm);
        // Update backtrack set of an executed event (transition): one transition before this one
        updateBacktrackSet(currentExecution, choiceCounter - 1);
        // Explore the next backtrack point:
        // 1) if we have seen this state or this state contains cycles that involve all events, and
        // 2) after the current CG is advanced at least once
        if (choiceCounter > 0 && terminateCurrentExecution()) {
          exploreNextBacktrackPoints(vm, icsCG);
        } else {
          // We only count IntChoiceFromSet CGs
          numOfTransitions++;
          countUniqueTransitions(vm.getStateId(), icsCG.getNextChoice());
        }
        // Map state to event
        mapStateToEvent(icsCG.getNextChoice());
        justVisitedStates.clear();
        choiceCounter++;
      }
    } else {
      // We only count IntChoiceFromSet CGs
      if (currentCG instanceof IntChoiceFromSet) {
        numOfTransitions++;
      }
    }
  }

  @Override
  public void instructionExecuted(VM vm, ThreadInfo ti, Instruction nextInsn, Instruction executedInsn) {
    // Check the timeout
    if (timeout > 0) {
      if (System.currentTimeMillis() - startTime > timeout) {
        StringBuilder sbTimeOut = new StringBuilder();
        sbTimeOut.append("Execution timeout: " + (timeout / (60 * 1000)) + " minutes have passed!");
        Instruction nextIns = ti.createAndThrowException("java.lang.RuntimeException", sbTimeOut.toString());
        ti.setNextPC(nextIns);
      }
    }

    if (stateReductionMode) {
      if (!isEndOfExecution) {
        // Has to be initialized and it is a integer CG
        ChoiceGenerator<?> cg = vm.getChoiceGenerator();
        if (cg instanceof IntChoiceFromSet || cg instanceof IntIntervalGenerator) {
          int currentChoice = choiceCounter - 1;  // Accumulative choice w.r.t the current trace
          if (currentChoice < 0) { // If choice is -1 then skip
            return;
          }
          currentChoice = checkAndAdjustChoice(currentChoice, vm);
          // Record accesses from executed instructions
          if (executedInsn instanceof JVMFieldInstruction) {
            // We don't care about libraries
            if (!isFieldExcluded(executedInsn)) {
              analyzeReadWriteAccesses(executedInsn, currentChoice);
            }
          } else if (executedInsn instanceof INVOKEINTERFACE) {
            // Handle the read/write accesses that occur through iterators
            analyzeReadWriteAccesses(executedInsn, ti, currentChoice);
          }
        }
      }
    }
  }


  // == HELPERS

  // -- INNER CLASSES

  // This class compactly stores backtrack execution:
  // 1) backtrack choice list, and
  // 2) first backtrack point (linking with predecessor execution)
  private class BacktrackExecution {
    private Integer[] choiceList;
    private TransitionEvent firstTransition;

    public BacktrackExecution(Integer[] choList, TransitionEvent fTransition) {
      choiceList = choList;
      firstTransition = fTransition;
    }

    public Integer[] getChoiceList() {
      return choiceList;
    }

    public TransitionEvent getFirstTransition() {
      return firstTransition;
    }
  }

  // This class stores a representation of an execution
  // TODO: We can modify this class to implement some optimization (e.g., clock-vector)
  // TODO: We basically need to keep track of:
  // TODO:    (1) last read/write access to each memory location
  // TODO:    (2) last state with two or more incoming events/transitions
  private class Execution {
    private HashMap<IntChoiceFromSet, Integer> cgToChoiceMap;   // Map between CG to choice numbers for O(1) access
    private ArrayList<TransitionEvent> executionTrace;          // The BacktrackPoint objects of this execution
    private boolean isNew;                                      // Track if this is the first time it is accessed
    private HashMap<Integer, ReadWriteSet> readWriteFieldsMap;  // Record fields that are accessed

    public Execution() {
      cgToChoiceMap = new HashMap<>();
      executionTrace = new ArrayList<>();
      isNew = true;
      readWriteFieldsMap = new HashMap<>();
    }

    public void addTransition(TransitionEvent newBacktrackPoint) {
      executionTrace.add(newBacktrackPoint);
    }

    public void clearCGToChoiceMap() {
      cgToChoiceMap = null;
    }

    public int getChoiceFromCG(IntChoiceFromSet icsCG) {
      return cgToChoiceMap.get(icsCG);
    }

    public ArrayList<TransitionEvent> getExecutionTrace() {
      return executionTrace;
    }

    public TransitionEvent getFirstTransition() {
      return executionTrace.get(0);
    }

    public TransitionEvent getLastTransition() {
      return executionTrace.get(executionTrace.size() - 1);
    }

    public HashMap<Integer, ReadWriteSet> getReadWriteFieldsMap() {
      return readWriteFieldsMap;
    }

    public boolean isNew() {
      if (isNew) {
        // Right after this is accessed, it is no longer new
        isNew = false;
        return true;
      }
      return false;
    }

    public void mapCGToChoice(IntChoiceFromSet icsCG, int choice) {
      cgToChoiceMap.put(icsCG, choice);
    }
  }

  // This class compactly stores a predecessor
  // 1) a predecessor execution
  // 2) the predecessor choice in that predecessor execution
  private class Predecessor {
    private int choice;           // Predecessor choice
    private Execution execution;  // Predecessor execution

    public Predecessor(int predChoice, Execution predExec) {
      choice = predChoice;
      execution = predExec;
    }

    public int getChoice() {
      return choice;
    }

    public Execution getExecution() {
      return execution;
    }
  }

  // This class represents a R-Graph (in the paper it is a state transition graph R)
  // This implementation stores reachable transitions from and connects with past executions
  private class RGraph {
    private int hiStateId;                                     // Maximum state Id
    private HashMap<Integer, HashSet<TransitionEvent>> graph;  // Reachable transitions from past executions

    public RGraph() {
      hiStateId = 0;
      graph = new HashMap<>();
    }

    public void addReachableTransition(int stateId, TransitionEvent transition) {
      HashSet<TransitionEvent> transitionSet;
      if (graph.containsKey(stateId)) {
        transitionSet = graph.get(stateId);
      } else {
        transitionSet = new HashSet<>();
        graph.put(stateId, transitionSet);
      }
      // Insert into the set if it does not contain it yet
      if (!transitionSet.contains(transition)) {
        transitionSet.add(transition);
      }
      // Update highest state ID
      if (hiStateId < stateId) {
        hiStateId = stateId;
      }
    }

    public HashSet<TransitionEvent> getReachableTransitionsAtState(int stateId) {
      if (!graph.containsKey(stateId)) {
        // This is a loop from a transition to itself, so just return the current transition
        HashSet<TransitionEvent> transitionSet = new HashSet<>();
        transitionSet.add(currentExecution.getLastTransition());
        return transitionSet;
      }
      return graph.get(stateId);
    }

    public HashSet<TransitionEvent> getReachableTransitions(int stateId) {
      HashSet<TransitionEvent> reachableTransitions = new HashSet<>();
      // All transitions from states higher than the given state ID (until the highest state ID) are reachable
      for(int stId = stateId; stId <= hiStateId; stId++) {
        // We might encounter state IDs from the first round of Boolean CG
        // The second round of Boolean CG should consider these new states
        if (graph.containsKey(stId)) {
          reachableTransitions.addAll(graph.get(stId));
        }
      }
      return reachableTransitions;
    }
  }

  // This class compactly stores Read and Write field sets
  // We store the field name and its object ID
  // Sharing the same field means the same field name and object ID
  private class ReadWriteSet {
    private HashMap<String, Integer> readMap;
    private HashMap<String, Integer> writeMap;

    public ReadWriteSet() {
      readMap = new HashMap<>();
      writeMap = new HashMap<>();
    }

    public void addReadField(String field, int objectId) {
      readMap.put(field, objectId);
    }

    public void addWriteField(String field, int objectId) {
      writeMap.put(field, objectId);
    }

    public void removeReadField(String field) {
      readMap.remove(field);
    }

    public void removeWriteField(String field) {
      writeMap.remove(field);
    }

    public boolean isEmpty() {
      return readMap.isEmpty() && writeMap.isEmpty();
    }

    public ReadWriteSet getCopy() {
      ReadWriteSet copyRWSet = new ReadWriteSet();
      // Copy the maps in the set into the new object copy
      copyRWSet.setReadMap(new HashMap<>(this.getReadMap()));
      copyRWSet.setWriteMap(new HashMap<>(this.getWriteMap()));
      return copyRWSet;
    }

    public Set<String> getReadSet() {
      return readMap.keySet();
    }

    public Set<String> getWriteSet() {
      return writeMap.keySet();
    }

    public boolean readFieldExists(String field) {
      return readMap.containsKey(field);
    }

    public boolean writeFieldExists(String field) {
      return writeMap.containsKey(field);
    }

    public int readFieldObjectId(String field) {
      return readMap.get(field);
    }

    public int writeFieldObjectId(String field) {
      return writeMap.get(field);
    }

    private HashMap<String, Integer> getReadMap() {
      return readMap;
    }

    private HashMap<String, Integer> getWriteMap() {
      return writeMap;
    }

    private void setReadMap(HashMap<String, Integer> rMap) {
      readMap = rMap;
    }

    private void setWriteMap(HashMap<String, Integer> wMap) {
      writeMap = wMap;
    }
  }

  // This class is a representation of a state.
  // It stores the predecessors to a state.
  // TODO: We also have stateToEventMap, restorableStateMap, and doneBacktrackMap that has state Id as HashMap key.
  private class PredecessorInfo {
    private HashSet<Predecessor> predecessors;  // Maps incoming events/transitions (execution and choice)
    private HashMap<Execution, HashSet<Integer>> recordedPredecessors;
                                                // Memorize event and choice number to not record them twice

    public PredecessorInfo() {
      predecessors = new HashSet<>();
      recordedPredecessors = new HashMap<>();
    }

    public HashSet<Predecessor> getPredecessors() {
      return predecessors;
    }

    private boolean isRecordedPredecessor(Execution execution, int choice) {
      // See if we have recorded this predecessor earlier
      HashSet<Integer> recordedChoices;
      if (recordedPredecessors.containsKey(execution)) {
        recordedChoices = recordedPredecessors.get(execution);
        if (recordedChoices.contains(choice)) {
          return true;
        }
      } else {
        recordedChoices = new HashSet<>();
        recordedPredecessors.put(execution, recordedChoices);
      }
      // Record the choice if we haven't seen it
      recordedChoices.add(choice);

      return false;
    }

    public void recordPredecessor(Execution execution, int choice) {
      if (!isRecordedPredecessor(execution, choice)) {
        predecessors.add(new Predecessor(choice, execution));
      }
    }
  }

  // This class compactly stores transitions:
  // 1) CG,
  // 2) state ID,
  // 3) choice,
  // 4) predecessors (for backward DFS).
  private class TransitionEvent {
    private int choice;                        // Choice chosen at this transition
    private int choiceCounter;                 // Choice counter at this transition
    private Execution execution;               // The execution where this transition belongs
    private int stateId;                       // State at this transition
    private IntChoiceFromSet transitionCG;     // CG at this transition

    public TransitionEvent() {
      choice = 0;
      choiceCounter = 0;
      execution = null;
      stateId = 0;
      transitionCG = null;
    }

    public int getChoice() {
      return choice;
    }

    public int getChoiceCounter() {
      return choiceCounter;
    }

    public Execution getExecution() {
      return execution;
    }

    public int getStateId() {
      return stateId;
    }

    public IntChoiceFromSet getTransitionCG() { return transitionCG; }

    public void setChoice(int cho) {
      choice = cho;
    }

    public void setChoiceCounter(int choCounter) {
      choiceCounter = choCounter;
    }

    public void setExecution(Execution exec) {
      execution = exec;
    }

    public void setStateId(int stId) {
      stateId = stId;
    }

    public void setTransitionCG(IntChoiceFromSet cg) {
      transitionCG = cg;
    }
  }

  // -- PRIVATE CLASSES RELATED TO SUMMARY
  // This class stores the main summary of states
  // 1) Main mapping between state ID and state summary
  // 2) State summary is a mapping between events (i.e., event choices) and their respective R/W sets
  private class MainSummary {
    private HashMap<Integer, HashMap<Integer, ReadWriteSet>> mainSummary;

    public MainSummary() {
      mainSummary = new HashMap<>();
    }

    public Set<Integer> getEventChoicesAtStateId(int stateId) {
      HashMap<Integer, ReadWriteSet> stateSummary = mainSummary.get(stateId);
      // Return a new set since this might get updated concurrently
      return new HashSet<>(stateSummary.keySet());
    }

    public ReadWriteSet getRWSetForEventChoiceAtState(int eventChoice, int stateId) {
      HashMap<Integer, ReadWriteSet> stateSummary = mainSummary.get(stateId);
      return stateSummary.get(eventChoice);
    }

    public Set<Integer> getStateIds() {
      return mainSummary.keySet();
    }

    private ReadWriteSet performUnion(ReadWriteSet recordedRWSet, ReadWriteSet rwSet) {
      // Combine the same write accesses and record in the recordedRWSet
      HashMap<String, Integer> recordedWriteMap = recordedRWSet.getWriteMap();
      HashMap<String, Integer> writeMap = rwSet.getWriteMap();
      for(Map.Entry<String, Integer> entry : recordedWriteMap.entrySet()) {
        String writeField = entry.getKey();
        // Remove the entry from rwSet if both field and object ID are the same
        if (writeMap.containsKey(writeField) &&
                (writeMap.get(writeField).equals(recordedWriteMap.get(writeField)))) {
          writeMap.remove(writeField);
        }
      }
      // Then add the rest (fields in rwSet but not in recordedRWSet)
      // into the recorded map because these will be traversed
      recordedWriteMap.putAll(writeMap);
      // Combine the same read accesses and record in the recordedRWSet
      HashMap<String, Integer> recordedReadMap = recordedRWSet.getReadMap();
      HashMap<String, Integer> readMap = rwSet.getReadMap();
      for(Map.Entry<String, Integer> entry : recordedReadMap.entrySet()) {
        String readField = entry.getKey();
        // Remove the entry from rwSet if both field and object ID are the same
        if (readMap.containsKey(readField) &&
                (readMap.get(readField).equals(recordedReadMap.get(readField)))) {
          readMap.remove(readField);
        }
      }
      // Then add the rest (fields in rwSet but not in recordedRWSet)
      // into the recorded map because these will be traversed
      recordedReadMap.putAll(readMap);

      return rwSet;
    }

    public ReadWriteSet updateStateSummary(int stateId, int eventChoice, ReadWriteSet rwSet) {
      // If the state Id has not existed, insert the StateSummary object
      // If the state Id has existed, find the event choice:
      // 1) If the event choice has not existed, insert the ReadWriteSet object
      // 2) If the event choice has existed, perform union between the two ReadWriteSet objects
      if (!rwSet.isEmpty()) {
        HashMap<Integer, ReadWriteSet> stateSummary;
        if (!mainSummary.containsKey(stateId)) {
          stateSummary = new HashMap<>();
          stateSummary.put(eventChoice, rwSet.getCopy());
          mainSummary.put(stateId, stateSummary);
        } else {
          stateSummary = mainSummary.get(stateId);
          if (!stateSummary.containsKey(eventChoice)) {
            stateSummary.put(eventChoice, rwSet.getCopy());
          } else {
            rwSet = performUnion(stateSummary.get(eventChoice), rwSet);
          }
        }
      }
      return rwSet;
    }
  }

  // -- CONSTANTS
  private final static String DO_CALL_METHOD = "doCall";
  // We exclude fields that come from libraries (Java and Groovy), and also the infrastructure
  private final static String[] EXCLUDED_FIELDS_CONTAINS_LIST = {"_closure"};
  private final static String[] EXCLUDED_FIELDS_ENDS_WITH_LIST =
          // Groovy library created fields
          {"stMC", "callSiteArray", "metaClass", "staticClassInfo", "__constructor__",
          // Infrastructure
          "sendEvent", "Object", "reference", "location", "app", "state", "log", "functionList", "objectList",
          "eventList", "valueList", "settings", "printToConsole", "app1", "app2"};
  private final static String[] EXCLUDED_FIELDS_STARTS_WITH_LIST =
          // Java and Groovy libraries
          { "java", "org", "sun", "com", "gov", "groovy"};
  private final static String[] EXCLUDED_FIELDS_READ_WRITE_INSTRUCTIONS_STARTS_WITH_LIST = {"Event"};
  private final static String GET_PROPERTY_METHOD =
          "invokeinterface org.codehaus.groovy.runtime.callsite.CallSite.callGetProperty";
  private final static String GROOVY_CALLSITE_LIB = "org.codehaus.groovy.runtime.callsite";
  private final static String JAVA_INTEGER = "int";
  private final static String JAVA_STRING_LIB = "java.lang.String";

  // -- FUNCTIONS
  private Integer[] copyChoices(Integer[] choicesToCopy) {

    Integer[] copyOfChoices = new Integer[choicesToCopy.length];
    System.arraycopy(choicesToCopy, 0, copyOfChoices, 0, choicesToCopy.length);
    return copyOfChoices;
  }

  private void ensureFairSchedulingAndSetupTransition(IntChoiceFromSet icsCG, VM vm) {
    // Check the next choice and if the value is not the same as the expected then force the expected value
    int choiceIndex = choiceCounter % refChoices.length;
    int nextChoice = icsCG.getNextChoice();
    if (refChoices[choiceIndex] != nextChoice) {
      int expectedChoice = refChoices[choiceIndex];
      int currCGIndex = icsCG.getNextChoiceIndex();
      if ((currCGIndex >= 0) && (currCGIndex < refChoices.length)) {
        icsCG.setChoice(currCGIndex, expectedChoice);
      }
    }
    // Get state ID and associate it with this transition
    int stateId = vm.getStateId();
    TransitionEvent transition = setupTransition(icsCG, stateId, choiceIndex);
    // Add new transition to the current execution and map it in R-Graph
    for (Integer stId : justVisitedStates) {  // Map this transition to all the previously passed states
      rGraph.addReachableTransition(stId, transition);
    }
    currentExecution.mapCGToChoice(icsCG, choiceCounter);
    // Store restorable state object for this state (always store the latest)
    if (!restorableStateMap.containsKey(stateId)) {
      RestorableVMState restorableState = vm.getRestorableState();
      restorableStateMap.put(stateId, restorableState);
    }
  }

  private TransitionEvent setupTransition(IntChoiceFromSet icsCG, int stateId, int choiceIndex) {
    // Get a new transition
    TransitionEvent transition;
    if (currentExecution.isNew()) {
      // We need to handle the first transition differently because this has a predecessor execution
      transition = currentExecution.getFirstTransition();
    } else {
      transition = new TransitionEvent();
      currentExecution.addTransition(transition);
      addPredecessors(stateId);
    }
    transition.setExecution(currentExecution);
    transition.setTransitionCG(icsCG);
    transition.setStateId(stateId);
    transition.setChoice(refChoices[choiceIndex]);
    transition.setChoiceCounter(choiceCounter);

    return transition;
  }

  // --- Functions related to statistics counting
  // Count unique state IDs
  private void countUniqueTransitions(int stateId, int nextChoiceValue) {
    HashSet<Integer> events;
    // Get the set of events
    if (!stateToUniqueTransMap.containsKey(stateId)) {
      events = new HashSet<>();
      stateToUniqueTransMap.put(stateId, events);
    } else {
      events = stateToUniqueTransMap.get(stateId);
    }
    // Insert the event
    if (!events.contains(nextChoiceValue)) {
      events.add(nextChoiceValue);
    }
  }

  // Summarize unique state IDs
  private int summarizeUniqueTransitions() {
    // Just count the set size of each of entry map and sum them up
    int numOfUniqueTransitions = 0;
    for (Map.Entry<Integer,HashSet<Integer>> entry : stateToUniqueTransMap.entrySet()) {
      numOfUniqueTransitions = numOfUniqueTransitions + entry.getValue().size();
    }

    return numOfUniqueTransitions;
  }

  // --- Functions related to cycle detection and reachability graph

  // Detect cycles in the current execution/trace
  // We terminate the execution iff:
  // (1) the state has been visited in the current execution
  // (2) the state has one or more cycles that involve all the events
  // With simple approach we only need to check for a re-visited state.
  // Basically, we have to check that we have executed all events between two occurrences of such state.
  private boolean completeFullCycle(int stId) {
    // False if the state ID hasn't been recorded
    if (!stateToEventMap.containsKey(stId)) {
      return false;
    }
    HashSet<Integer> visitedEvents = stateToEventMap.get(stId);
    // Check if this set contains all the event choices
    // If not then this is not the terminating condition
    for(int i=0; i<=maxEventChoice; i++) {
      if (!visitedEvents.contains(i)) {
        return false;
      }
    }
    return true;
  }

  private void initializeStatesVariables() {
    // DPOR-related
    choices = null;
    refChoices = null;
    choiceCounter = 0;
    maxEventChoice = 0;
    // Cycle tracking
    if (!isBooleanCGFlipped) {
      currVisitedStates = new HashMap<>();
      justVisitedStates = new HashSet<>();
      prevVisitedStates = new HashSet<>();
      stateToEventMap = new HashMap<>();
    } else {
      currVisitedStates.clear();
      justVisitedStates.clear();
      prevVisitedStates.clear();
      stateToEventMap.clear();
    }
    // Backtracking
    if (!isBooleanCGFlipped) {
      backtrackMap = new HashMap<>();
    } else {
      backtrackMap.clear();
    }
    backtrackStateQ = new PriorityQueue<>(Collections.reverseOrder());
    currentExecution = new Execution();
    currentExecution.addTransition(new TransitionEvent()); // Always start with 1 backtrack point
    if (!isBooleanCGFlipped) {
      doneBacktrackMap = new HashMap<>();
    } else {
      doneBacktrackMap.clear();
    }
    rGraph = new RGraph();
    // Booleans
    isEndOfExecution = false;
  }

  private void mapStateToEvent(int nextChoiceValue) {
    // Update all states with this event/choice
    // This means that all past states now see this transition
    Set<Integer> stateSet = stateToEventMap.keySet();
    for(Integer stateId : stateSet) {
      HashSet<Integer> eventSet = stateToEventMap.get(stateId);
      eventSet.add(nextChoiceValue);
    }
  }

  private boolean terminateCurrentExecution() {
    // We need to check all the states that have just been visited
    // Often a transition (choice/event) can result into forwarding/backtracking to a number of states
    boolean terminate = false;
    Set<Integer> mainStateIds = mainSummary.getStateIds();
    for(Integer stateId : justVisitedStates) {
      // We exclude states that are produced by other CGs that are not integer CG
      // When we encounter these states, then we should also encounter the corresponding integer CG state ID
      if (mainStateIds.contains(stateId)) {
        // We perform updates on backtrack sets for every
        if (prevVisitedStates.contains(stateId) || completeFullCycle(stateId)) {
          updateBacktrackSetsFromGraph(stateId, currentExecution, choiceCounter - 1);
          terminate = true;
        }
        // If frequency > 1 then this means we have visited this stateId more than once in the current execution
        if (currVisitedStates.containsKey(stateId) && currVisitedStates.get(stateId) > 1) {
          updateBacktrackSetsFromGraph(stateId, currentExecution, choiceCounter - 1);
        }
      }
    }
    return terminate;
  }

  private void updateStateInfo(Search search) {
    // Update the state variables
    int stateId = search.getStateId();
    // Insert state ID into the map if it is new
    if (!stateToEventMap.containsKey(stateId)) {
      HashSet<Integer> eventSet = new HashSet<>();
      stateToEventMap.put(stateId, eventSet);
    }
    addPredecessorToRevisitedState(stateId);
    justVisitedStates.add(stateId);
    if (!prevVisitedStates.contains(stateId)) {
      // It is a currently visited states if the state has not been seen in previous executions
      int frequency = 0;
      if (currVisitedStates.containsKey(stateId)) {
        frequency = currVisitedStates.get(stateId);
      }
      currVisitedStates.put(stateId, frequency + 1);  // Increment frequency counter
    }
  }

  // --- Functions related to Read/Write access analysis on shared fields

  private void addNewBacktrackPoint(int stateId, Integer[] newChoiceList, TransitionEvent conflictTransition) {
    // Insert backtrack point to the right state ID
    LinkedList<BacktrackExecution> backtrackExecList;
    if (backtrackMap.containsKey(stateId)) {
      backtrackExecList = backtrackMap.get(stateId);
    } else {
      backtrackExecList = new LinkedList<>();
      backtrackMap.put(stateId, backtrackExecList);
    }
    // Add the new backtrack execution object
    TransitionEvent backtrackTransition = new TransitionEvent();
    backtrackExecList.addFirst(new BacktrackExecution(newChoiceList, backtrackTransition));
    // Add to priority queue
    if (!backtrackStateQ.contains(stateId)) {
      backtrackStateQ.add(stateId);
    }
  }

  private void addPredecessors(int stateId) {
    PredecessorInfo predecessorInfo;
    if (!stateToPredInfo.containsKey(stateId)) {
      predecessorInfo = new PredecessorInfo();
      stateToPredInfo.put(stateId, predecessorInfo);
    } else {  // This is a new state Id
      predecessorInfo = stateToPredInfo.get(stateId);
    }
    predecessorInfo.recordPredecessor(currentExecution, choiceCounter - 1);
  }

  // Analyze Read/Write accesses that are directly invoked on fields
  private void analyzeReadWriteAccesses(Instruction executedInsn, int currentChoice) {
    // Get the field info
    FieldInfo fieldInfo = ((JVMFieldInstruction) executedInsn).getFieldInfo();
    // Analyze only after being initialized
    String fieldClass = fieldInfo.getFullName();
    // Do the analysis to get Read and Write accesses to fields
    ReadWriteSet rwSet = getReadWriteSet(currentChoice);
    int objectId = fieldInfo.getClassInfo().getClassObjectRef();
    // Record the field in the map
    if (executedInsn instanceof WriteInstruction) {
      // We first check the non-relevant fields set
      if (!nonRelevantFields.contains(fieldInfo)) {
        // Exclude certain field writes because of infrastructure needs, e.g., Event class field writes
        for (String str : EXCLUDED_FIELDS_READ_WRITE_INSTRUCTIONS_STARTS_WITH_LIST) {
          if (fieldClass.startsWith(str)) {
            nonRelevantFields.add(fieldInfo);
            return;
          }
        }
      } else {
        // If we have this field in the non-relevant fields set then we return right away
        return;
      }
      rwSet.addWriteField(fieldClass, objectId);
    } else if (executedInsn instanceof ReadInstruction) {
      rwSet.addReadField(fieldClass, objectId);
    }
  }

  // Analyze Read accesses that are indirect (performed through iterators)
  // These accesses are marked by certain bytecode instructions, e.g., INVOKEINTERFACE
  private void analyzeReadWriteAccesses(Instruction instruction, ThreadInfo ti, int currentChoice) {
    // Get method name
    INVOKEINTERFACE insn = (INVOKEINTERFACE) instruction;
    if (insn.toString().startsWith(GET_PROPERTY_METHOD) &&
            insn.getMethodInfo().getName().equals(DO_CALL_METHOD)) {
      // Extract info from the stack frame
      StackFrame frame = ti.getTopFrame();
      int[] frameSlots = frame.getSlots();
      // Get the Groovy callsite library at index 0
      ElementInfo eiCallsite = VM.getVM().getHeap().get(frameSlots[0]);
      if (!eiCallsite.getClassInfo().getName().startsWith(GROOVY_CALLSITE_LIB)) {
        return;
      }
      // Get the iterated object whose property is accessed
      ElementInfo eiAccessObj = VM.getVM().getHeap().get(frameSlots[1]);
      if (eiAccessObj == null) {
        return;
      }
      // We exclude library classes (they start with java, org, etc.) and some more
      ClassInfo classInfo = eiAccessObj.getClassInfo();
      String objClassName = classInfo.getName();
      // Check if this class info is part of the non-relevant classes set already
      if (!nonRelevantClasses.contains(classInfo)) {
        if (excludeThisForItStartsWith(EXCLUDED_FIELDS_READ_WRITE_INSTRUCTIONS_STARTS_WITH_LIST, objClassName) ||
                excludeThisForItStartsWith(EXCLUDED_FIELDS_STARTS_WITH_LIST, objClassName)) {
          nonRelevantClasses.add(classInfo);
          return;
        }
      } else {
        // If it is part of the non-relevant classes set then return immediately
        return;
      }
      // Extract fields from this object and put them into the read write
      int numOfFields = eiAccessObj.getNumberOfFields();
      for(int i=0; i<numOfFields; i++) {
        FieldInfo fieldInfo = eiAccessObj.getFieldInfo(i);
        if (fieldInfo.getType().equals(JAVA_STRING_LIB) || fieldInfo.getType().equals(JAVA_INTEGER)) {
          String fieldClass = fieldInfo.getFullName();
          ReadWriteSet rwSet = getReadWriteSet(currentChoice);
          int objectId = fieldInfo.getClassInfo().getClassObjectRef();
          // Record the field in the map
          rwSet.addReadField(fieldClass, objectId);
        }
      }
    }
  }

  private int checkAndAdjustChoice(int currentChoice, VM vm) {
    // If current choice is not the same, then this is caused by the firing of IntIntervalGenerator
    // for certain method calls in the infrastructure, e.g., eventSince()
    ChoiceGenerator<?> currentCG = vm.getChoiceGenerator();
    // This is the main event CG
    if (currentCG instanceof IntIntervalGenerator) {
      // This is the interval CG used in device handlers
      ChoiceGenerator<?> parentCG = ((IntIntervalGenerator) currentCG).getPreviousChoiceGenerator();
      // Iterate until we find the IntChoiceFromSet CG
      while (!(parentCG instanceof IntChoiceFromSet)) {
        parentCG = ((IntIntervalGenerator) parentCG).getPreviousChoiceGenerator();
      }
      // Find the choice related to the IntIntervalGenerator CG from the map
      currentChoice = currentExecution.getChoiceFromCG((IntChoiceFromSet) parentCG);
    }
    return currentChoice;
  }

  private void createBacktrackingPoint(int eventChoice, Execution conflictExecution, int conflictChoice) {
    // Create a new list of choices for backtrack based on the current choice and conflicting event number
    // E.g. if we have a conflict between 1 and 3, then we create the list {3, 1, 0, 2}
    // for the original set {0, 1, 2, 3}
    
    // eventChoice represents the event/transaction that will be put into the backtracking set of
    // conflictExecution/conflictChoice
    Integer[] newChoiceList = new Integer[refChoices.length];
    ArrayList<TransitionEvent> conflictTrace = conflictExecution.getExecutionTrace();
    int stateId = conflictTrace.get(conflictChoice).getStateId();
    // Check if this trace has been done from this state
    if (isTraceAlreadyConstructed(eventChoice, stateId)) {
      return;
    }
    // Put the conflicting event numbers first and reverse the order
    newChoiceList[0] = eventChoice;
    // Put the rest of the event numbers into the array starting from the minimum to the upper bound
    for (int i = 0, j = 1; i < refChoices.length; i++) {
      if (refChoices[i] != newChoiceList[0]) {
        newChoiceList[j] = refChoices[i];
        j++;
      }
    }
    // Predecessor of the new backtrack point is the same as the conflict point's
    addNewBacktrackPoint(stateId, newChoiceList, conflictTrace.get(conflictChoice));
  }

  private boolean excludeThisForItContains(String[] excludedStrings, String className) {
    for (String excludedField : excludedStrings) {
      if (className.contains(excludedField)) {
        return true;
      }
    }
    return false;
  }

  private boolean excludeThisForItEndsWith(String[] excludedStrings, String className) {
    for (String excludedField : excludedStrings) {
      if (className.endsWith(excludedField)) {
        return true;
      }
    }
    return false;
  }

  private boolean excludeThisForItStartsWith(String[] excludedStrings, String className) {
    for (String excludedField : excludedStrings) {
      if (className.startsWith(excludedField)) {
        return true;
      }
    }
    return false;
  }

  private void exploreNextBacktrackPoints(VM vm, IntChoiceFromSet icsCG) {
    // Check if we are reaching the end of our execution: no more backtracking points to explore
    // cgMap, backtrackMap, backtrackStateQ are updated simultaneously (checking backtrackStateQ is enough)
    if (!backtrackStateQ.isEmpty()) {
      // Set done all the other backtrack points
      for (TransitionEvent backtrackTransition : currentExecution.getExecutionTrace()) {
        backtrackTransition.getTransitionCG().setDone();
      }
      // Reset the next backtrack point with the latest state
      int hiStateId = backtrackStateQ.peek();
      // Restore the state first if necessary
      if (vm.getStateId() != hiStateId) {
        RestorableVMState restorableState = restorableStateMap.get(hiStateId);
        vm.restoreState(restorableState);
      }
      // Set the backtrack CG
      IntChoiceFromSet backtrackCG = (IntChoiceFromSet) vm.getChoiceGenerator();
      setBacktrackCG(hiStateId, backtrackCG);
    } else {
      // Set done this last CG (we save a few rounds)
      icsCG.setDone();
    }
    // Save all the visited states when starting a new execution of trace
    prevVisitedStates.addAll(currVisitedStates.keySet());
    // This marks a transitional period to the new CG
    isEndOfExecution = true;
  }

  private boolean isConflictFound(int eventChoice, Execution conflictExecution, int conflictChoice,
                                  ReadWriteSet currRWSet) {
    // conflictExecution/conflictChoice represent a predecessor event/transaction that can potentially have a conflict
    ArrayList<TransitionEvent> conflictTrace = conflictExecution.getExecutionTrace();
    HashMap<Integer, ReadWriteSet> confRWFieldsMap = conflictExecution.getReadWriteFieldsMap();
    // Skip if this event does not have any Read/Write set or the two events are basically the same event (number)
    if (!confRWFieldsMap.containsKey(conflictChoice) || eventChoice == conflictTrace.get(conflictChoice).getChoice()) {
      return false;
    }
    // R/W set of choice/event that may have a potential conflict
    ReadWriteSet confRWSet = confRWFieldsMap.get(conflictChoice);
    // Check for conflicts with Read and Write fields for Write instructions
    Set<String> currWriteSet = currRWSet.getWriteSet();
    for(String writeField : currWriteSet) {
      int currObjId = currRWSet.writeFieldObjectId(writeField);
      if ((confRWSet.readFieldExists(writeField) && confRWSet.readFieldObjectId(writeField) == currObjId) ||
          (confRWSet.writeFieldExists(writeField) && confRWSet.writeFieldObjectId(writeField) == currObjId)) {
        // Remove this from the write set as we are tracking per memory location
        currRWSet.removeWriteField(writeField);
        return true;
      }
    }
    // Check for conflicts with Write fields for Read instructions
    Set<String> currReadSet = currRWSet.getReadSet();
    for(String readField : currReadSet) {
      int currObjId = currRWSet.readFieldObjectId(readField);
      if (confRWSet.writeFieldExists(readField) && confRWSet.writeFieldObjectId(readField) == currObjId) {
        // Remove this from the read set as we are tracking per memory location
        currRWSet.removeReadField(readField);
        return true;
      }
    }
    // Return false if no conflict is found
    return false;
  }

  private boolean isFieldExcluded(Instruction executedInsn) {
    // Get the field info
    FieldInfo fieldInfo = ((JVMFieldInstruction) executedInsn).getFieldInfo();
    // Check if the non-relevant fields set already has it
    if (nonRelevantFields.contains(fieldInfo)) {
      return true;
    }
    // Check if the relevant fields set already has it
    if (relevantFields.contains(fieldInfo)) {
      return false;
    }
    // Analyze only after being initialized
    String field = fieldInfo.getFullName();
    // Check against "starts-with", "ends-with", and "contains" list
    if (excludeThisForItStartsWith(EXCLUDED_FIELDS_STARTS_WITH_LIST, field) ||
            excludeThisForItEndsWith(EXCLUDED_FIELDS_ENDS_WITH_LIST, field) ||
            excludeThisForItContains(EXCLUDED_FIELDS_CONTAINS_LIST, field)) {
      nonRelevantFields.add(fieldInfo);
      return true;
    }
    relevantFields.add(fieldInfo);
    return false;
  }

  // Check if this trace is already constructed
  private boolean isTraceAlreadyConstructed(int firstChoice, int stateId) {
    // Concatenate state ID and only the first event in the string, e.g., "1:1 for the trace 10234 at state 1"
    // Check if the trace has been constructed as a backtrack point for this state
    // TODO: THIS IS AN OPTIMIZATION!
    HashSet<Integer> choiceSet;
    if (doneBacktrackMap.containsKey(stateId)) {
      choiceSet = doneBacktrackMap.get(stateId);
      if (choiceSet.contains(firstChoice)) {
        return true;
      }
    } else {
      choiceSet = new HashSet<>();
      doneBacktrackMap.put(stateId, choiceSet);
    }
    choiceSet.add(firstChoice);

    return false;
  }

  private HashSet<Predecessor> getPredecessors(int stateId) {
    // Get a set of predecessors for this state ID
    HashSet<Predecessor> predecessors;
    if (stateToPredInfo.containsKey(stateId)) {
      PredecessorInfo predecessorInfo = stateToPredInfo.get(stateId);
      predecessors = predecessorInfo.getPredecessors();
    } else {
      predecessors = new HashSet<>();
    }

    return predecessors;
  }

  private ReadWriteSet getReadWriteSet(int currentChoice) {
    // Do the analysis to get Read and Write accesses to fields
    ReadWriteSet rwSet;
    // We already have an entry
    HashMap<Integer, ReadWriteSet> currReadWriteFieldsMap = currentExecution.getReadWriteFieldsMap();
    if (currReadWriteFieldsMap.containsKey(currentChoice)) {
      rwSet = currReadWriteFieldsMap.get(currentChoice);
    } else { // We need to create a new entry
      rwSet = new ReadWriteSet();
      currReadWriteFieldsMap.put(currentChoice, rwSet);
    }
    return rwSet;
  }

  // Reset data structure for each new execution
  private void resetStatesForNewExecution(IntChoiceFromSet icsCG, VM vm) {
    if (choices == null || choices != icsCG.getAllChoices()) {
      // Reset state variables
      choiceCounter = 0;
      choices = icsCG.getAllChoices();
      refChoices = copyChoices(choices);
      // Clear data structures
      currVisitedStates.clear();
      stateToEventMap.clear();
      isEndOfExecution = false;
    }
  }

  // Set a backtrack point for a particular state
  private void setBacktrackCG(int stateId, IntChoiceFromSet backtrackCG) {
    // Set a backtrack CG based on a state ID
    LinkedList<BacktrackExecution> backtrackExecutions = backtrackMap.get(stateId);
    BacktrackExecution backtrackExecution = backtrackExecutions.removeLast();
    backtrackCG.setNewValues(backtrackExecution.getChoiceList());  // Get the last from the queue
    backtrackCG.setStateId(stateId);
    backtrackCG.reset();
    // Update current execution with this new execution
    Execution newExecution = new Execution();
    TransitionEvent firstTransition = backtrackExecution.getFirstTransition();
    newExecution.addTransition(firstTransition);
    // Try to free some memory since this map is only used for the current execution
    currentExecution.clearCGToChoiceMap();
    currentExecution = newExecution;
    // Remove from the queue if we don't have more backtrack points for that state
    if (backtrackExecutions.isEmpty()) {
      backtrackMap.remove(stateId);
      backtrackStateQ.remove(stateId);
    }
  }

  // Update backtrack sets
  // 1) recursively, and
  // 2) track accesses per memory location (per shared variable/field)
  private void updateBacktrackSet(Execution execution, int currentChoice) {
    // Copy ReadWriteSet object
    HashMap<Integer, ReadWriteSet> currRWFieldsMap = execution.getReadWriteFieldsMap();
    ReadWriteSet currRWSet = currRWFieldsMap.get(currentChoice);
    if (currRWSet == null) {
      return;
    }
    currRWSet = currRWSet.getCopy();
    // Memorize visited TransitionEvent object while performing backward DFS to avoid getting caught up in a cycle
    HashSet<TransitionEvent> visited = new HashSet<>();
    // Conflict TransitionEvent is essentially the current TransitionEvent
    TransitionEvent confTrans = execution.getExecutionTrace().get(currentChoice);
    // Update backtrack set recursively
    updateBacktrackSetDFS(execution, currentChoice, confTrans.getChoice(), currRWSet, visited);
  }

  private void updateBacktrackSetDFS(Execution execution, int currentChoice, int conflictEventChoice,
                                     ReadWriteSet currRWSet, HashSet<TransitionEvent> visited) {
    TransitionEvent currTrans = execution.getExecutionTrace().get(currentChoice);
    // Record this transition into the state summary of main summary
    currRWSet = mainSummary.updateStateSummary(currTrans.getStateId(), conflictEventChoice, currRWSet);
    // Halt when we have visited this transition (in a cycle)
    if (visited.contains(currTrans)) {
      return;
    }
    visited.add(currTrans);
    // Check the predecessors only if the set is not empty
    if (!currRWSet.isEmpty()) {
      // Explore all predecessors
      for (Predecessor predecessor : getPredecessors(currTrans.getStateId())) {
        // Get the predecessor (previous conflict choice)
        int predecessorChoice = predecessor.getChoice();
        Execution predecessorExecution = predecessor.getExecution();
        // Push up one happens-before transition
        int newConflictEventChoice = conflictEventChoice;
        // Check if a conflict is found
        ReadWriteSet newCurrRWSet = currRWSet.getCopy();
        if (isConflictFound(conflictEventChoice, predecessorExecution, predecessorChoice, newCurrRWSet)) {
          createBacktrackingPoint(conflictEventChoice, predecessorExecution, predecessorChoice);
          // We need to extract the pushed happens-before event choice from the predecessor execution and choice
          newConflictEventChoice = predecessorExecution.getExecutionTrace().get(predecessorChoice).getChoice();
        }
        // Continue performing DFS if conflict is not found
        updateBacktrackSetDFS(predecessorExecution, predecessorChoice, newConflictEventChoice,
                newCurrRWSet, visited);
      }
    }
  }

  // --- Functions related to the reachability analysis when there is a state match

  private void addPredecessorToRevisitedState(int stateId) {
    // Perform this analysis only when:
    // 1) this is not during a switch to a new execution,
    // 2) at least 2 choices/events have been explored (choiceCounter > 1),
    // 3) state > 0 (state 0 is for boolean CG)
    if (!isEndOfExecution && choiceCounter > 1 && stateId > 0) {
      if ((currVisitedStates.containsKey(stateId) && currVisitedStates.get(stateId) > 1) ||
              prevVisitedStates.contains(stateId)) {
        // Record a new predecessor for a revisited state
        addPredecessors(stateId);
      }
    }
  }

  // Update the backtrack sets from previous executions
  private void updateBacktrackSetsFromGraph(int stateId, Execution currExecution, int currChoice) {
    // Get events/choices at this state ID
    Set<Integer> eventChoicesAtStateId = mainSummary.getEventChoicesAtStateId(stateId);
    for (Integer eventChoice : eventChoicesAtStateId) {
      // Get the ReadWriteSet object for this event at state ID
      ReadWriteSet rwSet = mainSummary.getRWSetForEventChoiceAtState(eventChoice, stateId).getCopy();
      // We have to first check for conflicts between the event and the current transition
      // Push up one happens-before transition
      int conflictEventChoice = eventChoice;
      if (isConflictFound(eventChoice, currExecution, currChoice, rwSet)) {
        createBacktrackingPoint(eventChoice, currExecution, currChoice);
        // We need to extract the pushed happens-before event choice from the predecessor execution and choice
        conflictEventChoice = currExecution.getExecutionTrace().get(currChoice).getChoice();
      }
      // Memorize visited TransitionEvent object while performing backward DFS to avoid getting caught up in a cycle
      HashSet<TransitionEvent> visited = new HashSet<>();
      // Update the backtrack sets recursively
      updateBacktrackSetDFS(currExecution, currChoice, conflictEventChoice, rwSet, visited);
    }
  }
}
