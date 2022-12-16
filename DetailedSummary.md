# DroneDelivery_v2

# This readMe is a work-in-process for notes as I develop the code...

Reinforcement learning methodology applied to Kaggle drone challenge 

The prior version of this project (https://github.com/GregWells/3402FinalProject) attempted to elicit emergent drone behavior optimized to the Kaggle Challenge goal but utilized a methodology of negative rewards to attempt to train the viable selection criteria. This attempt will present only valid options to the AI with positive value scoring (rewards) to facilitate optimal path selection. 'Unplayable' options will NOT be presented to the AI via the observation--> action --> reward --> observation cyle

Another prior version of this project (https://github.com/GregWells/DATA3402/tree/main/Exams/Final) was previously created without utilizing RL techniques, but rather, purely programmed logic.  

This effort will combine the two techniques. The first steps will create new features and the policies that will shape how the raw data and features will be presented to the AI. A second step will provide viable options to the AI for the model to train on. And the third step will process the resultant action to formulate the new observation.



## Overview


- [x] New feature: Create a variable for every order indicating the closest wh (simple Euclidean distance calculation)
 


- [x] If product is available in closest wh, assign that item to the order. This could be RL; sort orders by proximity to wh ; assign while traversing down the list to assure closest to wh orders get the in stock merch


- [x] Once all local stock for local orders is assigned:


If not in stock locally, append to a 'warehouse wish list'. (warehouse, ordernum, dist,prod) This could possibly be expressed as a hash. Collisions are assigned to the shortest distance (distance between warehouses + dist to order from local wh) first.


- [x] New feature: Create a variable for every order indicating the assigned intermodal warehouse (or None)


- [x] Mark the assigned items with the ordernum and the wh they belong in. 


- [x] All orders should now be assigned


- [x] New Feature: Calc the max possible subscore for every order(total dist from (intermodal wh to) wh to customer) 

- [x] New Feature: Calc the max possible score for each item (sum sub scores for all items in original order) 

- [ ] New feature: Convert each row,col of warehouse and orders to a dictionary single positive integer value. This code already exists in the prior project


Now the main AI part:

Present the observation to the AI:
* A Drone is at position X with the available orders of: [ (ordernum: dist, max score, weight) , …]  
* List (some) orders within proximity of furthest avail order from the nearest wh to current drone position 
* Optimally, where should the drone end up? Near a wh (probably) 
* If there are > x choices within half the distance to the next wh, only consider local loops
* Create (in consideration of payload/weight constraint) manifests and use the best option 
* THIS is the main AI portion- manifests optimized by multiple constraints (weight/maxscore/round trip dist/time). The total score per manifest is easy to compute but there are (insert equation) possibilities. Balance this computation cost by limiting scope to reasonable possibilities. (Later: research whether the ´reasonable-ness ´ is ignoring too many optimal solutions) 


Limit each episode to 10,000 iterations or when the ‘ep-mean-rew' stabilizes (how to determine?) Can the model be continually trained to shorten training for subsequent searches from same region?

What’s the cost of computation vs value of increased efficiency ? 


Note: Items marked GAME are game rule optimizations that would not be applied to real life scenarios. Real life would substitute customer-satisfaction-aligned goals instead.