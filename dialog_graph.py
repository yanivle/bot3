from dataclasses import dataclass, field
from typing import List
from enum import Enum
from utt import Utt
from state import State


@dataclass(frozen=True)
class Vertex(object):
    state: State
    robot_turn: bool

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

    def add(self, ev):
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
        self.state = initial_state
        self.robot_turn = True
        self.start_vertex = Vertex(initial_state, True)

    def neighbors(self, vertex):
        res = set()
        if vertex.robot_turn:
            for utt in self.robot_utts:
                if utt.requirementsMet(self.state):
                    new_state = utt.applyToState(self.state)
                    ev = EdgeAndVertex(Edge(utt), Vertex(new_state, not vertex.robot_turn))
                    res.add(ev)
        else:  # Human turn.
            if vertex.state.predictions.statements:
                new_state = vertex.state.clone()
                for var, prediction in vertex.state.predictions.statements.items():
                    new_state.statements.addStatement(prediction)
                new_state.predictions.statements = {}
                ev = EdgeAndVertex(Edge(None), Vertex(new_state, not vertex.robot_turn))
                res.add(ev)
        return res

    def bfs(self, goal, max_depth=10):
        res = []
        queue = [(self.start_vertex, Path.initFromVertex(self.start_vertex))]
        while queue:
            (vertex, path) = queue.pop(0)
            print(path)
            print()
            neighbors = self.neighbors(vertex)
            for neighbor in neighbors:
                if path.visited(neighbor.vertex):
                    continue
                if goal.satisfiedBy(neighbor.vertex.state):
                    res.append(path.add(neighbor))
                elif len(path) < max_depth:
                    queue.append((neighbor.vertex, path.add(neighbor)))
        return res
