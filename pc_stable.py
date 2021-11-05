import json
import itertools

from pc import PC
from utils import *

with open("parameters.json", 'r') as file:
    parameters = json.load(file)["parameters"]

save_folder = parameters["save_folder"]
save_prefix = parameters["save_prefix"]
save_steps = parameters["save_steps"]
save_final = parameters["save_final"]
save_compare = parameters["save_compare"]

class PC_stable(PC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @save_result(save_prefix + "_1.png", save=save_steps, folder=save_folder)
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
        SeptSet_xy = {tuple(sorted(edge)):[] for edge in self.graph.edges()}  # Z for every pair X, Y (sorted)
        while has_more_neighbours(self.graph, d):
            for X, Y in self.graph.edges():
                adj_X_excl_Y = self.graph.neighbours(X).copy()
                adj_X_excl_Y.remove(Y)

                if len(adj_X_excl_Y) >= d:
                    # Get all the d-sets of the neighbours of x
                    for Z in itertools.combinations(adj_X_excl_Y, d):
                        # Independance test, knowing the neighbours
                        if is_independant(learner, X, Y, Z):
                            self.graph.eraseEdge(X, Y)

                            SeptSet_xy[tuple(sorted((X, Y)))] += Z
                        
                        # Break if X and Y are no longer adjacent
                        if X in self.graph.neighbours(Y):   break
                            
            d += 1

        return {"graph":self.graph, "SeptSet_xy":SeptSet_xy}

if __name__ == "__main__":
    bn, learner = generate_bn_and_csv(folder=save_folder).values()
    pc_stable = PC_stable()

    pc_stable.learn(bn, learner)
    _, hamming, skeleton_scores = pc_stable.compare_learned_to_bn(bn).values()

    print("Hamming: {}\nSkeleton scores: {}\n".format(hamming, skeleton_scores))
    print("\nProportion of failed learnings: {}%".format(round(test_robustness(PC_stable) * 100, 3)))