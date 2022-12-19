import gym
from icecream import ic
from itertools import combinations
import math
import numpy as np
global PSEUDO,PSEUDOORDERLIMIT
PSEUDO=False
PSEUDOORDERLIMIT=82
DEBUG=False



########### Functions   ##################

def dist(p1, p2):
    (x1, y1), (x2, y2) = p1, p2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def distToLine(x1, y1, x2, y2, x3, y3): # x1,y1 one end of line segment x2,y2 other end; x3,y3 is the point
    px = x2-x1
    py = y2-y1
    norm = px*px + py*py
    u =  ((x3 - x1) * px + (y3 - y1) * py) / float(norm)
    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py
    dx = x - x3
    dy = y - y3
    # Note: If the actual distance does not matter,
    # if you only want to compare what this function
    # returns to other results of this function, you
    # can just return the squared distance instead
    # (i.e. remove the sqrt) to gain a little performance
    dist = (dx*dx + dy*dy)**.5
    return dist
def createOrdArray():
    # create a table of each order and its distance from a line connecting each two warehouse pairs
    #This will be used to select optimal flight/delivery paths on intermodal flights
    #Sorting the array by a given column (where prod is not fulfilled) and selecting the smallest value
    # results in an ordernum that is nearest the beeline
    #Cols: orderNum, r,c,weight,fulfilled,inStock,0to0,0to1,1to1,...

    import numpy as np

    # creating an empty 2d array of int type
    #cols=orderNum,r,c,weight,fulfilled,distFrom0to1line,
    global ordArray
    ordArray = np.empty((0,106), int)
    #ordArray=ordArray.reshape((0, 105))
    #ordArray=np.append(ordArray,np.zeros((105,), dtype=int))
    # using np.append()
    for i in range(len(ord)):
        ordList=list()
        #ordArray=np.append(ordArray,np.zeros((105,), dtype=np.int32))
        r,c=ord[i].getPos()
        wt=ord[i].getWeight()
        _,wh=ord[i].getAssignedItem() 
        assignedWh=ord[i].getWh()
        if wh==assignedWh:
            inStock=True
        else:
            inStock=False
        if ord[i].isFulfilled() or ord[i].isLoaded(): 
            fulfilled=1
        else:
            fulfilled=0
        ordList.extend([i,r,c,wt,fulfilled,inStock])
        for j in range(10):
            wr1,wc1=w[j].getPos()
            for k in range(10):
                wr2,wc2=w[k].getPos()
                #ordArray[i][5+j*10+k]=distToLine(wr1,wc1,wr2,wc2,r,c)
                if wr1!=wr2 and wc1!=wc2:
                    ordList.append(int(distToLine(wr1,wc1,wr2,wc2,r,c)))
                else:
                    ordList.append(0)
        ordArray=np.append(ordArray,ordList)
    ordArray.shape=(len(ord),106)
    
def closestToBeeline(wh1,wh2):
    colNum=6+wh1*10+wh2
    #a[a[:,2].argsort()]           #sort by the 3rd column ascending
    #a[a[:,2].argsort()][::-1]     #sort by the 3rd column descending
    #first sort by weight(ascending),then by dist from beeline(ascending), then by fulfilled(ascending?)
    
    #ordArray=ordArray[ordArray[:,3].argsort()] #weight
    #ordArray=ordArray[ordArray[:,colNum].argsort()] #distance
    #ordArray=ordArray[ordArray[:,4].argsort()] #isFulfilled
    ind = np.lexsort((ordArray[:,colNum],ordArray[:,3],ordArray[:,4]))
    #ic(colNum)
    #use ordArray[i][colNum] for selection
    return ind    

def ordersInRadius(wh,r):    #Usage ordersInRadius(2,30)
    wr,wc=w[wh].getPos()
    return np.count_nonzero(np.logical_and ( ( (ordArray[:,1]-wr)**2 + (ordArray[:,2]-wc)**2 <r**2) ,  ordArray[:,4]==0)) 
def ordersInRadius2(wh,r):    #Usage ordersInRadius(2,30)
    wr,wc=w[wh].getPos()
    return np.count_nonzero(  (ordArray[:,1]-wr)**2 + (ordArray[:,2]-wc)**2 <r**2 )
def ordersUnfilled(wh):    #Usage ordersUnfilled(2)
    unfilledOrderCount=0
    for i in range(Order.getQty()):
        if ord[i].getWh()==wh and not ord[i].isFulfilled() and not ord[i].isLoaded:
            unfilledOrderCount+=1
    return unfilledOrderCount

def ordersInStockClose(wh,r):
    wr,wc=w[wh].getPos()
    return np.count_nonzero(np.logical_and ( ( (ordArray[:,1]-wr)**2 + (ordArray[:,2]-wc)**2 <r**2) ,  ordArray[:,4]==0,ordArray[:,5]==0)) 
def ordersInStockFar(wh,r):
    wr,wc=w[wh].getPos()
    return np.count_nonzero(np.logical_and ( ( (ordArray[:,1]-wr)**2 + (ordArray[:,2]-wc)**2 >=r**2) ,  ordArray[:,4]==0,ordArray[:,5]==0)) 

def dronesInRadius(wh,r):    #Usage dronesInRadius(2,30)
    count=0
    wr,wc=w[wh].getPos()
    for i in range(Drone.getQty()):
        dr,dc=d[i].getDest()
        if ((dr-wr)**2 + (dc-wc)**2 <r**2 ):
            count+=1
    return count

def knn(x, X, k, **kwargs):
    """
    find indices of k-nearest neighbors of x in X
    """
    d = distance.cdist(x.reshape(1,-1), X, **kwargs).flatten()
    return np.argpartition(d, k)[:k]

def consumeInputFile2():
    global prodWeight,item,warehouse,drone,orders,locations,priorDroneCmd
    global whProdOffset,dronePayloadOffset
    global gridRows,gridCols, droneQty,deadline,maxLoad,whLocs
    global w, p, d, ord
    locations={}
    item=list()
    locationCounter=0
    #read datafile
    filename="busy_day.in"
    #raise SystemExit("Stop right here to evaluate! {}".format(filename))

    with open(filename) as fp:
        line = fp.readline()
        line=line.strip()
        phase = 0
        
        while line: 
            print("Executing section {} of input file {}: {}".format(phase,filename, line.strip()))
            if phase==0:
                rows,cols,droneqty,deadline,maxLoad=line.split(maxsplit=5)
                gridRows=int(rows)
                gridCols=int(cols)
                print("gridRows:{} ,gridCols:{}".format(gridRows,gridCols))
                droneqty=int(droneqty)
                deadline=int(deadline)
                maxLoad=int(maxLoad)
            elif phase==1:  ########  Simulation  parameters  ##############
                print(line)

                minItemWeight=maxLoad   #tune this downward as items are processed
                totalProductTypes=int(line)
                line = fp.readline()
                productWeightList = line.split()  #this is a list of product weights

                p=[0]*(totalProductTypes)  #create a list of productType object names
                
                

                for productNum in range(totalProductTypes):
                    #instantiate each product
                    thisWeight=int(productWeightList[productNum])
                    if minItemWeight>thisWeight:
                        minItemWeight=thisWeight
                    #ic(ProductType(productNum,thisWeight))
                    #raise SystemExit("Stop right here to evaluate! 3c")
                    p[productNum]=ProductType(productNum,thisWeight)
                    
                    #print("productNum:{},Weight:{} ".format(productNum,thisWeight) )
                    #pass
                #phase +=1

            elif phase==2:   ########  Warehouse detail  ##############

                whQty=int(line)
                whDict={}
                whLocs=list()
                w=[0]*(whQty)  #create a list of warehouse object names
                for warehouseNum in range(whQty):
                    line = fp.readline()
                    r,c = line.split()
                    r,c=int(r),int(c)
                    locations.update({(r,c):locationCounter})
                    locationCounter+=1
                    w[warehouseNum]=Warehouse(warehouseNum,r,c)
                    whLocs.append(  (r,c)  )
                    whDict[(r,c)]=warehouseNum
                    line = fp.readline()
                    for productNum,productQty in enumerate(line.split()):
                        productNum,productQty=int(productNum),int(productQty)
                        #instantiate quantity of each product for this warehouse
                        #print("Warehouse:{}   productNum:{}  qty:{}".format(warehouseNum,productNum,productQty))
                        #itemQuantity=item.getQty()
                        for i in range(productQty):
                            item.append(Item(productNum,'W',warehouseNum,p[productNum].getWeight()))
                        pass
                    #Validate all products are listed in the input file
                    if productNum+1!= totalProductTypes:
                        print("ERROR:  Invalid input file load for warehouse: {} productNum={}".format(warehouseNum,productNum))
                        break
                print("warehouse Locations:{}".format(whLocs))
                #compute average distance btw warehouses
                points=whLocs
                distances = [Calculate.dist(p1, p2) for p1, p2 in combinations(whLocs, 2)]
                avg_distance = sum(distances) / len(distances)
                print("avg_distance btw warehouses:{}".format(avg_distance))
                closeDist=avg_distance/2
                #instantiate drones
                row,col=w[0].getPos()
                d=list()
                for i in range(int(droneqty)):
                    d.append(Drone(row,col,maxLoad))
                    d[i].setDest(row,col)
                    #ic(d[i].getDest())
            elif phase==3:  ########  Customer orders   ##############
                totalOrders=int(line)
                print("There are {} total orders".format(totalOrders))
                allOrderlocs=list()
                ord=list()  #create a list of order object names
                for orderNum in range(totalOrders):

                    line = fp.readline()
                    r,c = line.split()
                    r,c = int(r),int(c)
                    orderTup=(r,c)
                    if orderTup not in locations.keys():               #some orders are for repeat cust, so not at new loc
                        locations.update({orderTup:locationCounter})
                        locationCounter+=1
                    line = fp.readline()
                    orderQty = int(line)
                    #ord[orderNum]=Order(orderNum,r,c)
                    line = fp.readline()
                    if PSEUDO:
                        if orderNum==PSEUDOORDERLIMIT:
                            #orderedProducts=line.split()
                            prodNums = [int(x) for x in line.split()]
                            for index in range(orderQty):
                                #instantiate order
                                allOrderlocs.append( (r,c) )
                                weight=p[prodNums[index]].getWeight()
                                orderIndex=Order.getQty()
                                ord.append(Order(orderNum,r,c,prodNums[index],orderQty,weight))
                            DEBUG and print("OrderNum {}: Cust: {},{}  Line Items:{} ".format(orderNum, r,c,orderQty,line))
                    else:
                        #orderedProducts=line.split()
                        prodNums = [int(x) for x in line.split()]
                        for index in range(orderQty):
                            #instantiate order
                            allOrderlocs.append( (r,c) )
                            weight=p[prodNums[index]].getWeight()
                            orderIndex=Order.getQty()
                            ord.append(Order(orderNum,r,c,prodNums[index],orderQty,weight))
                        DEBUG and print("OrderNum {}: Cust: {},{}  Line Items:{} ".format(orderNum, r,c,orderQty,line))
                break
            phase +=1
            line = fp.readline()  #read next line
            line=line.strip()
        #raise SystemExit("Stop right here to evaluate! 4")
        
    fp.close()
    
    
    #print("{} extra lines in input file".format(counter))  
    print("Max Payload:{}".format(maxLoad))
    #raise SystemExit("Stop right here to evaluate! 3")

    #totalItemsInSim=Item.getQty()
    print("Total Items available in warehouses:{}".format(Item.getQty()))

    ##### Show what was loaded from input file
    for i in range(Drone.getQty()):
        #d[i].showStatus()
        pass   
    for productNum in range(totalProductTypes):
        #num,weight=p[productNum].getStatus()
        #print("Product:{}  Weight:{}".format(num,weight))
        pass
    for whn in range(whQty):
        itemCount=w[whn].getInventory(item,Item.getQty())
        #print("Warehouse:{} has {} items".format(whn,itemCount))
        pass
    print("Order qty:{}".format(Order.getQty()))   

    #for i in range(395,410):
        #item[i].showStatus()
    #    pass
    #for i in range(10):
    #    orderIndex,r,c,orderNum,prodNum,remItems=ord[i].getStatus()
        #print("orderIndex:{} orderNum:{}  r:{} c:{}  prodNum:{} remItems:{}".format(orderIndex,orderNum,r,c,prodNum,remItems))
    #    pass

    #for i in range(Order.getQty()):
    #    if ord[i].getRemItems()>8:
    #        print(i,"  ",ord[i].getRemItems())

    #################################################################
    ####                 Warehouse assignments             ##########
    #################################################################


    #First assign each order to a warehouse based on proximity 
    #later an ML will determine assignment

    for i in range(Order.getQty()):
        r,c=ord[i].getPos()
        ord[i].setWh(Calculate.nearestWh(r,c )  )
    #print("Order qty:{}".format(Order.getQty()))

    count=0
    for i in range(Order.getQty()):
        count+=1
        r,c=ord[i].getPos()
        #print(ord[i].getWh( )  ,end='' )                     

    ########## for each warehouse, assign existing product-items to a specific order ###########
    origInStockCounter=0
    origInStockList=list()
    intermodalListCounter=0
    #first create a list of every order based on distance to warehouse
    for wh in range(whQty):
        print("Warehouse {}".format(wh))
        wr,wc=w[wh].getPos()
        thisWhOrderList=Calculate.getAllOrdersForWh(wh)

        #Starting with the closest, assign specific items to orders
        for orderTup in thisWhOrderList:

            orderIndex,_=orderTup
            #print("orderIndex {}".format(orderIndex))
            #if the order does not yet have an item assignment...
            if not ord[orderIndex].isAssigned():
                #print("orderIndex {} is not assigned".format(orderIndex))
                prodNum=ord[orderIndex].getProdNum()
                #print("prodNum {} ".format(prodNum))

                # if the item is in stock at the designated warehouse then assign it

                #review products in this warehouse, if available, then assign it
                warehousesWithThisProd=list()
                foundLocally=False
                for i in range( Item.getQty() ):
                    itemIndex,pn,facType,facIndex,assigned=item[i].getStatus2()
                    if facType=='W'  and pn==prodNum and assigned==False :
                        #print("===>",'W',facType,wh,facIndex,facType=='W',facIndex==wh,pn==prodNum )

                        if wh==facIndex:
                            #print("origInStockCounter:{}".format(origInStockCounter))
                            foundLocally=True
                            origInStockCounter+=1
                            #assign this item to this order
                            item[itemIndex].assignToOrder(orderIndex)
                            ord[orderIndex].setAssignedItem((itemIndex,wh))
                            wr,wc=w[wh].getPos()
                            r,c=ord[orderIndex].getPos()
                            dist=math.ceil( Calculate.distance(r,c,wr,wc) )
                            origInStockList.append(orderIndex)
                            #print("Item {} Instock at local wh:{} dist:{}".format(itemIndex,wh,dist))
                            break
                if not foundLocally:
                    for i in range( Item.getQty() ):
                        itemIndex,pn,facType,facIndex,assigned=item[i].getStatus2()
                        if facType=='W'  and pn==prodNum and assigned==False :
                            #print(facIndex,type(facIndex),wh,type(wh),facIndex==wh )
                            warehousesWithThisProd.append(facIndex)

                    warehousesWithThisProd=list(set(warehousesWithThisProd))


                    #print("Warehouses with this prod:{}".format(warehousesWithThisProd))
                    closestWh=Calculate.nearestWh(wr,wc,warehousesWithThisProd )
                    #print("Assigning closest wh:{}".format(closestWh))
                    #print("product:{} not found locally in wh:{} --> closest wh:{}".format(prodNum,wh,closestWh))
                    #Find an available item. Search all available items with loc= chosen wh
                    itemIndex=Calculate.findAvailProdInWh(prodNum,closestWh)
                    item[itemIndex].assignToOrder(orderIndex)

                    ord[orderIndex].setAssignedItem(  (itemIndex,closestWh)  )
                    DEBUG and print("Order:{} being assigned item:{} NOT in wh:{} --> closest wh:{}".format(orderIndex,itemIndex,wh,closestWh))
                    #print("-",end='')
                    w[wh].addToIntermodalList(  (closestWh,orderIndex,itemIndex)      )

                    intermodalListCounter+=1


    print("Items originally in stock: {}  Intermodal list:{}".format(origInStockCounter, intermodalListCounter))
    #Check for orders without an assigned product
    for orderIndex in range( Order.getQty() ):
        if ord[orderIndex].isAssigned() == False:
            print("order[{}] has not been assigned an item ".format(orderIndex))
            raise SystemExit("Stop right here to evaluate!") 

        else:
            #print("=",end='')
            pass
    print("\n\n")

    for wh in range(whQty):
        print("Warehouse:{} Intermodal list length:{}".format(wh,len(w[wh].getIntermodalList())))



class DroneEnv(gym.Env):
    def __init__(self):
        super(DroneEnv, self).__init__()
        self.name="parent object to contain data and algorithm subclasses"
        self.manifestSeqNum=0
        self.macroScore=0
        self.total_reward=0
        self.droneqty=None
        self.totalOrders=None
        self.max_weight=None
        global deadline
        deadline=0
        
        #raise SystemExit("Stop right here to evaluate!")

        #consumeInputFile2()
        
        self.LUDWoptions=3
        #deadline=int(deadline* (self.totalOrders/9400))
        #[ priorDroneCmd.update({x:3}) for x in range(30) ] 
        # Define action and observation space
        # They must be gym.spaces objects
        
        #action position 0=drone , pos 1=LUDW, pos 2=order or warehouse ,pos 4=prodNum
        #print("self.action_space = gym.spaces.MultiDiscrete([ {} ])".format(2,3,self.orderIndex,self.totalProductTypes) )
        #self.action_space = gym.spaces.MultiDiscrete([1,self.LUDWoptions,len(locations),self.totalProductTypes])
        #To verify the environment works correctly, change the first value in the action space to 1 or 2 (drone qty)
        #starting Wh,ending Wh(vicinity), flight type (0=local:1=intermodal:2=mixed)
        self.action_space = gym.spaces.MultiDiscrete([10,10,3])

        #self.action_space = gym.spaces.MultiDiscrete([self.droneqty,3,self.orderIndex,self.totalProductTypes])
        
        #print("                                                ManSeq#,orders_Completed,#drones,Drone@Loc,PayloadWeight,priorCmd,currentCmd ])" )
        #print("self.observation_space = gym.spaces.MultiDiscrete([ {},{},{},{},{},{},{} ])".format(len(orders)*5,self.orderIndex+1,self.droneqty+1,self.locationCounter+1,maxLoad+2,3,3) )

        #self.observation_space =gym.spaces.MultiDiscrete(np.array([2001,9369,31,1254,11]))
        #obs space( ManifestNum, )
        #self.observation_space =gym.spaces.MultiDiscrete([len(orders),self.orderIndex+1,self.droneqty+1,self.locationCounter+1,maxLoad+1,int(4),int(4)])

    def showStatus(self,val=None):
        if val==None:
            rangeval=range(self.droneqty)
        else:
            rangeval=range(val,val+1)
        for i in rangeval:
            print("Drone:{} ".format(i),end=' ')
            for c in range (15):
                print(drone[i][c],end=' ')
            print( "    Excess Capacity:{}".format(maxLoad-sum([prodWeight[x] for x in filter(None,drone[i][dronePayloadOffset:15]) ]))) 
            #print("")
        print("")
    def getDroneLoc(self,droneNum):
        self.droneLoc=locations[drone[droneNum][2:4]]
        return self.droneLoc
    def getPayloadItems(self,droneNum):    
        self.payloadItems=len([self.x for self.x in drone[droneNum][5:15] if self.x!=None] )#last is # of items onboard  
        return self.payloadItems
    def resetManifestSeqNum(self):
        self.manifestSeqNum=0
    def getManifestSeqNum(self):
        return self.manifestSeqNum
    def incManifestSeqNum(self):
        self.manifestSeqNum+=1
    def getMacroScore(self):
        return self.macroScore
    def incMacroScore(self):
        self.macroScore+=1
    def resetMacroScore(self):
        self.macroScore==0
    def getWarehouseLoc(self,wh):
        return warehouse[wh][0:2]
    def getOrigOrderNum(self,val):
        self.origOrderNum=orders[val][5]
        return self.origOrderNum
    def getOrderLoc(self,val):
        return orders[val][0:2]
    
        
    def step(self, action):   #startWh, endWh, manifest type 0=local:1=intermodal:2=mixed
        self.actionList=list(action)
        #self.prev_actions.append(self.actionList)
        self.reward=0
        self.penalty=0
        self.bonus=0
        self.order=0
        #print("NextCommand:{}, {}, {}, {}:".format(nextCommand[0],nextCommand[1],nextCommand[2],nextCommand[3] ) )
        #manifestSeqNum,microScore,macroScore,droneNum,droneLoc,payloadItems=simAction(nextCommand)    

        #result=simAction(nextCommand[0],nextCommand[1],nextCommand[2],nextCommand[3]) 
        self.startWh=actionList[0]
        self.endWh=actionList[1]
        self.manifestType=actionList[2]
        
        self.droneNum=self.nextCommand[0]
        self.LUDW=self.nextCommand[1]
        self.location=self.nextCommand[2]
        self.order=self.nextCommand[3]
        self.pn=orders[self.order][6]
        
        #Get current drone details:
        DEBUG and print("Drone:{}".format(self.droneNum))
        self.dr,self.dc,self.dest_r,self.dest_c,self.dest_time=drone[self.droneNum][0:5]
        self.droneStartTime=self.dest_time
        self.droneStartingRow,self.droneStartingCol=(self.dr,self.dc)
                
        #def simAction(droneNum,LUDW,param1,pn,qty=1):  # DroneNum, L/U/D/W(1-4), (wh/orderNum/Time), prodNum, qty

        self.qty=1
        self.filledOrders=len([self.k for self.k, self.v in orders.items() if self.v[4]==True ])
        self.unfilledOrders=len([self.k for self.k, self.v in orders.items() if self.v[4]!=True ])

        #print("Len of Locations:{}  First={}  Last={}".format(len(locations),locations[(113,179)],locations[(157,157)] )  )

        self.droneLoc=locations[drone[self.droneNum][2:4]]
        #print("Drone:{}  LUDW:{} param1:{} pn:{}".format(droneNum,LUDW,param1,pn))
        #print("Number of wh:{} {}".format( len(warehouse),type (warehouse)  ))
        #If this is a load or unload function, then param1 should be less than whQty
        
        #If attempting to load or unload, must be at a warehouse
        if ( self.LUDW==0 or  self.LUDW==1) and self.location>=len(warehouse):
            self.penalty=  -4 #invalid parameter
        
        #Load: drone 'L' warehouse orderNum qty            
        elif self.LUDW==0  and ( orders[self.order][8]==True or  orders[self.order][4]==True):
            #This order is has already been loaded or previously fulfilled
            self.penalty=  -3.9 
        
        #If a wait state is requested, fields pn and qty must be 0
        #elif self.LUDW==3 and (self.pn!=0 or self.qty!=0):
        #    self.penalty= -2 #invalid command
            
        #elif self.LUDW==3 and self.param1>math.sqrt( (gridRows)**2 + (gridCols)**2 ):  #There is no(?) reason to wait longer than the diag of the game grid
        #   self.penalty=  -2#invalid command
            
        #If product is not onboard for D or U operation, then negative reward
        elif (self.LUDW==1 or self.LUDW==2) and self.pn not in drone[self.droneNum][5:15]:  #U or D
            self.penalty=  -3.5 #invalid command
            
        #If drone is trying to unload from the same location it was loaded at, then penalty
        #elif self.LUDW==1 and  warehouse[self.param1][0:2]==(self.dr,self.dc):  
        #    self.penalty=  -3.2 #invalid command
            
        #If drone is trying to unload from the same location it was loaded at, then penalty
        elif self.LUDW==1 and  priorDroneCmd[self.droneNum] ==0 and warehouse[self.location][0:2]==(self.dr,self.dc):  
            self.penalty=  -10.2 #invalid command
            
        #If Load command, make sure requested warehouse has the product in stock
        elif self.LUDW==0 and warehouse[self.location][whProdOffset+self.pn]==0:
            #Not in stock
            self.penalty=  -3.3
            
        #If Load command, make sure drone has sufficient capacity
        #currentLoad=sum([prodWeight[x] for x in drone[droneNum][dronePayloadOffset:15]])
        #excessCapacity=maxLoad-sum([prodWeight[x] for x in filter(None,drone[droneNum][dronePayloadOffset:15])])
        elif self.LUDW==0 and prodWeight[self.pn]>maxLoad-sum([prodWeight[self.x] for self.x in filter(None,drone[self.droneNum][dronePayloadOffset:15]) ]):
            #Too heavy to load
            self.penalty=  -.1
            
        #emptyPayloadBays=len([x for x in drone[droneNum][5:15] if x==None])
        elif self.LUDW==0 and len([self.x for self.x in drone[self.droneNum][5:15] if self.x==None])==0:
            #No room in the inn Max number of boxes the drone can carry is 10: articicial constraint 
            self.penalty=  -2.1
        
        #Deliver: drone 'D' orderNum prodNum qty            
        elif self.LUDW==2  and orders[self.order][4]==True:
            #This order is already fulfilled
            self.penalty=  -3.4 

        elif self.LUDW==2 and orders[self.order][8]!=True :
            #This is an attempt to deliver an order that hasn't been loaded yet 
            self.penalty=  -3.41     

        elif self.LUDW==2 and self.pn not in drone[self.droneNum][5:15]  :
            #This is an attempt to deliver an order that isn't in the current payload of the specified drone 
            self.penalty=  -3.42  			
              
        ######################################## Main Loop ###########################################    
        #self.unfilledOrders=len([self.k for self.k, self.v in order.items() if self.v[4]==False ])
        else:
            
                
            self.unfilledOrders=len([self.k for self.k, self.v in orders.items() if self.v[4]==False ])
            if self.unfilledOrders>0:

                #droneNum=min(drone.items(), key=lambda k: k[1][4])[0]
                #for droneNum in range(droneQty):    #Next drone should be drone with min destTime 
                self.score=0

                
                #If "LOAD" then fly to the warehouse and load the item
                #set destRow,DestCol to the warehouse location 
                # and destTime to the distance + 1
                if self.LUDW==0:     #droneNum,LUDW,param1,pn,qty  
                    #self.incManifestSeqNum()
                    self.wh=self.location
                    self.wr,self.wc=warehouse[self.wh][0:2]
                    self.dist=math.ceil(distance(self.dr,self.dc,self.wr,self.wc))
                    #entry=(dest_r,dest_c,wr,wc,dest_time+dist+1)
                    updateDrone5(self.droneNum,(self.dest_r,self.dest_c,self.wr,self.wc,self.dest_time+self.dist+1))
                    #Decrement product from warehouse
                    decrementWarehouseQty(self.wh,self.pn)
                    #Add product to drone
                    loadDrone(self.droneNum,self.pn)
                    #Mark order as 'loaded'
                    markOrderLoaded(self.order)
                    ##if priorDroneCmd was also a load then give a reward bonus based on the total drone load
                    if priorDroneCmd[self.droneNum] == 0:
                        #self.bonus=int((sum([prodWeight[self.x] for self.x in filter(None,drone[self.droneNum][dronePayloadOffset:15]) ])/maxLoad)*10)
                        self.bonus=.75
                    else:
                        ##    self.penalty=-(math.log(self.dist)/10)  #negative reward proportional to dist to wh for 1st item
                        ##    self.bonus=0  
                        self.bonus=.25
                    #log
                    DEBUG and print("Drone:{}  L  warehouse:{}  ProdNum:{}  Qty:{}".format(self.droneNum,self.wh,self.pn,1))
                    
                    DEBUG and print("Duration to fly to correct warehouse:{}".format(self.dist+1))
                    #prevWhlist.append(item[itemIndex][0]) #Short term memory of warehouses visited
                
                #If "UNLOAD" then fly to the warehouse and unload the item
                #set destRow,DestCol to the warehouse location 
                # and destTime to the distance + 1
                elif self.LUDW==1:     #droneNum,LUDW,param1,pn,qty  
                    #self.incManifestSeqNum()
                    self.wh=self.location
                    self.wr,self.wc=warehouse[self.wh][:2]
                    self.dist=math.ceil(distance(self.dr,self.dc,self.wr,self.wc))
                    updateDrone5(self.droneNum,(self.dest_r,self.dest_c,self.wr,self.wc,self.dest_time+self.dist+1))
                    #Increment product at warehouse
                    incrementWarehouseQty(self.wh,self.pn)
                    #Remove product from drone
                    unloadDrone(self.droneNum,self.pn)
                    #If warehouse had less than 2 of these items then bonus
                    if warehouse[self.wh][whProdOffset+self.pn]<2:
                        self.bonus=10
                    #if priorDroneCmd was also an unload then give no penalty
                    elif priorDroneCmd[self.droneNum] == 1 or self.dist==0:
                        self.bonus=.66
                    else:
                        self.bonus=(1/math.log(self.dist))
                    #self.reward=-self.dist
                    #self.reward=0
                    #log
                    DEBUG and print("Drone:{}  U  warehouse:{}  ProdNum:{}  Qty:{}".format(self.droneNum,self.wh,self.pn,1))
                    
                    DEBUG and print("Duration to fly to correct warehouse:{}".format(self.dist+1))
                    #prevWhlist.append(item[itemIndex][0]) #Short term memory of warehouses visited
                    

                #If "DELIVER" then fly to the customer and deliver the item
                #set destRow,DestCol to the Order location 
                # and destTime to the distance + 1
                elif self.LUDW==2:     #droneNum,LUDW,orderNum,pn,qty  
                    #self.incManifestSeqNum()
                    self.orderIndex=self.order
                    self.cr,self.cc=orders[self.orderIndex][0],orders[self.orderIndex][1]
                    self.dist=math.ceil(distance(self.dr,self.dc,self.cr,self.cc))
                    self.newDestTime=self.dest_time+self.dist+1
                    updateDrone5(self.droneNum,(self.dest_r,self.dest_c,self.cr,self.cc,self.newDestTime))
                    self.filledOrders=len([self.k for self.k, self.v in orders.items() if self.v[4]==True ])
                    self.unfilledOrders=len([self.k for self.k, self.v in orders.items() if self.v[4]==False ])
                    #Mark order as fulfilled
                    markOrderFulfilled(self.orderIndex)
                    #Remove product from drone
                    unloadDrone(self.droneNum,self.pn)
                    #order[orderIndex][4]==True
                    #score
                    self.reward= ( ( ((deadline-self.newDestTime)/deadline) *100 ) ) 
                    #ic(self.orderIndex,self.cr,self.cc,self.dist,self.reward)

                    self.total_reward+=self.reward
                    #log
                    DEBUG and print("Drone:{}  D  Order:{}  ProdNum:{}  Qty:{}".format(self.droneNum,self.orderIndex,self.pn,1))
                    
                    DEBUG and print("Duration to fly to customer:{}".format(self.dist+1))
                    
                elif self.LUDW==3:    #Waiting  param1=duration
                    #manifestSeqNum+=1 
                    #self.incManifestSeqNum()                    
                    updateDrone5(self.droneNum,(self.dr,self.dc,self.dest_r,self.dest_c,self.dest_time+self.location))

                    #score
                    self.reward= 0
                    #log
                    DEBUG and print("Drone:{}  Wait  Duration:{}  ".format(self.droneNum,self.location))
                    
                else:
                    print("Invalid option: action(droneNum:{},LUDW:{},location:{},order:{},qty:{}".format(self.droneNum,self.LUDW,self.location,self.order,self.qty))
                    raise SystemExit("Stop right there!") 
        self.droneLoc=locations[drone[self.droneNum][2:4]]    
                
        #result=outputFile.write( str(manifestSeqNum)+","+str(microScore)+","+str(filledOrders)+","+str(droneNum)+","+str(droneLoc)+","+str(drone[droneNum][5:15]) +'\n')
        #No longer needed
        #self.payloadItems=  len([self.x for self.x in drone[self.droneNum][5:15] if self.x!=None] )#last is # of items onboard  
            
        
        #print("manifestSeqNum:{},microScore:{},macroScore:{},droneNum:{},droneLoc:{},payloadItems:{}".format(manifestSeqNum,microScore,macroScore,droneNum,droneLoc,payloadItems))
        
        #self.total_reward =len([self.k for self.k, self.v in order.items() if self.v[4]!=False ])
        if self.penalty<0:
            self.reward=self.penalty
        elif self.bonus>0: #Value 1-10 are the bonus for 
            self.reward=self.bonus
        #elif self.reward>0:
        #    self.reward=self.total_reward
        
        self.prev_reward = self.total_reward

        info = {}
        
        self.incManifestSeqNum()
        
        #if 5>self.getManifestSeqNum()>0:
        #    print("Hit manifest seq number of {}".format(self.getManifestSeqNum()))
        #if self.getManifestSeqNum()>=len(order)*9:
        if self.getManifestSeqNum()>=len(orders)*9:
            self.filledOrders=len([self.k for self.k, self.v in orders.items() if self.v[4]==True ])
            self.unfilledOrders=len([self.k for self.k, self.v in orders.items() if self.v[4]==False ])
            self.other=len([self.k for self.k, self.v in orders.items() if self.v[4]!=False and self.v[4]!=True])
            print("Hit manifest seq number limit of {} Ending episode with {} successful deliveries".format(self.getManifestSeqNum(),self.filledOrders))
            #ic(self.filledOrders,self.unfilledOrders,self.other)
            self.done=True 
        self.currentPayload=sum([prodWeight[x] for x in filter(None,drone[self.droneNum][dronePayloadOffset:15]) ])
        #if self.filledOrders/len(orders)>.80:
        #    print("80% of orders completed! ({}) in {} manifest steps".format(self.filledOrders,self.getManifestSeqNum()))
        #    self.done=True 
        if self.unfilledOrders==0:
            print("All orders completed! ({}) in {} manifest steps".format(self.filledOrders,self.getManifestSeqNum()))
            self.done=True 

        # create observation:
        #observation = [manifestSeqNum,macroScore,droneNum,droneLoc,payloadItems] + list(self.prev_actions)
        whStat=list()
        radius=30
        for wh in range(Warehouse.getQty()): 
            whStat.append( ( wh, dronesInRadius(wh,radius),ordersInStockClose(wh,radius), ordersInStockFar(wh,radius), ordersunfilled(wh)) )       ########################
        #Whstat=wh,closeProxInstockOrders,instockOrders,outOfStockOrders, dronesInArea
        
        observation = [self.getManifestSeqNum(),droneNum,wh, whStat] 
        observation = np.array(observation)
        #print("Observation:{}   shape:{}".format( observation,observation.shape))
                #Store the prior LUDW command for later use (but only if successful)
        if self.reward>=0:
            priorDroneCmd[self.droneNum] = self.LUDW
            
        return observation, self.reward, self.done, info

    def reset(self):
        consumeInputFile2()
        createOrdArray()
        self.resetManifestSeqNum()
        #self.resetManifestSeqNum=0
        #self.resetMacroScore()
        self.total_reward=0
        self.prev_reward = 0
        self.filledOrders = 0
        self.droneNum=0
        self.droneLoc=0
        self.currentPayload=0
        #[ priorDroneCmd.update({x:3}) for x in range(30) ]
        droneNum=0
        
        self.done = False

        # create observation:

        whStat=list()
        radius=30
        for wh in range(Warehouse.getQty()): 
            whStat.append( ( wh, dronesInRadius(wh,radius),ordersInStockClose(wh,radius), ordersInStockFar(wh,radius), ordersUnfilled(wh)))        ########################
        #Whstat=wh,closeProxInstockOrders,instockOrders,outOfStockOrders, dronesInArea
        
        observation = [self.getManifestSeqNum(),droneNum,wh, whStat] 
        observation = np.array(observation)
                          
        return observation
        
        
        
        
        
class Data(DroneEnv):
    clock=0
    score=0
    scoreList=list()
    
    def __init__(self):
        super(Data, self).__init__()
        self.name="data parent object"  
        self.clock=99
    def clockTick():
        Data.clock+=1
        return
    def incScore(n):
        Data.score+=n
    def addScoreTup(tup):
        Data.scoreList.append(tup)
    def getScore():
        return Data.score
    def getScoreListLen():
        return len(Data.scoreList)
    
class Algo(DroneEnv):
    def __init__(self):
        super().__init__()
        self.name="Algorithm parent object"
    
class Calculate(Algo):                    ############ A L G O ##################
    def __init__(self):
        super().__init__()
        
              
      
    def deliverLocally(self):
        for wh in range(Warehouse.getQty()): 
            #Each warehouse was designated drones to serve it's local customer orders
            theseDrones=w[wh].getDroneList()
            #t<2 and print("The drones assigned to Wh#{} are: {}".format(wh,theseDrones))
            #t<2 and print("Searching for orders for warehouse:{} ".format(wh))
            for droneNum in theseDrones:
                #t<2 and print("   Wh#{} Determining load for Drone:{}".format(wh,droneNum))
                if d[droneNum].isAvail():
                    #t<2 and print("   Wh#{} Preparing to load drone#{}...".format(wh,droneNum))
                    r,c=d[droneNum].getPos()
                    excessCapacity=d[droneNum].getExcessCapacity()
                    priorityList=w[wh].getLocalPriorityList()
                    if len(priorityList)==0:
                        #print("\t\t\tWh#{} Nothing left to load for drone:{}".format(wh,droneNum))
                        break
                    minimumWeightInList=w[wh].getPriorityListMinWeight()
                    #make sure an option is available, if not, proceed to next
                    endOfOrders=False
                    #print("ExcessCap:{}  minWeightinList:{}".format(excessCapacity,minimumWeightInList))
                    while  excessCapacity >= minimumWeightInList and not endOfOrders:   
                        allowIntermodal=False
                        orderIndex=w[wh].popNextOrder(excessCapacity,allowIntermodal)
                        if isinstance(orderIndex,bool) and orderIndex==False:   #False indicates no valid orders to load
                            endOfOrders=True
                        else:
                            #ord[orderIndex].showStatus()
                            #print("\tWh#{} Loaded order {} onto drone:{}".format(wh,orderIndex,droneNum))
                            weight=ord[orderIndex].getWeight()
                            itemIdx=ord[orderIndex].getAssignedItem()
                            result=d[droneNum].load(orderIndex,wh,ord[orderIndex].getProdNum(),1,itemIdx,weight)

                            excessCapacity=d[droneNum].getExcessCapacity()
                            #print("\tWh#{} Drone: {}  remaining capacity: {}".format(wh,droneNum,excessCapacity))
                            priorityList=w[wh].getPriorityList()
                            if len(priorityList)==0:
                                break
                            minimumWeightInList=w[wh].getPriorityListMinWeight()

                    #print("Drone: {} is loaded with {} boxes ".format(droneNum,d[droneNum].getNumItems()))
                    r,c=d[droneNum].getDest()
                    if d[droneNum].getNumItems()>0:
                        DEBUG and print("Wh#{} Drone #{} has {} boxes Next stop:{},{} at time: {}"\
                          .format(wh,droneNum,d[droneNum].getNumItems(),r,c,d[droneNum].getDestTime()))
        #raise SystemExit("Stop right there!")   
    def getImMinWeight(imList):
        minWeight=maxLoad
        for tup in imList:
            #(closestWh,orderIndex,itemIndex)
            _,_,ii=tup
            weight=item[ii].getWeight()
            if weight<minWeight:
                minWeight=weight
        return minWeight
    def selectOrder(imList,excessCapacity):
        selectionLessThanEC=False
        for index,tup in enumerate(imList):
            #(closestWh,orderIndex,itemIndex)
            _,oi,ii=tup
            weight=item[ii].getWeight()
            if weight<excessCapacity:
                selectionLessThanEC=oi
                break
        return selectionLessThanEC
    
    def getAllOrdersForWh(wh):
        orderList=list()
        wr,wc=w[wh].getPos()
        for i in range(Order.getQty()):
            if ord[i].getWh()==wh:
                r,c=ord[i].getPos()
                dist=Calculate.dist( (r,c),(wr,wc) )
                orderList.append( (i,dist)   )
        #Now sort the generated list of tuples by distance
        orderList.sort(reverse=False,key = lambda x: x[1])
        return orderList
    def subScores():   #subScore is the maxmimum score for this item to be completed. (intermodal dist+ local dist)
        for orderIndex in range(Order.getQty()):
            subScore=0
            imDist,whDist= ord[orderIndex].getDistances()
            minTimeToComplete=imDist+whDist
            #if there was an intermodal transfer required, add 2 time units for the load/unload
            if imDist>0:
                subScore=2
            subScore+=imDist+whDist+2 #the +2 is for local warehouse load/delivery unload
            ord[orderIndex].setSubScore( subScore )
    def maxScores():   #MaxScore is the maxmimum score for the whole orig order to be completed(sum of subscores)
        for orderIndex in range(Order.getQty()):
            origOrder=ord[orderIndex].getOrderNum()
            minTimeToComplete=0
            for i in range(Order.getQty()):
                if ord[i].getOrderNum()==origOrder:
                    minTimeToComplete+=ord[i].getSubScore()
            maxScore=((deadline-minTimeToComplete)/deadline)*100
            ord[orderIndex].setMaxScore( maxScore )
    def maxScores0():   #MaxScore is the maxmimum score for the whole orig order to be completed(sum of subscores)
        for orderIndex in range(Order.getQty()):
            origOrder=ord[orderIndex].getOrderNum()
            minTimeToComplete=0
            for i in range(Order.getQty()):
                if ord[i].getOrderNum()==origOrder:
                    imDist,whDist= ord[i].getDistances()
                    #print("{}  {}".format(i,ord[i].getDistances()))
                    minTimeToComplete+=imDist+whDist
            maxScore=(deadline-minTimeToComplete)/deadline
            ord[orderIndex].setMaxScore( maxScore )
    def finalStats():
        finalTime=Calculate.currentTime()
        #show total order qty
        print("Total orders possible:{}  originally in stock:{}  ".format(Order.getQty(), origInStockCounter ))
        print("Total intermodal transfers completed:{}"  .format(intermodalXfersCompleted)  )
        #Show order qty delivered
        filled=0
        unfilled=0
        totalScore=0
        #print("OrdIndex fulfilled  remItems  isAssigned  assignedItemIndex turnFulfilled\n"+'-'*50)
        for i in range(Order.getQty()):
            fulfilled, remItems,isAssigned,assignedItemIndex,turnFulfilled=ord[i].getEndStatus()
            DEBUG and print(i,fulfilled, remItems,isAssigned,assignedItemIndex,turnFulfilled)
            if fulfilled:
                filled +=1
            else:
                unfilled+=1
        print("Filled:{}   Unfilled:{}".format(filled,unfilled)) 
        self.finalScore(finalTime)
        
    def finalScore(endTime):
        #Calc final score for this sim

        finalScore=0
        for i in range(totalOrders):   #totalOrders came from the reading of the orig input file
            #print("Processing orderNum:{} of {}".format(i,totalOrders))

            lastDeliveryTime=endTime  #initialize to a large num
            foundFulfilled=False
            for oi in range(Order.getQty()):
                if ord[oi].getOrderNum()==i and ord[oi].getRemItems()==0:   #in the list of orderlines, just look at the ones that match the orderNum
                    foundFulfilled=True
                    #print('FulfilledTime:{} {}'.format( ord[oi].getFulfilledTime() ,  isinstance(ord[oi].getFulfilledTime(),int) ) )
                    if not isinstance(ord[oi].getFulfilledTime(),bool) and ord[oi].getFulfilledTime()< lastDeliveryTime:
                        #print('<{}'.format(lastDeliveryTime),end='')
                        lastDeliveryTime=ord[oi].getFulfilledTime()
                        #print("Updating last delivery time to:{}".format(lastDeliveryTime))

                        #itemsInThisOrder=ord[oi].getItemsInOrder()
            if foundFulfilled:
                thisScore=math.ceil(  (  (endTime-lastDeliveryTime) /endTime)  * 100 )
                finalScore+= thisScore
                DEBUG and print("Order:{} score:{}".format(i,thisScore))
        print("Final score:{} at final time:{}".format(finalScore,endTime))  
        return finalScore
        
    def nearestWh(r,c,whSubList=list()):
        if len(whSubList)==0:
            whSubList=list(range(Warehouse.getQty() ))
        #print("Looking for warehouse closest to: {},{}".format(r,c) )
        maxDist=gridRows+gridCols  #Max possible value
        closestDist=maxDist
        closestWhIndex=-1  
        for index,(wr,wc) in enumerate(whLocs):
            if index not in whSubList:
                continue
            distance=Calculate.dist((r,c),(wr,wc)) 
            if distance<closestDist:
                closestDist=distance
                closestWhIndex=index
        #print("Closest warehouse is:{}".format(closestWhIndex) )
        return closestWhIndex 

    def findAvailProdInWh(pn,wh):
        for i in range(Item.getQty()):
            itemIndex,assigned,prodNum,facType,facIndex=item[i].getStatus3()
            if prodNum==pn and facType=='W' and facIndex==wh and assigned==False:
                break
        return itemIndex
            
    def getStatus3():
        #itemIndex,OrderIndex,prodNum,facType,facIndex
        return (self.__index,self.__assignedToOrder,self.__prodNum,self.__facType,self.__facIndex)
    
    def nearbyWh(r,c,whLocList):
        distToWh=list()
        #If the drone is already at a warehouse location then just return that loc
        for index,(wr,wc) in enumerate(whLocs):
            distToWh.append( dist((r,c),(wr,wc))  )
        #now return the index of the minimal value in the list
        minpos = distToWh.index(min(distToWh))
        #print("The closest warehouse to {},{} is at index {} at a distance of:{}".format(r,c,minpos,min(distToWh)))
        return minpos,min(distToWh)
    def getNewLocation(currR,currC,destR,destC,timeInterval=1):
        adjacent=destR-currR
        opposite=destC-currC
        hyp=math.sqrt(adjacent**2+opposite**2)
        angleRadians=math.atan2(opposite,adjacent)
        #print("Opposite:{}   Adj:{}   Angle:{} Hyp:{}".format(opposite,adjacent,angleRadians,hyp))
        newRow=currR+math.cos(angleRadians)*timeInterval
        newCol=currC+math.sin(angleRadians)*timeInterval
        if hyp<1:
            return destR,destC
        return newRow,newCol
    def decodeLabel(labelString):
        if ('L' in labelString) or ('D' in labelString):
            label=labelString.split()
            droneNum=int(label[0])
            DLW=label[1]
            wh=int(label[2])
            prodNum=int(label[3])
            qty=int(label[4])
            wait=False
            return (droneNum,DLW,wh,prodNum,qty,wait)
        if ('D' in labelString):
            label=labelString.split()
            droneNum=int(label[0])
            DLW=label[1]
            wait=int(label[2])
            wh=False
            prodNum=False
            qty=False
            return (droneNum,DLW,wh,prodNum,qty,wait)
        return (False,False,False,False,False,False)
    
        
    def genLabel(labelTup,labelType):
        DLW=labelType
        if 'L' in  labelType:
            droneNum,DLW,warehouseNum,prodNum,prodQty,_,_,_,weight=labelTup
            label=str(droneNum)+' '+DLW+' '+str(warehouseNum)+' '+str(prodNum)+' '+str(prodQty)
        elif 'D' in  labelType:
            droneNum,DLW,_,prodNum,prodQty,orderIndex,_,itemIndex,weight=labelTup
            #Fetch the original item number using the order index
            orderNum=ord[orderIndex].getOrderNum()
            label=str(droneNum)+' '+'D'+' '+str(orderNum)+' '+str(prodNum)+' '+str(prodQty)
        elif 'I' in  labelType:
            #droneNum,DLW,_,prodNum,prodQty,orderIndex,_,itemIndex,weight=labelTup
            droneNum,DLW,warehouseNum,prodNum,prodQty,orderIndex,_,itemIndex,orderWeight=labelTup
            orderNum=ord[orderIndex].getOrderNum()
            label=str(droneNum)+' '+'U'+' '+str(warehouseNum)+' '+str(prodNum)+' '+str(prodQty)
        elif 'U' in  labelType:
            #droneNum,DLW,_,prodNum,prodQty,orderIndex,_,itemIndex,weight=labelTup
            droneNum,DLW,warehouseNum,prodNum,prodQty,orderIndex,_,itemIndex,orderWeight=labelTup
            orderNum=ord[orderIndex].getOrderNum()
            label=str(droneNum)+' '+'U'+' '+str(warehouseNum)+' '+str(prodNum)+' '+str(prodQty)        
        elif 'W' in labelType:    
            droneNum,DLW,_,_,_,_,wait,_,weight=labelTup
            label=str(droneNum)+' '+DLW+' '+str(wait)
        #print ("Generated label:{} of type:{}".format(label,type(label)))
        return label
    def genOrderList(r,c):   #Unused
        #return a list of orders in the neighborhood with score and dist from r,c and dist from nearest neighbor 
        potentialOrdList=list()
        
        potentialOrdList=Calculate.genOrderList(w[wh].getPos())    
      
    def warehouseWithProdRandom(prodNum,w,item):
        #Identify a random warehouse that has this product. 
        #Question: Will the product still be there when the drone arrives??
        #print("Looking for product number:{} in any warehouse".format(prodNum))
        #tempWHlist=list()
        r = list(range(Item.getQty()))
        random.shuffle(r)
        #print("Quantity of items:   Item.getQty() {}".format(Item.getQty()))
        for i in r:
            #print("item[i].getFacType:{}   item[i].getProdNum():{}".format(item[i].getFacType(),item[i].getProdNum()))
            if item[i].getFacType()=='W' and item[i].getProdNum()==prodNum:    
                return item[i].getWarehouseNum()   
        return False
    def warehousesWithProd(r,c,prodNum,w,item):
        #Identify all warehouses that have this product. 
        #Question: Will the product still be there when the drone arrives??
        
        #print("Looking for product number:{} in warehouses".format(prodNum))
        itemlist=list()
        tempWHlist=list()
        #print("Quantity of items:   Item.getQty() {}".format(Item.getQty()))
        for i in range(Item.getQty()):
            #print("item[i].getFacType:{}   item[i].getProdNum():{}".format(item[i].getFacType(),item[i].getProdNum()))
            if item[i].getFacType()=='W' and item[i].getProdNum()==prodNum:    
                tempWHlist.append(item[i].getWarehouseNum() )  
        return tempWHlist
    
    
    def loadList(r,c,maxLoad,w,item):
        #Find optimal orders to fulfill by calculating the score for the delivery of each product
        DEBUG and print("Looking for product number:{} in warehouses".format(prodNum))
        itemlist=list()
        tempWHlist=list()
        #print("Quantity of items:   Item.getQty() {}".format(Item.getQty()))
        for i in range(Item.getQty()):
            if item[i].getFacType()=='W':    
                 tempWHlist.append(item[i].getWarehouseNum() )  
        #print("Warehouses with the product:{} are:()".format(prodNum,tempWHlist))
        costFnList=list()
        return costFnList
        #for orderNum in range(Order.getQty()):
        #    if ord[orderNum].isFulfilled()==True or ord[orderNum].msgQueue()==True:
        #        costFnList.append(0)            
    def updateRemItems(ordIndex):                            ################################################
        #Given this single-item order index, find other lines from this same order by using the common orderNum
        if ord[ordIndex].getRemItems()==0:
            print("Error 007: Remaining items is already 0. This shouldn't happen.")
            return False
        targetOrderNum=ord[ordIndex].getOrderNum()
        linesInThisOrderList=list()
        for i in range(Order.getQty()):
            index,row,col,orderNum,prodNum,remItems= ord[i].getStatus()
            if orderNum==targetOrderNum:
                linesInThisOrderList.append(index)
        orderLineQty=len(linesInThisOrderList)
        #Now count the number that are fulfilled
        fulfilledCount=0
        for i in linesInThisOrderList:
            if ord[i].isFulfilled():
                fulfilledCount+=1
        remItems=len(linesInThisOrderList)-fulfilledCount
        #Update the ord[].setRemItems(n) for each
        for i in linesInThisOrderList:
            ord[i].setRemItems(remItems)
        return remItems
  
    def getRandomUnfilledOrder(ord):                     
        #tempUnfilledOrderList=list()
        r = list(range(Order.getQty()))
        random.shuffle(r)
        for i in r:
            if ord[i].isFulfilled()==False: 
                return ord[i].getStatus()              
        return False
    def getRemainingOrders():
        unfilledOrders=0
        unfilledOrdersList=list()
        for i in range(Order.getQty()):
            if ord[i].isFulfilled()==False:
                unfilledOrders+=1
                unfilledOrdersList.append(i)
        return unfilledOrders,unfilledOrdersList
            
    def getNearbyUnfilledOrders(warehouseIndex,k):       ####This is the most CPU intensive routine
        wr,wc=w[warehouseIndex].getPos()
        #allOrderlocs is a permanent list of the location of all orders
        X=np.array(allOrderlocs)
        x=np.array([[wr,wc]])
        inds = knn(x, X, k)
        potentialOrderList=list()
        for i in inds:
            #print(ord[i].getStatus())
            if ord[i].isFulfilled()==False:
                #print('=',end='')
                prodNum=ord[i].getProdNum()
                if Calculate.checkStock(warehouseIndex,prodNum)==True:
                    #print("Found the product in warehouse!!")
                    potentialOrderList.append(i)            
        return potentialOrderList
    def getAvgDistNearbyUnfilledOrders(r,c,k):
        #allOrderlocs is a permanent list of the location of all orders
        X=np.array(allOrderlocs)
        x=np.array([[r,c]])
        inds = knn(x, X, k)
        xyList=list()
        nextWhDist=list()
        for i in inds:
            #print(ord[i].getStatus())
            if ord[i].isFulfilled()==False:
                orderRow,orderCol=ord[i].getPos()
                xyList.append( Calculate.distance(orderRow,orderCol,r,c) ) 
                _,whDist=Calculate.nearbyWh(r,c,whLocs)
                nextWhDist.append( whDist )
        return np.mean(xyList),np.mean(nextWhDist)
    
    def orderMetrics(droneRow,DroneCol,wr,wc,potentialOrdList):      
        orderMetricsList=list()
        for i in potentialOrdList:
            index,row,col,orderNum,prodNum,remItems= ord[i].getStatus()
            weight=ord[i].getWeight()
            #compute dist to wh, nearest neighbor, 
            droneDist=dist((wr,wc),(droneRow,DroneCol) )
            whDist=dist((wr,wc),(row,col) )
            score=((deadline-(Calculate.currentTime()+droneDist+whDist))/deadline) /(remItems)
            #score=((deadline-(Calculate.currentTime()+droneDist+whDist))/deadline) 
            distToNeighbors,neighborAvgDistToWh=Calculate.getAvgDistNearbyUnfilledOrders(row,col,4)
            orderMetricsList.append((i,score,distToNeighbors,neighborAvgDistToWh,weight))
        return orderMetricsList
    
    
    def getRandomAvailableDrone(d):
        r = list(range(Drone.getQty()))
        random.shuffle(r)
        for i in r:
            if d[i].isAvail()==True: 
                return d[i].getStatus()              
        return False
    def distance(r1,c1,r2,c2):
        return math.sqrt(    ( r1-r2   )**2 +  ( c1-c2  )**2     )
    def dist(tup1,tup2):
        (r1,c1)=tup1
        (r2,c2)=tup2
        return math.sqrt(    ( r1-r2   )**2 +  ( c1-c2  )**2     )
    def currentTime():
        return Data.clock
    def inStock(wh,pn):
        #print("Does warehouse:{} have prodNum:{}?".format(wh,pn))
        for i in range(Item.getQty()):
            itemIndex,prodNum,facType,facIndex,assignedToOrder=item[i].getStatus2()
            #print("Next: {}/{} {}/{} {}/{} ".format(prodNum,pn,facType,'W',facIndex,wh))
            
            if facType=='W' and facIndex==wh and prodNum==pn and assignedToOrder==False :
                DEBUG and print("Product {} is in stock (and available) at wh:{}".format(pn,wh))
                return True
        return False         
    def checkStock(wh,orderId,itemId,pn):
        DEBUG and print("Does warehouse:{} have order:{} which is assigned item:{} (Prod={})?".format(wh,orderId,itemId,pn))
        #for i in range(totalItemsInSim):
        #print("ItemID:{} {}".format(itemId,type(itemId)))
        itemIndex,OrderIndex,prodNum,facType,facIndex=item[itemId].getStatus3()
        #print("Check: {}/{} {}/{} {}/{} {}/{} {}/{}".format(orderIndex,orderId,itemIndex,itemId,facType,'W',facIndex,wh,prodNum,pn))
            
        if facType=='W' and facIndex==wh and itemIndex==itemId and prodNum==pn:
            #print("Product {} is in stock at wh:{}".format(pn,wh))
            return True
        else:
            DEBUG and print("facType=='W'   {}=={}  {}   {}  {}".format (facType,'W',facType=='W',type(facType),type('W')))
            DEBUG and print("facIndex==wh   {}=={}  {}   {}  {}".format (facIndex,wh,facIndex==wh,type(facIndex),type(wh)))
            DEBUG and print("itemIndex==itemId   {}=={}  {}   {}  {}".format (itemIndex,itemId,itemIndex==itemId,type(itemIndex),type(itemId)))
            DEBUG and print("prodNum==pn   {}=={}  {}   {}  {}".format (prodNum,pn,prodNum==pn,type(prodNum),type(pn)))
        return False 
    def checkItem(wh,orderId,itemId):
        print("Order:{} Does the item #{} show it is located in this warehouse({})?".format(orderId,itemId,wh))
        #for i in range(totalItemsInSim):
        
        itemIndex,OrderIndex,prodNum,facType,facIndex=item[itemId].getStatus3()
        DEBUG and print("Check: {}/{} {}/{} {}/{} {}/{} ".format(orderIndex,orderId,itemIndex,itemId,facType,'W',facIndex,wh))
            
        if facType=='W' and facIndex==wh and itemIndex==itemIdx:
            #print("Product {} is in stock at wh:{}".format(pn,wh))
            return True
        else:
            DEBUG and print("facType=='W'   {}=={}  {}   {}  {}".format (facType,'W',facType=='W',type(facType),type('W')))
            DEBUG and print("facIndex==wh   {}=={}  {}   {}  {}".format (facIndex,wh,facIndex==wh,type(facIndex),type(wh)))
            DEBUG and print("itemIndex==itemIdx   {}=={}  {}   {}  {}".format (itemIndex,itemId,itemIndex==itemId,type(itemIndex),type(itemId)))
        return False 
    
    def xfer2Drone(itemIndex,droneNum):    
        #are item and drone in the same location??

        result=item[itemIndex].droneLoad(droneNum)
        return result

    def showLog():
        for i in range(len(log)):
            print(log[i].getLine())
        return
    
    
class Log(Data):    ########## Logfile to store commands  #######
    counter=-1
    def __init__(self,logString):
        super().__init__()
        Log.counter += 1
        self.__logString=logString
    def getCount():
        return Log.counter
    def getQty():
        return Log.counter
    def getLine(self):
        return self.__logString
    def show(self):
        print(self.__logString)
    def showAll():
        for i in range(Log.getQty()):
            log[i].show()
    def showAllForDrone(dn):
        for i in range(Log.getQty()):
            line=log[i].getLine().split()
            if int(line[0])==dn:
                print(line)
            
        
    
class Warehouse(Data):              ####  Warehouse ####
    counter=0
    def __init__(self,warehouseNum,row,col):
        self.__index=Warehouse.counter
        Warehouse.counter += 1
        super().__init__()
        #self.counter += 1
        self.__warehouseNum=warehouseNum
        self.__intermodalList=list()
        self.__row=row
        self.__col=col
        self.__droneList=list()
        self.__priorityList=list()
    def generatePriorityList(self):
        self.__priorityList=list()
        #create list of all orders for this wh with associated metrics tuple
        #Priority list fields: index,maxscore,weight,intermodal
        for i in range(Order.getQty()):
            if ord[i].getWh()==self.__warehouseNum and not ord[i].isFulfilled() and not ord[i].getDeliveryInProcess()==True:
                #print("Orders: {}".format(i))
                ms=ord[i].getMaxScore()
                self.__priorityList.append( (i,ms,ord[i].getWeight(),ord[i].isIntermodal()) )
        self.__priorityList.sort(reverse=True,key = lambda x: x[1])
        #print("Priority:{}".format(self.__priorityList))
        #return self.__priorityList
    def showPriorityList(self):
        print("orderIndex,maxscore,weight,intermodal True/False")
        print("Warehouse:{} Priority List:{}".format(self.__warehouseNum,self.__priorityList))
    def getPriorityList(self):
        return self.__priorityList
    def getLocalPriorityList(self):
        localList=list()
        for i in range(len(self.__priorityList)):
            oi,ms,weight,im=self.__priorityList[i]
            if not ord[oi].isIm():
                localList.append(self.__priorityList[i])
        return localList
        #return self.__priorityList
    def getPriorityListMinWeight(self):
        #Find minimum weight in prioritized list that is not intermodal
        PriorityListNoIm = [item for item in self.__priorityList if item[3] == False ]
        if len(PriorityListNoIm)==0:
            return False
        _,_,minimumWeightInList,isIntermodal = min(PriorityListNoIm, key=lambda tup: tup[2])
        return minimumWeightInList
    def popNextOrder(self,maxWeight,allowIntermodal):
        #if allowIntermodal is false, don't include orders with an itemNum type tuple
        #Priority list fields: index,maxscore,weight,intermodal
        #print("popnextOrder:   AllowIntermodal:{}".format(allowIntermodal))
        for i in range(len(self.__priorityList)):   
            if self.__priorityList[i][2]<=maxWeight:
                #print("Priority list item:{} is < maxweight:{}".format(i,maxWeight))
                #print(self.__priorityList[i][3], allowIntermodal)
                if (self.__priorityList[i][3]==False or allowIntermodal==True) :
                    ordIndex=self.__priorityList[i][0]
                    #print("ordIndex:{}   delivery in process:{}".format(ordIndex,ord[ordIndex].getDeliveryInProcess()))
                    if ord[ordIndex].getDeliveryInProcess()!=True:
                        DEBUG and print("Length of self.__priorityList: {}  i={}".format(len(self.__priorityList),i))
                        self.__priorityList.pop(i)
                        DEBUG and print("returning order index :{}".format(ordIndex))
                        return ordIndex
        return False
    def assignDrone(self,droneNum):
        self.__droneList.append(droneNum)
    def getDroneList(self):
        return self.__droneList
    def getStatus(self):
        return self.__warehouseNum,self.__row,self.__col
    def getCount(self):
        return self.counter
    def getQty():
        return Warehouse.counter
    def reset():
        Warehouse.counter=0
    def getPos(self):
        return self.__row,self.__col                           
    def addToIntermodalList(self,tup):
        self.__intermodalList.append(tup)
    def removeFromIntermodalList(self,target_oi,target_ii):
        #print("Request for removal of ord:{} item:{} from IM list on Wh:{}".format(target_oi,target_ii,self.__warehouseNum))
        for i in range(len(self.__intermodalList)):
            sourceWh,oi,ii= self.__intermodalList[i]
            if isinstance(target_ii,tuple):
                #print("Converting tuple: {}".format(target_ii))
                target_ii,donorWh=target_ii
            if oi==target_oi and ii==target_ii:
                self.__intermodalList.pop(i)
                #print("Success!")
                return True
        #print("Failed.")
        return False
        
    def getIntermodalList(self,wh=-1):
        #(closestWh,orderIndex,itemIndex)
        #By default (wh=-1) return the whole list
        # otherwise only return the tuples from the warehouses in the provided list
        ## new feature: do not include orders that are currently being flown intermodally
        newList=list()
        if wh==-1:
            for tup in self.__intermodalList:
                closestWh,orderIndex,itemIndex=tup
                if ord[orderIndex].getIntermodal()!=True:
                    newList.append( (closestWh,orderIndex,itemIndex)    )
            return newList
        else:
            #print("searching for Wh={}".format(wh))
            imList = [tup for tup in self.__intermodalList if tup[0] == wh]
            for tup in imList:
                closestWh,orderIndex,itemIndex=tup
                if ord[orderIndex].getIntermodal()!=True:
                    newList.append( (closestWh,orderIndex,itemIndex)    )
            return newList
            
    def getInventory(self,itemObj,totalItemsInSim):
        #print("Item is type {}".format(itemObj))
        #itemQuantity=itemObj[0].getQty()
        #print("itemQuantity:{}".format(itemQuantity))
        itemCount=0
        for i in range(totalItemsInSim):
            if itemObj[i].getWarehouse()==('W',self.__warehouseNum):
                itemCount+=1
        return itemCount
    def loadInitialProduct(self,p,productNum,qty):
        p[productNum].addItem(qty,'W',self.__warehouseNum)


class ProductType(Data):               ############## ProductType Object ############
    counter=0
    def __init__(self,prodNum,weight):
        super().__init__()
        self.counter += 1
        self.__prodNum=prodNum
        self.__weight=weight
        self.__qty=0
        self.__itemList=list()
    def reset():
        ProductType.counter=0
    def getWeight(self):
        return self.__weight
    def getStatus(self):
        return (self.__prodNum,self.__weight)
    def addItem(self,qty,facilityType,facilityNum):
        #print("Adding item: {} with qty:{} at {}{}".format(self.__prodNum,qty,facilityType,facilityNum))
        for ii in qty:
            #print('.',end='')
            self.__itemList.append(self.__qty)
            self.__qty+=1
            #print("self.__itemList:{}".format(self.__itemList))
            
            #self.__item[self.__itemList[self.__qty]].load(self.__prodNum,self.__weight,(facilityType,facilityNum))
        return
        
        
class Item():              ############## Item Object ############
    counter=0
    def __init__(self,prodNum,facType,facIndex,weight):
        #super().__init__(prodNum,weight)
        self.__index=Item.counter
        Item.counter += 1
        self.__prodNum=prodNum
        self.__weight=weight
        self.__facType=facType   #indicating D,W or C  for Drone/Warehouse/Cust
        self.__facIndex=facIndex  #index of container D/W/C           
        self.__deliveryTime=-1
        self.__assignedToOrder=False
        #print("Instantiated new item object")
    def setLoc(self,facType,facIndex):
        self.__facType,self.__facIndex=facType,facIndex
    def getQty():
        return Item.counter
    def reset():
        Item.counter=0
    def getWeight(self):
        return self.__weight
    def getWarehouse(self):
        return self.__facType,self.__facIndex
    def getWarehouseNum(self):
        return self.__facIndex
    def getFacType(self):
        return self.__facType    
    def getProdNum(self):
        return self.__prodNum
    def load(self,prodNum,facType,facIndex):
        self.counter += 1
        self.__prodNum=num
        self.__weight=weight
        self.__facType=facType   #indicating D,W or C  for Drone/Warehouse/Cust
        self.__facIndex=facIndex  #index of container D/W/C   
        DEBUG and print("Instantiated: {} {} {}{}".format(prodNum,weight,facType,facIndex))
    def droneLoad(self,droneNum):
        self.__facType='D'  
        self.__facIndex=droneNum
        return True
    def setCustDelivery(self,custLoc):  
        self.__facType='C'  
        self.__facIndex=custLoc
        self.__deliveryTime=Calculate.currentTime()
    def assignToOrder(self,ordNum):
        self.__assignedToOrder=ordNum
    def isAssigned(self):
        return self.__assignedToOrder        
    def getStatus(self):
        return self.__index,self.__prodNum,self.__facType,self.__facIndex
    def getStatus2(self):
        return self.__index,self.__prodNum,self.__facType,self.__facIndex,self.__assignedToOrder

    def getStatus3(self):
        #itemIndex,OrderIndex,prodNum,facType,facIndex
        return (self.__index,self.__assignedToOrder,self.__prodNum,self.__facType,self.__facIndex)
    def showStatus(self):
        print("Item:{}\nProdNum:{}\nLoc:{}{}".format(self.__index,self.__prodNum,self.__facType,self.__facIndex))
        print("Assigned to order:{}".format(self.__assignedToOrder))
        print("Delivery Time:{}".format(self.__deliveryTime))
        print("Weight:{}".format(self.__weight))
        
class Drone(Data):                ###############   Drone ########
    counter=0
    def __init__(self,row,col,maxLoad):
        super().__init__()
        self.__index=Drone.counter
        Drone.counter += 1
        self.__maxLoad=maxLoad
        self.__enRoute=False
        self.__deliveringBoxIndex=False
        self.__destRow=row
        self.__destCol=col
        self.__destTime=0
        self.__boxes=list()
        self.__labels=list()
        self.__payload=list()
        self.__row=row
        self.__col=col
        self.__assignedToWh=False
        self.__imFlight=False
    #def clearVals(self):
    #    return self.__row,self.__col
    def empty(self):
        self.__enRoute=False
        self.__deliveringBoxIndex=False
        self.__destRow=False
        self.__destCol=False
        self.__destTime=False
        self.__boxes=list()
        self.__labels=list()
        self.__payload=list()
    def removeImBoxes(self):
        #remove any boxes marked Intermodal transfer
        for i in range(len(self.__boxes)-1,-1,-1):
            if self.__boxes[i][1]=='I':
                self.__boxes.pop(i)
    def isAssignedToWh(self):
        return self.__assignedToWh
    def setAssignedToWh(self,val):
        self.__assignedToWh=val
    def getNumItems(self):
        return len(self.__boxes)
    def setImFlight(self,val):
        self.__imFlight=val
    def getImFlight(self):
        return self.__imFlight
    def fly2Cust(self):
        if len(self.__boxes)==0:
            return False
        closestIndex=-1
        closestDist=9999
        closestrc=(-1,-1)
        #find the closest order delivery site for the onboard packages
        for i in range(len(self.__boxes)):
            labelTup=self.__boxes[i]
            droneIndex,DLW,wh,prodNum,qty,orderIndex,wait,itemIndex,weight=labelTup
            cr,cc=ord[orderIndex].getPos()
            dist=Calculate.distance(self.__row,self.__col,cr,cc)
            if dist <closestDist:
                closestDist=dist
                closestIndex=i
                closestrc=(cr,cc)
        #Now set the Destination and arrival time and enroute params
        self.deliveringBoxIndex(closestIndex)
        self.__enRoute=True
        self.__destRow,self.__destCol=closestrc
        dist=math.ceil( Calculate.distance(self.__row,self.__col,self.__destRow,self.__destCol) )
        DEBUG and print("Drone #{} Now flying to {},{} for order:{} / item{}".format(self.__index,self.__destRow,self.__destCol,orderIndex,itemIndex))
        DEBUG and print("Hypot:{} Ceiling dist/time:{}".format(Calculate.distance(self.__row,self.__col,self.__destRow,self.__destCol),dist) )

        currentTime=Calculate.currentTime()
        self.__destTime=currentTime+dist +1
        
    def xfer2Cust(self):                                                ########## Xfer2Cust  ##############
        #Adjust r,c to exact vals as there may have been accumulated rounding error inflight
        self.__row,self.__col==round(self.__row),round(self.__col)
        #find all boxes that should be delivered to this grid location
        DEBUG and print("Transferring box(es) to cust at {},{} ".format( self.__row,self.__col))
        listOfBoxesToRemove=list()
        tempBoxList=self.__boxes
        for i in range(len(tempBoxList)):
            labelTup=tempBoxList[i]
            droneNum, LDW,_,prodNum,prodQty,orderIndex,_,itemIndex,weight=labelTup
            cr,cc=ord[orderIndex].getPos()
            if ( self.__row,self.__col )==(cr,cc):
                DEBUG and print("Order:{} matches this location {},{} so delivering it here.".format(orderIndex,cr,cc))
                #unload this box
                listOfBoxesToRemove.insert(0,orderIndex)
                
                newBoxList = [x for x in self.__boxes if x[5] != orderIndex ]
                self.__boxes=newBoxList
                DEBUG and print("Removing box order {} from \n=>boxlist:{} \n==>now:{}".format(orderIndex,tempBoxList,self.__boxes))
                ord[orderIndex].setFulfilled(Calculate.currentTime(),itemIndex)
                assWh=ord[orderIndex].getWh()
                w[assWh].generatePriorityList()
                item[itemIndex].setCustDelivery( (cr,cc) ) #Update this item with its final details
                Data.incScore(1)   
                
                labelTup=(droneNum, 'D',False,prodNum,qty,orderIndex,False,itemIndex,_)
                log.append(Log(Calculate.genLabel(labelTup,'D')))
                
                
                Calculate.updateRemItems(orderIndex)                         #*********************************
                
                
                
                
                
        #listOfBoxesToRemove.sort(reverse=True) #pop items from the end of the list to the front
        #for oi in listOfBoxesToRemove: 
        #    print("Removing box with order {} from listOfBoxesToRemove:{}".format(oi,listOfBoxesToRemove))
            #newBoxList = [x for x in self.__boxes if x[5] == oi ] #remove this box from the list
        #self.__boxes=newBoxList
        #print("Remaining boxes:")
        #self.showBoxes()
        ###
        ###Note:after deliveries the priority list of the warehouse should be recalced################
        #####
        
        #if there are more boxes on board, set the flight path to the next closest
        if len(self.__boxes)>0:
            DEBUG and print("Drone:{} is NOT empty. Remaining:{}".format(self.__index,self.__boxes))
            self.fly2Cust()
        else:
            #Drone is empty. Clear values so next round it can be reloaded
            DEBUG and print("Drone:{} is empty {}".format(self.__index,'*'*50))
            self.empty()

    def deliveringBoxIndex(self,boxIndex):  
        self.__deliveringBoxIndex=boxIndex
    def pushBox(self,label):
        self.__boxes.append(  (label) )
        return 
    def swapLabelforDelivery(self,boxIndex):
        labelTup=self.__boxes[boxIndex] 
        labelList=list(labelTup)
        labelList[1]='D'
        labelTup=tuple(labelList)
        self.__boxes[boxIndex]=(labelTup)

    def getBoxes(self):
        boxList=list()
        for b in self.__boxes:
            boxList.append(b)
        return boxList
    def showBoxes(self):
        print("index,LDW,warehouseNum,prodNum,prodQty,orderIndex,wait,itemIndex,orderWeight")
        for b in self.__boxes:
            print("{}  ".format(b),end='')
        print("")
        return 
    def setDest(self,r,c):
        self.__destRow,self.__destCol=r,c
    def getDest(self):
        return self.__destRow,self.__destCol
    def getDestTime(self):
        return self.__destTime
    def setDestTime(self,val):
        self.__destTime=val
    def getExcessCapacity(self):
        currentPayload = sum(tup[8] for tup in self.__boxes)
        return self.__maxLoad-currentPayload
    def getPos(self):
        return self.__row,self.__col
    def setPos(self,r,c):
        self.__row,self.__col=r,c
    def updateLocation(self,newR,newC):
        self.__row,self.__col=newR,newC
    def setEnRoute(self,val):
        self.__enRoute=val
    def isEnRoute(self):
        return (self.__enRoute)
    def isAvail(self):
        return not(self.__enRoute)
    def setAvail(self,val):
        self.__enRoute= not val
    def getStatus(self):
        return self.__index,self.__enRoute,self.__destRow,self.__destCol,self.__destTime
    def showStatus(self):
        print ("Drone #: {}".format(self.__index) )
        print ("En route:{}".format(self.__enRoute) )
        print ("Row:{} Col:{}".format(self.__row,self.__col) )
        print ("Dest Row:{} DestCol:{}".format(self.__destRow,self.__destCol) )
        print ("Dest Time:{}".format(self.__destTime) )
        print ("Assigned to warehouse:{}".format(self.__assignedToWh))
        print ("Intermodal:{}".format(self.__imFlight))
        self.showBoxes()
    def getQty():
        return Drone.counter
    def reset():
        Drone.counter=0
    def load(self,orderIndex,warehouseNum,prodNum,prodQty,itemIndex,orderWeight,intermodal=False):

        ord[orderIndex].setDeliveryInProcess(True)
        dr,dc=w[warehouseNum].getPos()
        self.setDest(dr,dc)
        #print ("D#{} Dest Row:{} Dest Col:{} IM:{}".format(self.__index,self.__destRow,self.__destCol,intermodal) )
        dist=math.ceil( Calculate.distance(self.__row,self.__col,self.__destRow,self.__destCol) )
        
        currentTime=Calculate.currentTime()
        self.__destTime=currentTime+dist+1
        self.__enRoute=True  
        DEBUG and print ("D#{} Dest Row:{} Dest Col:{} DestTime:{} IM:{}".format(self.__index,self.__destRow,self.__destCol,self.__destTime,intermodal) )
        if intermodal:
            labelTup=(self.__index, 'LI',warehouseNum,prodNum,prodQty,orderIndex,False,itemIndex,orderWeight)
            #   log.append(Log(Calculate.genLabel(labelTup,'I')))
        else:
            labelTup=(self.__index, 'L',warehouseNum,prodNum,prodQty,orderIndex,False,itemIndex,orderWeight)
            #    log.append(Log(Calculate.genLabel(labelTup,'L')))
        self.pushBox(labelTup)
        return True
    def hasArrived(self):
        #print("{},{} {},{}".format(self.__row,self.__col,self.__destRow,self.__destCol))
        #if ( self.__destTime==Calculate.currentTime() ) and ( (round(self.__row),round(self.__col))==((self.__destRow,self.__destCol))  ):

        if ( self.__destTime==Calculate.currentTime() ) :
            #Adjust r,c to exact vals as there may have been accumulated error inflight
            distanceError=Calculate.dist( (self.__row,self.__col), (self.__destRow,self.__destCol) )
            if distanceError>(1.5):
                print("Error 006: expected location is outside anticipated rounding error.")
                print("            distance offset={}".format(distanceError))  
                print("            Dest Time: {}   Current Time: {} ".format(self.__destTime,Calculate.currentTime()))
            self.__row,self.__col==self.__destRow,self.__destCol
            #Is the drone at a warehouse location?
            if  (  self.__row,self.__col  )  in whDict:
                return (True,'W')
            #Is the drone at a customer location for one of the onboard boxes?
            DEBUG and print("Boxes on board:{}".format(self.__boxes))
            for tup in self.__boxes:
                _,_,_,_,_,orderIndex,_,itemIndex,weight=tup
                cr,cc=ord[orderIndex].getPos()
                DEBUG and print("Order:{} has a delivery location of:{},{}".format(orderIndex,cr,cc))
                if (  round(self.__row),round(self.__col)  )==(cr,cc):
                    DEBUG and print("The drones current pos is: {},{} so it has arrived.".format(round(self.__row),round(self.__col)))
                    return (True,'C')
            #We ended up where we thought we wanted to be, but this is not
            #  a warehouse location or an address for an onboard box
            print("Error 005: Drone:{} is confused while at {},{}".format(self.__index,self.__row,self.__col))
            print("( self.__destTime==Calculate.currentTime() ) {}".format(( self.__destTime==Calculate.currentTime() ) ))
            print( " (round(self.__row),round(self.__col))==((self.__destRow,self.__destCol))",end='')
            print(  (round(self.__row),round(self.__col)==((self.__destRow,self.__destCol))) )
            
            #self.showStatus()
            
        return (False,False)
        
    
class Order(Data):            ########## Order ########
    counter=0
    def __init__(self,orderNum,row,col,prodNum,remItems,weight): 
        self.__index=Order.counter
        Order.counter+=1
        self.__row=row
        self.__col=col
        self.__orderNum=orderNum
        self.__prodNum=prodNum
        self.__isAssigned=False
        self.__assignedItemIndex=-1
        self.__fulfilled=False
        self.__loaded=False
        self.__turnFulfilled=False
        self.__itemDeliveredIndex=False
        self.__itemsInThisOrder=remItems
        self.__remItems=remItems
        self.__msgQueue=False
        self.__weight=weight
        self.__assignedWarehouse=False  #Closest wh to customer
        self.__subScore=False
        self.__maxScore=False
        self.__imInProcess=False  #Intermodal
        self.__deliveryInProcess=False 
    def getItemsInOrder(self):
        return self.__itemsInThisOrder
    def setIntermodal(self,val):
        self.__imInProcess=val
    def getIntermodal(self):
        return self.__imInProcess
    def isIm(self):
        if isinstance(self.__assignedItemIndex,tuple):
            return True
        return False
    def setDeliveryInProcess(self,DIPval):
        self.__deliveryInProcess=DIPval
    def getDeliveryInProcess(self):
        return self.__deliveryInProcess
    def getMetrics(self):
        #(intermodal dist, WhDist,remaining items,weight,maxScore)
        if self.isAssigned():
            imDist=0
            wr,wc=w[self.__assignedWarehouse].getPos()
            whDist=Calculate.dist( (self.__row,self.__col), (wr,wc))
            if isinstance(self.__assignedItemIndex,tuple):
                itemIndex,imWh=self.__assignedItemIndex
                imRow,imCol=w[imWh].getPos()
                imDist=Calculate.dist( (imRow,imCol), (wr,wc))  
                maxScore=0
                #maxScore=Calculate.orderMaxScore(self.__index)

            return (imDist,whDist,self.__remItems,self.__weight,maxScore)
        return (False,False,self.__remItems,self.__weight,False)
    def getDistances(self):
        if self.isAssigned():
            imDist=0
            wr,wc=w[self.__assignedWarehouse].getPos()
            whDist=Calculate.dist( (self.__row,self.__col), (wr,wc))
            if isinstance(self.__assignedItemIndex,tuple):
                itemIndex,imWh=self.__assignedItemIndex
                imRow,imCol=w[imWh].getPos()
                imDist=Calculate.dist( (imRow,imCol), (wr,wc))  
            return (imDist,whDist)
        raise SystemExit("Stop right here to evaluate!") 

    def getMaxScore(self):
        return self.__maxScore
    def setMaxScore(self,n):
        self.__maxScore=n
        return 
    def getSubScore(self):
        return self.__subScore
    def setSubScore(self,n):
        self.__subScore=n
        return 
    def getQty():
        return Order.counter
    def reset():
        Order.counter=0
    def isAssigned(self):
        return self.__isAssigned
    def setAssignedItem(self,itemIndex):
        self.__isAssigned=True
        self.__assignedItemIndex=itemIndex
    def isIntermodal(self):
        if isinstance(self.__assignedItemIndex,tuple):
            return True
        else:
            return False
    def getAssignedItem(self):
        return self.__assignedItemIndex
    def setWh(self,wh):
        self.__assignedWarehouse=wh
    def getWh(self):
        return self.__assignedWarehouse        
    def getPos(self):
        return self.__row,self.__col
    def getProdNum(self):
        return self.__prodNum
    def getWeight(self):
        return p[self.__prodNum].getWeight()
    def getOrderNum(self):
        return self.__orderNum
    def setQueue(self,droneNum):
        self.__msgQueue=droneNum
        return 
    def getQueue(self):
        return self.__msgQueue
    def setRemItems(self,remItems):
        self.__remItems=remItems
        return 
    def getRemItems(self):
        return self.__remItems

    def isLoaded(self):
        return self.__loaded
    def setLoaded(self,val):
        self.__loaded=val
    def isFulfilled(self):
        return self.__fulfilled
    def setFulfilled(self,t,itemDeliveredIndex):
        self.__turnFulfilled=t
        self.__fulfilled=True
        self.__itemDeliveredIndex==itemDeliveredIndex
    def getFulfilledTime(self):
        return self.__turnFulfilled
    def getStatus(self):
        return self.__index,self.__row,self.__col,self.__orderNum,self.__prodNum,self.__remItems
    def getEndStatus(self):
        return self.__fulfilled, self.__remItems,self.__isAssigned,self.__assignedItemIndex,self.__turnFulfilled
    def showStatus(self):
        print("Order: {}\nLoc:{},{}".format(self.__index,self.__row,self.__col))
        print("Orig OrderNum: {}\nProdNum:{}  Weight:{}".format(self.__orderNum,self.__prodNum,self.__weight))
        print("Is Assigned:{}   AssignedItem:{}".format(self.__isAssigned,self.__assignedItemIndex))
        print("Warehouse:{}\nFulFilledAt:{}".format(self.__assignedWarehouse ,self.__turnFulfilled ))
        print("RemItems: {}\nFulfilled:{}".format(self.__remItems,self.__fulfilled))
        print("subScore: {}   maxScore:{}".format(self.__subScore,self.__maxScore))
        print("Delivery in process: {}".format(self.__deliveryInProcess))
class Sim(Algo):
    counter=0
    def __init__(self):
        super().__init__()
        self.counter += 1
        self.__rows=False
        self.__cols=False
        self.__droneQty=False
        self.__deadline=False
        self.__droneMaxPayload=False
    def initializeParams(self,rows,cols,droneQty,deadline,maxLoad):
        self.__rows=rows
        self.__cols=cols
        self.__droneQty=droneQty
        self.__deadline=deadline
        self.__droneMaxPayload=maxLoad        
    def getStatus(self):
        print("Grid:{}x{}".format(self.__rows,self.__cols))
        print("Drone Qty:{}   Max Payload:{}".format(self.__droneQty,self.__droneMaxPayload))
        print("Deadline:{}".format(self.__deadline))
        return

