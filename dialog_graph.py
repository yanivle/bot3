from dataclasses import dataclass, field
from typing import List
from enum import Enum
from utt import Utt
from state import State

@dataclass(frozen=True)
class Vertex(object):
    state: State

    def __repr__(self):
        return f'{self.state}'


@dataclass(frozen=True)
class Edge(object):
    utt: Utt

    def __repr__(self):
        return f'{self.utt}'


@dataclass(frozen=True)
class EdgeAndVertex(object):
    edge: Edge
    vertex: Vertex

    def __repr__(self):
        if self.edge.utt:
            return self.edge.utt.text
        return '-'


@dataclass
class Path(object):
    edges_and_vertices: List[EdgeAndVertex]

    def visited(self, vertex):
        return any(ev.vertex == vertex for ev in self.edges_and_vertices)

    def __add__(self, ev):
        return Path([ev for ev in self.edges_and_vertices] + [ev])

    def __len__(self):
        return len(self.edges_and_vertices)

    @staticmethod
    def initFromVertex(vertex):
        return Path([EdgeAndVertex(Edge(None), vertex)])

    def __repr__(self):
        return f'Path({self.edges_and_vertices})'


class DialogGraph(object):
    def __init__(self, robot_utts, human_utts, initial_state):
        self.robot_utts = robot_utts
        self.human_utts = human_utts
        self.start_vertex = Vertex(initial_state)

    def neighbors(self, vertex):
        res = set()
        if vertex.state.predictions.statements:
            new_state = vertex.state.clone()
            for var, prediction in vertex.state.predictions.statements.items():
                new_state.statements.addStatement(prediction)
            new_state.predictions.statements = {}
            ev = EdgeAndVertex(Edge(None), Vertex(new_state))
            res.add(ev)
        else:
            for utt in self.robot_utts:
                if utt.requirementsMet(vertex.state):
                    new_state = utt.applyToState(vertex.state)
                    ev = EdgeAndVertex(Edge(utt), Vertex(new_state))
                    res.add(ev)
        return res

    def bfs(self, goal, max_depth=10):
        res = []
        queue = [(self.start_vertex, Path.initFromVertex(self.start_vertex))]
        visited_count = 0
        while queue:
            visited_count += 1
            (vertex, path) = queue.pop(0)
            print(f'Visited {visited_count} nodes.')
            # print(vertex.state)
            neighbors = self.neighbors(vertex)
            for neighbor in neighbors:
                if path.visited(neighbor.vertex):
                    continue
                elif goal.satisfiedBy(neighbor.vertex.state):
                    res.append(path + neighbor)
                    max_depth = len(path)
                elif len(path) <= max_depth:
                    queue.append((neighbor.vertex, path + neighbor))
                else:
                    pass
        return res
