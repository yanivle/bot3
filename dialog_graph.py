from dataclasses import dataclass, field
from typing import List
from enum import Enum
from utt import Utt
from state import State
import colors
import goal as goal_module
import statement
import graphviz
import time


@dataclass(frozen=True)
class Vertex(object):
    state: State
    robot_turn: bool

    def __repr__(self):
        return f'({self.state}, robot_turn={self.robot_turn})'


@dataclass(frozen=True)
class Edge(object):
    utt: Utt

    def __repr__(self):
        if self.utt:
            return f'{self.utt.text}'
        return '-'


@dataclass(frozen=True)
class EdgeAndVertex(object):
    edge: Edge
    vertex: Vertex

    def __repr__(self):
        return repr(self.edge)


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


def isTrivial(utt, state):
    for statement in utt.state.statements.statements:
        if state.statements.value(statement.var) != statement.value:
            return False
    for prediction in utt.state.allPredictionStatements():
        if state.statements.value(prediction.var) != prediction.value:
            return False
    return True


class DialogGraph(object):
    def __init__(self, robot_utts, initial_state):
        self.robot_utts = robot_utts
        self.start_vertex = Vertex(initial_state, True)

    def neighbors(self, vertex):
        res = set()
        if vertex.robot_turn:
            for utt in self.robot_utts:
                if utt.requirementsMet(vertex.state):
                    # Don't allow statements that only repeat stuff or make predictions that are already set.
                    if isTrivial(utt, vertex.state):
                        continue
                    new_state = utt.applyToState(vertex.state)
                    ev = EdgeAndVertex(Edge(utt), Vertex(new_state, not vertex.robot_turn))
                    res.add(ev)
        # Human turn - apply predictions (for now applying all together - we might want to generate separate neighbors).
        else:
            if vertex.state.allPredictionStatements():
                new_state = vertex.state.clone()
                for prediction in vertex.state.allPredictionStatements():
                    new_state.statements.update(prediction)
                new_state.predictions = statement.StatementList()
                new_state.positive_predictions = statement.StatementList()
                ev = EdgeAndVertex(Edge(None), Vertex(new_state, not vertex.robot_turn))
                res.add(ev)
            else:
                ev = EdgeAndVertex(Edge(None), Vertex(vertex.state.clone(), not vertex.robot_turn))
                res.add(ev)
        return res

    def bfs(self, goal, max_path_length=7):
        node_to_label = {}
        dot = graphviz.Digraph()

        def vertex_to_label(vertex):
            if vertex.robot_turn:
                header = f'R{len(self.neighbors(vertex))}<br/>'
            else:
                header = f'H{len(self.neighbors(vertex))}<br/>'
            statements = '<br/>'.join(repr(x) for x in vertex.state.statements.statements)
            preds = '<br/>'.join(repr(x) for x in vertex.state.allPredictionStatements())
            remaining = '<br/>'.join(repr(x) for x in goal.unsatisfiedStatements(vertex.state))
            if remaining:
                remaining = f'<font color="red">{remaining}</font>'
            if not preds:
                return '<' + header + statements + '<br/>Unsatisfied:<br/>' + remaining + '>'
            return '<' + header + statements + '<br/>Preds:<br/>' + preds + '<br/>Unsatisfied:<br/>' + remaining + '>'

        def vertex_to_id(vertex):
            label = vertex_to_label(vertex)
            if label not in node_to_label:
                #id = str(len(node_to_label))
                the_id = str(id(vertex))
                node_to_label[label] = the_id
                color = 'white'
                if goal.falseGivenState(vertex.state):
                    color = 'red'
                elif goal.satisfiedByState(vertex.state):
                    color = 'green'
                elif goal_statement.trueGivenStatementList(vertex.state.statements):
                    color = 'deepskyblue'
                dot.attr('node', fillcolor=color, style='filled')
                dot.node(the_id, label)
            else:
                the_id = node_to_label[label]
            return the_id

        goal_statement = goal.firstUnsatisfiedStatement(self.start_vertex.state.statements)
        assert goal_statement
        res = []
        queue = [(self.start_vertex, Path.initFromVertex(self.start_vertex))]
        visited = set()
        while queue:
            (vertex, path) = queue.pop(0)
            visited.add(vertex)
            if len(path) > max_path_length:
                break
            # print('Path:', path)
            # print(f'Visited {visited_count} nodes.')
            neighbors = self.neighbors(vertex)
            # print(f'vertex: {vertex}')
            # print(f'{len(neighbors)} neighbors.')
            for neighbor in neighbors:
                # print(f'neighbor: {neighbor}')
                # print(neighbor.vertex.state)
                if path.visited(neighbor.vertex):
                    # print('Already visited')
                    continue
                dot.edge(vertex_to_id(vertex), vertex_to_id(neighbor.vertex), repr(neighbor.edge))
                # elif goal_statement.trueGivenStatementList(neighbor.vertex.state.statements):
                if goal.satisfiedByState(neighbor.vertex.state):
                    # print('Satisfied!')
                    res.append(path + neighbor)
                    max_path_length = len(path)
                elif len(path) < max_path_length:
                    if not goal.falseGivenState(neighbor.vertex.state):
                        # print('Will explore.')
                        queue.append((neighbor.vertex, path + neighbor))
                    else:
                        pass
                        # print('Goal contradicted by state')
                else:
                    pass
        dot.attr(label=f'Goal: {goal.name}\nGoal statement: {repr(goal_statement)}')
        dot.attr(labelloc='t')
        dot.view(f'/tmp/botdot{time.time()}.gv')
        # graph.view()
        return res


def getActiveGoal(state, goals):
    # TODO: need to consider positive_predictions here?
    if state.predictions:
        new_goal = goal_module.Goal(
            'Interest', statement.GoalStatementList.fromStatementList(state.predictions))
        return new_goal
    for goal in goals:
        if goal.canBeTrueGivenState(state):
            print('Goal:', goal.name)
            return goal


def getNextUtt(state, robot_utts, goals) -> Utt:
    # print('Start state:', state)
    dg = DialogGraph(robot_utts, state)
    goal = getActiveGoal(state, goals)
    if goal.satisfiedByState(state):
        print(f'{colors.C("*** ALL DONE***", colors.HEADER)}')
        return [robot_utts[-1]]
    paths = dg.bfs(goal)
    # print(f'Found total of {len(paths)} paths to goal.')
    if paths:
        #print('Selected path:', paths[0])
        # BUG: Something is very weird with the lengths of the paths...
        # Debug this - I was expecting them to be 1 when we're 1 away from winning,
        # but sometimes they are long.
        # for path in paths:
        #     print (len(path), path.edges_and_vertices[1].edge.utt)
        return [path.edges_and_vertices[1].edge.utt for path in paths]
    #print('No path found to goal :(')
    return [robot_utts[-1]]
