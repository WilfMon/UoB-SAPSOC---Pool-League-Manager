import networkx as nx
import itertools

from networkx import max_weight_matching

G = nx.Graph()

players = ["name1", "name2", "name3", "name4"]

G.add_nodes_from(players) # add players to the graph
for a, b in itertools.combinations(players, 2): # add connections between players
    G.add_edge(a, b)

rounds = []
round_num = 1

while G.number_of_edges() > 0:
    matches = max_weight_matching(G, maxcardinality=True)
    
    rounds.append(matches)
    
    # Remove used matches so they can't repeat
    for u, v in matches:
        G.remove_edge(u, v)
    
    round_num += 1

# Print schedule
for i, rnd in enumerate(rounds, 1):
    print(f"Round {i}: {list(rnd)}")