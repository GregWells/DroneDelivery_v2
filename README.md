# DroneDelivery_v2

# This readMe is a work-in-process for notes as I develop the code...

Reinforcement learning methodology applied to Kaggle drone delivery challenge 

The prior version of [this project] (https://github.com/GregWells/3402FinalProject) attempted to elicit emergent drone behavior optimized to the Kaggle Challenge goal but utilized a methodology of negative rewards to attempt to train the viable selection criteria. This attempt will present only valid options to the AI with positive value scoring (rewards) to facilitate optimal path selection. 'Unplayable' options will NOT be presented to the AI via the observation--> action --> reward --> observation cyle

Another [prior version of this project](https://github.com/GregWells/DATA3402/tree/main/Exams/Final) was previously created without utilizing RL techniques, but rather, purely programmed logic.  

This effort will combine the two techniques. The first steps will create new features and the policies that will shape how the raw data and features will be presented to the AI. A second step will provide viable options to the AI for the model to train on. And the third step will process the resultant action to formulate the new observation.

## Detailed summary
A detailed summary of the ongoing development can be found [here](https://github.com/GregWells/DroneDelivery_v2/detailedSummary.md). 


## Overview

The action will be a simple single value (discrete) criteria. The observation will be an array of viable manifests. Within the array will be a variety of objectives. For instance, array row 0 will contain a manifest that begins at a given warehouse and ends with a final delivery very close to that same warehouse (tight loop), row 1 will be a relatively straight line to the next closest warehouse making deliveries along the route, objective 2 will be intermodal transfer, objective 3 will be a combination of 1 & 2, etc. These objectives for the observation arrays will remain as consistent as possible and will also contain an unrealistic option as a control. The use of the control over the learning cycle should approach 0. This will be plotted for verification.

## Expectations 

* Possible emergent behavior
    * As delivery options very close to the warehouses are fulfilled, the AI may transition to intermodal transfers. The usage of these options can be graphed. 
    * Some drones could emerge as mostly intermodal while others mostly delivery. 


## Questions:

* Does the configuration of the  action and observation spaces facilitate this possibility?" Clearly some information of other drone positions must be available within the observation space to make this possible. 
* How does the ratio of warehouses to drones to orders alter the behavior of the drones in the simulation?

## Improvements to explore:
* The setup of this configuration is that all products for a specified delivery area must transit through the closest warehouse. This is clearly at least slightly sub-optimal. Accomodating the most egregious time penalties by providing direct routing would be a possible future exploration or completely altering the warehouse delivery area concept could be a significant optimization. 
    