# Reminder: NEEDS MODIFICATIONS...!!!

#--------------------------------------------------------------
# Team NO:     403                                            |
#--------------------------------------------------------------
# Members:     Francisco Martinez   [1000784747]              |
#              Brandon Lawrence     [1000744004]              |
#              Miguel Obiang        [1000819926]              |
#              Reynaldo Gonzales    [1000991514]              |
#              Adetomilola Popoola  [1000855160]              |
#                                                             |
# Course:      CSE4344-001 [Networks]                         |
# Assignment:  Final Project [Routing Algorithm]              |
# Date:        December 24, 2015                              |
#--------------------------------------------------------------

import sys, socket, json, time
from select import select
from collections import defaultdict, namedtuple
from threading import Thread, Timer
from datetime import datetime
from copy import deepcopy

#-----------------------------------------------------------------
# User commands and inter-node protocol update types             |
# Note: set of commands and set of protocol messages intersect!  |
#       if you want a list see user_cmds and udpates near main.  |
#-----------------------------------------------------------------
LINKDOWN      = "linkdown"
LINKUP        = "linkup"
LINKCHANGE    = "linkchange"
SHOWRT        = "showrt"
CLOSE         = "close"
COSTSUPDATE   = "costsupdate"
SHOWNEIGHBORS = "neighbors"
DEBUG         = "debug"
SIZE          = 4096



#==============================================================|| Functions ||
class RepeatTimer(Thread):
    """ Thread that will call a function every interval seconds """
    def __init__(self, interval, target):
        Thread.__init__(self)
        self.target = target
        self.interval = interval
        self.daemon = True
        self.stopped = False

    def run(self):
        while not self.stopped:
            time.sleep(self.interval)
            self.target()


class ResettableTimer():
    def __init__(self, interval, func, args=None):
        if args != None: assert type(args) is list
        self.interval = interval
        self.func = func
        self.args = args
        self.countdown = self.create_timer()
    def start(self):
        self.countdown.start()

    def reset(self):
        self.countdown.cancel()
        self.countdown = self.create_timer()
        self.start()

    def create_timer(self):
        t = Timer(self.interval, self.func, self.args)
        t.daemon = True
        return t

    def cancel(self):
        self.countdown.cancel()


def estimate_costs():
    """ Recalculate inter-node path costs using bellman ford algorithm """
    # =======================================================================
    # Objective:                                                           ||
    #----------------------------------------------------------------------||
    # -> Check for duplicates, to avaoid the distance update of ourselves  ||
    # -> Iterate through neighbors and find available cheapest route       ||
    # =======================================================================
    for destination_addr, destination in nodes.iteritems():
        if destination_addr != me:
            cost = float("inf")
            nexthop = ''
            for neighbor_addr, neighbor in get_neighbors().iteritems():
                if destination_addr in neighbor['costs']:
                    dist = neighbor['direct'] + neighbor['costs'][destination_addr]
                    if dist < cost:
                        cost = dist
                        nexthop = neighbor_addr
            # set new estimated cost to node in the network
            destination['cost'] = cost
            destination['route'] = nexthop


def update_costs(host, port, **kwargs):
    # ================================================================
    # Objective:                                                    ||
    # --------------------------------------------------------------||
    # -> Handles existen and non-existen nodes in our list of nodes ||
    # -> Saving or recording each of their cost...                  ||
    # ================================================================
    """ update neighbor's costs """
    costs = kwargs['costs']
    addr = addr2key(host, port)

    # ---------------------
    #  Create a new node  |
    # ---------------------
    for node in costs:
        if node not in nodes:
            nodes[node] = default_node()

    # ----------------------------
    #  If node not a neighbor ...|
    # ----------------------------
    if not nodes[addr]['is_neighbor']:
        # ... Make it your neighbor!
        print 'making new neighbor {0}\n'.format(addr)
        del nodes[addr]
        nodes[addr] = create_node(
                cost        = nodes[addr]['cost'],
                is_neighbor = True,
                direct      = kwargs['neighbor']['direct'],
                costs       = costs,
                addr        = addr)
    else:
        # ...  Otherwise just update node costs
        node = nodes[addr]
        node['costs'] = costs			# Restart silence monitor
        node['silence_monitor'].reset()
    estimate_costs() 					# Run bellman ford


def linkdown(host, port, **kwargs):
    #==============================================
    # Objectives:                                ||
    # -------------------------------------------||
    # -> Save direct distance to                 ||
    # -> neighbor, then set to infinity          ||
    #==============================================
    node, addr, err = get_node(host, port)
    if err: return
    if not node['is_neighbor']:
        print "node {0} is not a neighbor so it can't be taken down\n".format(addr)
        return
    node['saved'] = node['direct']
    node['direct'] = float("inf")
    node['is_neighbor'] = False
    node['silence_monitor'].cancel()
    estimate_costs()	# Run bellman-ford


def broadcast_costs():
    """ send estimated path costs to each neighbor """
    costs = { addr: node['cost'] for addr, node in nodes.iteritems() }
    data = { 'type': COSTSUPDATE }
    for neighbor_addr, neighbor in get_neighbors().iteritems():
        poisoned_costs = deepcopy(costs)
        for dest_addr, cost in costs.iteritems():    	        # only do poisoned reverse...
							        # if destination not me or neighbor

            if dest_addr not in [me, neighbor_addr]:            # If we route through neighbor to get to destination ...
                if nodes[dest_addr]['route'] == neighbor_addr:  # ... tell neighbor distance to destination is infinty!
                    poisoned_costs[dest_addr] = float("inf")

        # -------------------------------------------------
        # Send (potentially 'poisoned') costs to neighbor |
        # -------------------------------------------------
        data['payload'] = { 'costs': poisoned_costs }
        data['payload']['neighbor'] = { 'direct': neighbor['direct'] }
        sock.sendto(json.dumps(data), key2addr(neighbor_addr))


def setup_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((host, port))
        print "listening on {0}:{1}\n".format(host, port)
    except socket.error, msg:
        print "An error occured binding the server socket. \
               Error code: {0}, msg:{1}\n".format(msg[0], msg[1])
        sys.exit(1)
    return sock

def default_node():
    return { 'cost': float("inf"), 'is_neighbor': False, 'route': '' }


def create_node(cost, is_neighbor, direct=None, costs=None, addr=None):
    #=========================================================
    #    Takes:      (float)                                ||
    #               (boolen)                                ||
    #               (boolen)                                ||
    #           (dictionary)                                ||
    #   Return: node's address and status                   ||
    #-------------------------------------------------------||
    # Purposed: Ensure transmition cost of neighbored nodes ||
    #           and updates using a resettable timer        ||
    #=========================================================
    # nodes[addr] = create_node(
    # cost        = nodes[addr]['cost'],
    # is_neighbor = True,
    # direct      = kwargs['neighbor']['direct'],
    # costs       = costs,
    # addr        = addr)

    """ Centralizes the pattern for creating new nodes """
    node = default_node()
    node['cost'] = cost
    node['is_neighbor'] = is_neighbor
    node['direct'] = direct if direct != None else float("inf")
    node['costs']  = costs  if costs  != None else defaultdict(lambda: float("inf"))

    if is_neighbor:
        node['route'] = addr
        monitor = ResettableTimer(
            interval = 3*run_args.timeout,
            func = linkdown,
            args = list(key2addr(addr)))
        monitor.start()
        node['silence_monitor'] = monitor
    return node


def get_node(host, port):
    #====================================================
    #    Takes: host's address,                        ||
    #           host's port,                           ||
    #   Return: node's address and status              ||
    #--------------------------------------------------||
    # Purposed: Check for neighbored nodes...          ||
    #====================================================
    """ returns formatted address and node info for that addr """
    error = False
    addr  = addr2key(get_host(host), port)

    if not in_network(addr):
        error = 'node not in network'

    node = nodes[addr]
    return node, addr, error


def linkchange(host, port, **kwargs):
    #====================================================
    #    Takes: host's address,                        ||
    #           host's port,                           ||
    #           **                                     ||
    #   Return: (void)                                 ||
    #--------------------------------------------------||
    # Purposed: Check status of neighbored nodes...    ||
    #           Then change their links if need to...  ||
    #====================================================
    node, addr, err = get_node(host, port)
    if err: return

    if not node['is_neighbor']:
        print "node {0} is not a neighbor so the link cost can't be changed\n".format(addr)
        return

    direct = kwargs['direct']
    if direct < 1:
        print "the minimum amount a link cost between nodes can be is 1"
        return

    if 'saved' in node:
        print "This link's currently down. Please first bring link back to life using LINKUP cmd."
        return
    node['direct'] = direct
    estimate_costs()        # run bellman-ford


def linkup(host, port, **kwargs):
    #====================================================
    #    Takes: host's address,                        ||
    #           host's port,                           ||
    #           **                                     ||
    #   Return: (void)                                 ||
    #--------------------------------------------------||
    # Purposed: -> Check for "LINKDOWN cmd" nodes      ||
    #           -> Restore required distances          ||
    #====================================================
    node, addr, err = get_node(host, port)
    if err: return

    # -----------------------------------------------------------
    # make sure node was previously taken down via LINKDOWN cmd |
    # -----------------------------------------------------------
    if 'saved' not in node:
        print "{0} wasn't a previous neighbor\n".format(addr)
        return

    # -------------------------------
    # restore saved direct distance |
    # -------------------------------
    node['direct'] = node['saved']
    del node['saved']
    node['is_neighbor'] = True
    estimate_costs()		# run bellman-ford


def formatted_now():
    return datetime.now().strftime("%b-%d-%Y, %I:%M %p, %S seconds")


def show_neighbors():
    """ Show active neighbors """
    print formatted_now()
    print "Neighbors: "
    for addr, neighbor in get_neighbors().iteritems():
        print "{addr}, cost:{cost}, direct:{direct}".format(
                addr   = addr,
                cost   = neighbor['cost'],
                direct = neighbor['direct'])
    print # extra line


def showrt():
    """ Display routing info: cost to destination; route to take """
    print formatted_now()
    print "Distance vector list is:"
    for addr, node in nodes.iteritems():
        if addr != me:
            print ("Destination = {destination}, "
                   "Cost = {cost}, "
                   "Link = ({nexthop})").format(
                        destination = addr,
                        cost        = node['cost'],
                        nexthop     = node['route'])
    print # extra line


def close():
    """ Notify all neighbors that she's a comin daaaahwn! then close process"""
    ''' I am commenting out the code that instantly notifies neighbors that the link
        is being closed because requirements say a 'close' cmd "is like simulating link failure"
        data = {'type': LINKDOWN, 'payload': {}}
        for neighbor_addr, neighbor in get_neighbors().iteritems():
        sock.sendto(json.dumps(data), key2addr(neighbor_addr))
    '''
    sys.exit()


def in_network(addr):
    if addr not in nodes:
        print 'node {0} is not in the network\n'.format(addr)
        return False
    return True

def key2addr(key):
    host, port = key.split(':')
    return host, int(port)

def addr2key(host, port):
    return "{host}:{port}".format(host=host, port=port)

def get_host(host):
    """ translate host into ip address """
    return localhost if host == 'localhost' else host

def get_neighbors():
    """ return dict of all neighbors (does not include self) """
    return dict([d for d in nodes.iteritems() if d[1]['is_neighbor']])

def is_number(n):
    try:
        float(n)
        return True
    except ValueError:
        return False

def is_int(i):
    try:
        int(i)
        return True
    except ValueError:
        return False

def parse_argv():
    #====================================================
    #    Takes: (void)                                 ||
    #   Return: (void)                                 ||
    #--------------------------------------------------||
    # Purposed: -> Port Validates 		               ||
    #           -> Timeout Validates                   ||
    #====================================================
    """
    pythonicize bflient run args
    (note: yes, I know I should be raising exceptions instead of returning {'err'} dicts)
    """
    #------------------
    #   Validations   |
    #------------------
    s = sys.argv[1:]
    parsed = {}

#TODO MOVE TO SEPARATE FUNCTION??
# NEW Functions
    if not s:
        print "Enter the port for this machine to listen on:"
        arg = sys.stdin.readline()
        while not is_int(arg):
            print "port values must be integers. {0} is not an int."
            parsed = sys.stdin.readline()
        s.append(str(arg))
        print "Enter the timeout for this machine:"
        arg = sys.stdin.readline()
        while not is_int(arg):
            print "timeout values must be integers. {0} is not an int."
            arg = sys.stdin.readline()
        s.append(str(arg))

        # return { 'error': "please provide host, port, and link cost for each link." }
#END NEW FUNCTIONS


    port = s.pop(0)	# Validates port
    timeout = s.pop(0)  # Validates timeout

    if not is_int(port):
        return { 'error': "port values must be integers. {0} is not an int.".format(port) }
    parsed['port'] = int(port)

    if not is_number(timeout):
        return { 'error': "timeout must be a number. {0} is not a number.".format(timeout) }
    parsed['timeout'] = float(timeout)

    # ---------------------------------------------
    # Iterate through s extracting and validating |
    # neighbors and costs along the way           |
    # ---------------------------------------------
    parsed['neighbors'] = []
    parsed['costs'] = []

    while len(s):
        if len(s) < 3:
            return { 'error': "please provide host, port, and link cost for each link." }

        host = get_host(s[0].lower())
        port = s[1]

        if not is_int(port):
            return { 'error': "port values must be integers. {0} is not an int.".format(port) }

        parsed['neighbors'].append(addr2key(host, port))
        cost = s[2]

        if not is_number(cost):
            return { 'error': "link costs must be numbers. {0} is not a number.".format(cost) }

        parsed['costs'].append(float(s[2]))
        del s[0:3]

    return parsed

# def prompt_user_args(user_input):



def parse_user_input(user_input):
    """
    validate user input and parse values into dict. returns (error, parsed) tuple.
    (note: yes, I know I should be raising exceptions instead of returning {'err'} dicts)
    """

    #--------------------------------
    #  Define default return value  |
    #--------------------------------
    parsed = { 'addr': (), 'payload': {} }
    user_input = user_input.split()
    if not len(user_input):
        return { 'error': "please provide a command\n" }

    #----------------------------
    #    Verify cmd is valid    |
    #----------------------------
    cmd = user_input[0].lower()
    if cmd not in user_cmds:
        return { 'error': "'{0}' is not a valid command\n".format(cmd) }

    #----------------------------
    #  CMDs below require args  |
    #----------------------------
    if cmd in [LINKDOWN, LINKUP, LINKCHANGE]:
        args = user_input[1:]

    	#--------------------
        #    Validate args  |
        #--------------------
        if cmd in [LINKDOWN, LINKUP] and len(args) != 2:
            return { 'error': "'{0}' cmd requires args: host, port\n".format(cmd) }

        elif cmd == LINKCHANGE and len(args) != 3:
            return { 'error': "'{0}' cmd requires args: host, port, link cost\n".format(cmd) }

        port = args[1]
        if not is_int(port):
            return { 'error': "port must be an integer value\n" }

        parsed['addr'] = (get_host(args[0]), int(port))
        if cmd == LINKCHANGE:
            cost = args[2]

            if not is_number(cost):
                return { 'error': "new link weight must be a number\n" }
            parsed['payload'] = { 'direct': float(cost) }

    parsed['cmd'] = cmd
    return parsed


def print_nodes():
    """ helper function for debugging """
    print "nodes: "
    for addr, node in nodes.iteritems():
        print addr
        for k,v in node.iteritems():
            print '---- ', k, '\t\t', v
    print # extra line




#==============================================================|| Main Program ||

#=========================================
# Map Command/Update Names to Functions ||
#=========================================
user_cmds = {
    LINKDOWN   : linkdown,
    LINKUP     : linkup,
    LINKCHANGE : linkchange,
    SHOWRT     : showrt,
    CLOSE      : close,
    SHOWNEIGHBORS : show_neighbors,
    DEBUG      : print_nodes,
}
updates = {
    LINKDOWN   : linkdown,
    LINKUP     : linkup,
    LINKCHANGE : linkchange,
    COSTSUPDATE: update_costs,
}

if __name__ == '__main__':
    localhost = socket.gethostbyname(socket.gethostname())
    parsed = parse_argv()

    if 'error' in parsed:
        print parsed['error']
        sys.exit(1)

    RunArgs = namedtuple('RunInfo', 'port timeout neighbors costs')
    run_args = RunArgs(**parsed)

    # -------------------------------------------
    # initialize dict of nodes to all neighbors |
    # -------------------------------------------
    nodes = defaultdict(lambda: default_node())
    for neighbor, cost in zip(run_args.neighbors, run_args.costs):
        nodes[neighbor] = create_node(cost=cost,
                                      direct=cost,
                                      is_neighbor=True,
                                      addr=neighbor)

    sock = setup_server(localhost, run_args.port)  # begin accepting UDP packets
    me = addr2key(*sock.getsockname())		   # set cost to myself to 0
    nodes[me] = create_node(cost=0.0,
                            direct=0.0,
                            is_neighbor=False,
                            addr=me)

    # ---------------------------------------
    # broadcast costs every timeout seconds |
    # ---------------------------------------
    broadcast_costs()
    RepeatTimer(run_args.timeout, broadcast_costs).start()


    # ----------------------------------------------------
    # listen for updates from other nodes and user input |
    # ----------------------------------------------------
    inputs = [sock, sys.stdin]
    running = True

    while running:
        in_ready, out_ready, except_ready = select(inputs,[],[])

        for s in in_ready:
            if s == sys.stdin:

    		# --------------------
                # User input command |
    		# --------------------
                parsed = parse_user_input(sys.stdin.readline())
                if 'error' in parsed:
                    print parsed['error']
                    continue

    		# ----------------------------------------------
                # Notify node on one end of the link of action |
    		# ----------------------------------------------
                cmd = parsed['cmd']
                if cmd in [LINKDOWN, LINKUP, LINKCHANGE]:
                    data = json.dumps({ 'type': cmd, 'payload': parsed['payload'] })
                    sock.sendto(data, parsed['addr'])

    		# -------------------------------------------------
                # Else: cmd is performed on other end of the link |
    		# -------------------------------------------------
                user_cmds[cmd](*parsed['addr'], **parsed['payload'])

            else:
    		#--------------------------------------
                # Updates performed from another node |
    		#--------------------------------------
                data, sender = s.recvfrom(SIZE)
                loaded = json.loads(data)
                update = loaded['type']
                payload = loaded['payload']

                if update not in updates:
                    print "'{0}' is not in the update protocol\n".format(update)
                    continue
                updates[update](*sender, **payload)

    sock.close()
