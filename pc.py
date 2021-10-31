import pyAgrum as gum
import pyAgrum.lib.image as gimg

from utils import *

save_folder = "Results/"
save_prefix = "learned_bn"
save_steps = False
save_final = not(save_steps)

class PC():
    """
    PC algorithm to learn a Bayesian Network
    """
    def __init__(self):
        self.graph = gum.MixedGraph()
    
    @save_result(save_prefix + "_0.png", save=save_steps)
    def _init_graph(self, bn):
        for n in bn.nodes():
            self.graph.addNodeWithId(n)

        for x in self.graph.nodes():
            for y in self.graph.nodes():
                if x != y:  self.graph.addEdge(x,y)
        
        return {"graph":self.graph}
    
    @save_result(save_prefix + "_1.png", save=save_steps)
    def _learn_skeleton(self, learner):
        """
        Phase 1: learn the skeleton
        """
        def has_more_neighbours(graph, d):
            """
            Loop condition
            """
            for x in graph.nodes():
                if len(graph.neighbours(x)) > d:    return True
            return False
        
        d = 0
        SeptSet_xy = {} # Z for every pair X, Y
        while has_more_neighbours(self.graph, d) is True:
            for x in self.graph.nodes():
                if len(self.graph.neighbours(x)) >= d + 1:
                    for y in self.graph.neighbours(x):
                        # Get all the d-sets of the neighbours of x
                        if d == 0:  new_neigh = [[]]
                        else:
                            new_neigh = [i for i in self.graph.neighbours(x) if i != y]
                            new_neigh = [new_neigh[i:i+d] for i in range(0, len(self.graph.neighbours(x)), d)]
                        
                        # Independance test, knowing the neighbours
                        for z in new_neigh:
                            if is_independant(learner, x, y, z) is True:
                                self.graph.eraseEdge(x,y)
                                if (x,y) in SeptSet_xy.keys():  SeptSet_xy[(x,y)] += z
                                else:   SeptSet_xy[(x,y)] = z

            d += 1
        return {"graph":self.graph, "SeptSet_xy":SeptSet_xy}

    @save_result(save_prefix + "_2.png", save=save_steps)
    def _orient_edges(self, SeptSet_xy):
        """
        Phase 2: orient the skeleton's edges
        """
        # V-structures
        for z in self.graph.nodes():
            neigh = list(self.graph.neighbours(z))
            for i in range(len(neigh)):
                for y in neigh[i+1:]:
                    x = neigh[i]
                    if self.graph.existsEdge(x, y) is False:
                        # Unshielded triple
                        if (x,y) in SeptSet_xy.keys() and z not in SeptSet_xy[(x,y)]:
                            edge_to_arc(self.graph, x, z)
                            edge_to_arc(self.graph, y, z)

        # Propagation
        was_oriented = True # Until no edge can be oriented
        while was_oriented is True:
            was_oriented = False
            for x in self.graph.nodes():
                for y in self.graph.nodes():
                    if self.graph.existsEdge(x, y) is False and self.graph.existsArc(x, y) is True:
                        # No v-structure added
                        for z in self.graph.neighbours(y):
                            if self.graph.existsArc(x, z) and self.graph.existsEdge(z, y) is True:
                                edge_to_arc(graph, z, y)
                                was_oriented = True
                            
                    elif self.graph.existsEdge(x, y) is True and self.graph.hasDirectedPath(x, y):
                        # No cycle
                        edge_to_arc(graph, x, y)
                        was_oriented = True

        return {"graph":self.graph}

    @save_result(save_prefix + "_3.png", save=save_steps)
    def _wrap_up_learning(self):
        """
        Phase 3: fill the other orientations without adding any v-structure
        """
        for x, y in self.graph.edges():
            self.graph.eraseEdge(x, y)
            self.graph.addArc(y, x)

            for z in self.graph.neighbours(y):
                if self.graph.existsArc(z, y):    break
            else:
                self.graph.addArc(x, y)
                self.graph.eraseArc(y, x)

        return {"graph":self.graph}
    
    @save_result(save_prefix + "_final.png", save=save_final)
    def learn(self, bn, learner):
        print("Initializing the graph..")
        self._init_graph(bn)

        print("Learning the skeleton..")
        SeptSet_xy = self._learn_skeleton(learner)["SeptSet_xy"]

        print("Orienting the graph's edges..")
        self._orient_edges(SeptSet_xy)

        print("Wrapping up the orientations..")
        self._wrap_up_learning()

        return {"graph":self.graph}

if __name__ == "__main__":
    bn, lea = generate_bn_and_csv().values()

    pc = PC()
    pc.learn(bn, lea)