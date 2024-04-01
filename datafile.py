
from scipy.sparse import dok_matrix
from collections import namedtuple


def z2y(r, x):
    """ converts impedance Z=R+jX to admittance Y=G+jB """
    return r/(r**2+x**2), -x/(r**2+x**2)

def load_gens(casefileobj, e2i):
    """ returns a dictionary mapping generator buses to their power output and
     voltage. internal numbering """
    Gen = namedtuple('Gen', ['p', 'v'])
    line = ''
    gens = {}
    while line.find("mpc.gen = [") == -1:
        line = casefileobj.readline()
    line = casefileobj.readline()
    while line.find("];") == -1:
        words = line.split()
        bus, p, v = e2i[int(words[0])], float(words[1]), float(words[5])
        gens[bus] = Gen(p, v)
        line = casefileobj.readline()
    return gens


def adjust_demands(demands, gens):
    """ subtracts off any power generated at non-slack buses. internal numbering
    """
    for (bus, gen) in gens.items():
        if bus != 0:
            demands[bus] -= gen.p
def load_buses(casefileobj):
    """ returns a dictionary of bus demands, the root bus, and its voltage
    uses external bus numbering
    """
    line = ''
    demand_dict = {}
    root = 1
    vhat = 1
    while line.find("mpc.bus = [") == -1:
        line = casefileobj.readline() 
    line = casefileobj.readline()
    while line.find("];") == -1:
        words = line.split()
        bus, bus_type, p = (int(words[0]), int(words[1]), (float(words[2])))
        if bus_type == 3:
            root = bus

        demand_dict[bus] = p 
        line = casefileobj.readline()
    return demand_dict, root, vhat


def renumber_buses(demand_dict, root):
    """ creates a map of external to internal bus numbering, and a list with the
    reverse map. also returns the demands as a list using internal numbering
    """
    e2i = {root: 0}
    i2e = [0]*len(demand_dict)
    demands = [0]*len(demand_dict)
    i2e[0] = root
    i = 1
    for bus in sorted(demand_dict.keys()):
        if bus != root:
            e2i[bus] = i
            i2e[i] = bus
            i += 1
    for bus, d in demand_dict.items():
        i = e2i[bus]
        demands[i] = d
    return e2i, i2e, demands

def load_branches(casefileobj, e2i):
    
    line = ''
    n = len(e2i)
    current_limit=dok_matrix((n,n))
    G = dok_matrix((n, n))
    B = dok_matrix((n, n))
    
    branch_list = [None]*(n-1)
    branch_data_list = [None]*(n-1)
    i = 0
    limits=[]
    while line.find("mpc.branch = [") == -1:
        line = casefileobj.readline()
    line = casefileobj.readline()
    while line.find("];") == -1:
        words = line.split()
        #print(words)
        fbus, tbus = e2i[int(words[0])], e2i[int(words[1])]
        
        #print(type(fbus))
        r, x = float(words[2]), float(words[3])
        limit=(float(words[5]))
        #print(limit)
        limits.append(limit)
        g, b = z2y(r, x)
        #print(g,b)
        
        G[fbus, tbus] = (g)
        G[tbus, fbus] = (g)
        B[fbus, tbus] = (b)
        B[tbus, fbus] = (b)
        current_limit[fbus,tbus]= limit
        #print(G)
        branch_list[i] = (fbus, tbus)
        branch_data_list[i]=(r,x)
        #print(branch_list)
        line = casefileobj.readline()
        i += 1

    return G, B,branch_list,branch_data_list,current_limit


class Case(object):
    pass


def load_case(casefile):
    
   
    casefileobj = open(casefile)
    demand_dict, root, vhat = load_buses(casefileobj)
    e2i, i2e, demands = renumber_buses(demand_dict, root)
    gens = load_gens(casefileobj, e2i)
   
    G,B,  branch_list, branch_data_list,current_limit = load_branches(casefileobj, e2i)
    
    c = Case()
    c.demands = demands
    c.G = G
    c.B=B
    c.branch_list = branch_list
    c.branch_data_list = branch_data_list
    c.vhat = vhat
    c.i2e = i2e
    c.gens = gens
    c.current_limit =current_limit
    return c



