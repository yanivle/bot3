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

    def __repr__(self):
        return f'Vertex({self.state})'


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


def stateAfterHumanTurn(vertex):
    res = vertex.state.clone()
    for prediction in vertex.state.allPredictionStatements():
        res.statements.update(prediction)
    return res

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
        self.start_vertex = Vertex(initial_state)

    def neighbors(self, vertex, goal):
        res = set()
        state_after_human_turn = stateAfterHumanTurn(vertex)
        if goal.satisfiedByState(state_after_human_turn):
            return {EdgeAndVertex(Edge(None), Vertex(state_after_human_turn))}
        if goal.falseGivenState(state_after_human_turn):
            return {EdgeAndVertex(Edge(None), Vertex(state_after_human_turn))}
        state_after_human_turn.predictions = statement.StatementList()
        state_after_human_turn.positive_predictions = statement.StatementList()
        for utt in self.robot_utts:
            if utt.requirementsMet(state_after_human_turn):
                # Don't allow statements that only repeat stuff or make predictions that are already set.
                if not isTrivial(utt, state_after_human_turn):
                    new_state = utt.applyToState(state_after_human_turn)
                    ev = EdgeAndVertex(Edge(utt), Vertex(new_state))
                    res.add(ev)
        return res

    def bfs(self, goal, max_path_length=5, plot=False, max_nodes_to_visit=1000):
        node_to_label = {}
        dot = graphviz.Digraph() if plot else None

        def vertex_to_label(vertex):
            header = f'{len(self.neighbors(vertex, goal))}<br/>'
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

        res = []
        queue = [(self.start_vertex, Path.initFromVertex(self.start_vertex))]
        visited = set()
        while queue:
            (vertex, path) = queue.pop(0)
            goal_statement = goal.firstUnsatisfiedStatement(vertex.state.statements)
            assert goal_statement
            visited.add(vertex)
            if len(visited) > max_nodes_to_visit:
                break
            if len(path) > max_path_length:
                break
            # print('Path:', path)
            neighbors = self.neighbors(vertex, goal)
            # print(f'vertex: {vertex}')
            # print(f'{len(neighbors)} neighbors.')
            for neighbor in neighbors:
                # print(f'neighbor: {neighbor}')
                # print(neighbor.vertex.state)
                if path.visited(neighbor.vertex):
                    # print('Already visited')
                    continue
                if plot:
                    dot.edge(vertex_to_id(vertex), vertex_to_id(neighbor.vertex), repr(neighbor.edge))
                if neighbor.vertex in visited:
                    continue
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
        if plot:
            initial_goal_statement = goal.firstUnsatisfiedStatement(self.start_vertex.state.statements)
            dot.attr(label=f'Goal: {goal.name}\nGoal statement: {repr(initial_goal_statement)}')
            dot.attr(labelloc='t')
            dot.view(f'/tmp/botdot{time.time()}.gv')
        # graph.view()
        return res


def getActiveGoal(state, goals):
    for goal in goals:
        if goal.canBeTrueGivenState(state):
            if state.predictions:
                new_goal = goal.clone()
                new_goal.name = 'INTEREST'
                predictions = statement.GoalStatementList.fromStatementList(state.predictions)
                positive_predictions = statement.GoalStatementList.fromStatementList(state.positive_predictions)
                new_goal.statements.statements = predictions.statements + positive_predictions.statements + new_goal.statements.statements
                print('Goal:', goal.name)
                return new_goal
            print('Goal:', goal.name)
            return goal


def getNextUtt(state, robot_utts, goals) -> Utt:
    # print('Start state:', state)
    dg = DialogGraph(robot_utts, state)
    goal = getActiveGoal(state, goals)
    if goal.satisfiedByState(state):
        print(f'{colors.C("*** ALL DONE***", colors.HEADER)}')
        return [robot_utts[-1]]
    paths = dg.bfs(goal, plot=False)
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
