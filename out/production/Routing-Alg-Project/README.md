#Computer Networks (CSE 4344)
##Programing Assignment 3, Project A: Distance Vector Routing Protocol

##Problem Statement:
Implement the distance vector routing protocol similar to the one described in the textbook.

###Project Objective/Overview:
DVR works by having each routing node periodically exchange routing updates with its
neighbors. Each routing update contains the node’s entire routing table. Upon receiving a
routing update, a node updates its routing table with the “best” routes to each destination. In
addition, each routing daemon must remove entries from its routing table when they have not
been updated for a long time.

###Your implementation of DVR should have the following features:
1. Full routing table updates should be exchanged between neighboring nodes every
advertisement cycle.
2. In the event of a tie for shortest path, the next hop in the routing table should always
point to the nodeID with the lowest numerical value.
3. Set all routes in the routing table through a neighbor to the infinity value if it hasn’t
given any updates for some period of time.
4. Set routes in the routing table to the infinity value if they have not been updated for
some period of time (“expire” them).
5. Delete routes from the routing table that have been set to infinity for some period of
time (“garbage collect” them).
6. If a node or link goes down (e.g., routing daemon crashes, or link between them no
longer works and drops all messages), your routing tables in the network should reflect
the new network graph.

###Specifications: 
1. Network ID: The network ID or destination corresponding to the route. The network ID
can be subnet or supernet network ID, or an IP address for a host route.
2. Next Hop: The IP address of the next hop.
3. Metric/Cost: A number used to indicate the cost of the route so the best route among
possible multiple routes to the same destination can be selected.
4. Interface: An indication of which network interface is used to forward the IP packet.

###Challenges:
1. In the event of a tie in hop counts for a given destination it always chooses the route
where the nodeID of next hop has the lowest numerical value.
2. If your routing daemon does not receive any advertisements from a certain neighbor for
a number of advertisement cycles it is time to consider a neighbor to be down. The
routing daemon propagates this information the next time it advertises its routes.
3. Next, if a route has not been updated in a long time, then we “expire” it by marking it
invalid and setting its distance to infinity. However, we keep advertising it to our
neighbors (as infinity).
4. Finally, if a route has been expired (had infinity distance) for many advertisement cycles
already, then you can delete the route permanently from its routing table.

##Nature of Project, Tips for Success and Team Composition:
This project will require significant time and effort to conceptualize, design, code, test and
iterate through prototypes. It expected that it will require several weeks of effort from a typical
team of 4-5 students. The earlier you start the better the resulting program will be.

Start by analyzing and understanding the protocol and it’s functioning by referring the
textbook and related RFC’s. This will be a great opportunity to understand and perhaps give
you more complete exposure to the protocols that we have studied in class.

Taking into account the complexity of this assignment, you must select a team of no less
than four (4) and no more than five (5) students in your section to work with on this project.
All students on a team will receive the same grade for this assignment, so work should
apportioned accordingly. If you have any questions about this assignment, please contact
Sharad Velmajala, 4344 GTA, for clarification.

###Expected Results: Your submitted program, using Python or Java, should:
1. Simulate the distance vector routing algorithm with 4-5 nodes (simulated routers) in the
network.
2. Create and store the routing table on the local host.
3. Advertise and exchange routing updates periodically and also process incoming
advertisements from neighbors.
4. Update routing tables whenever there is a shortest route available in the network.
5. Be able to handle communication failures.

###Submission Details:
1. Select your team of 4 or 5 studentsand submit names of teammates to your GTA by email
(copy to Professor O’Dell) no later than midnight, October 23, 2015. Please coordinate within
the team to ensure that only one person on the team submits the names.
2. Submit your completed project source code to your GTA by email no later thanmidnight,
December 4, 2015.
3. Include a brief write-up with your submission that discusses the highlights of your project,
execution details and sample results that you have obtained during final testing.
4. Be prepared to demonstrate the operation of your application if requested.
5. Maximum credit cannot be achieved on this assignment unless your program operates as
specified and handles typical error.
