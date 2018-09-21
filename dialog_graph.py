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

    def turn(self):
        if self.robot_turn:
            return 'R'
        return 'H'

    def __repr__(self):
        if self.robot_turn:
            return f'R - ({self.state})'
        else:
            return f'H - ({self.state})'


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


def simulateHumanTurn(state):
    res = state.clone()
    for prediction in state.allPredictionStatements():
        res.statements.update(prediction)
    res.predictions = statement.StatementList()
    res.positive_predictions = statement.StatementList()
    return res


def isTrivial(utt, state):
    for statement in utt.state.statements.statements + utt.state.allPredictionStatements():
        if state.statements.value(statement.var) != statement.value:
            return False
    if utt.positive:
        for statement in state.positive_predictions.statements:
            if state.statements.value(statement.var) != statement.value:
                return False
    return True


class DialogGraph(object):
    def __init__(self, robot_utts, initial_state):
        self.robot_utts = robot_utts
        self.start_vertex = Vertex(initial_state, True)

    def neighbors(self, vertex, goal):
        res = set()
        if vertex.robot_turn:
            # all predictions should have been cleared into the active goal.
            assert not vertex.state.predictions, 'Have predictions after human turn.'
            for utt in self.robot_utts:
                if utt.requirementsMet(vertex.state):
                    # Don't allow statements that only repeat stuff or make predictions that are already set.
                    if not isTrivial(utt, vertex.state):
                        new_state = utt.applyToState(vertex.state)
                        ev = EdgeAndVertex(Edge(utt), Vertex(new_state, robot_turn=False))
                        res.add(ev)
        else:
            new_state = simulateHumanTurn(vertex.state)
            ev = EdgeAndVertex(Edge(None), Vertex(new_state, robot_turn=True))
            res.add(ev)
        return res

    def bfs(self, goal, goal_statement, max_path_length=10, plot=False, max_nodes_to_visit=1000):
        node_to_label = {}
        dot = graphviz.Digraph() if plot else None

        def makeHTMLList(items, title, color):
            res = '<br/>'.join(repr(x) for x in items)
            if res:
                res = f'<font color="{color}"><br/>{title}:<br/>{res}</font>'
                return res
            return ''

        def vertex_to_label(vertex):
            header = f'{vertex.turn()} ({len(self.neighbors(vertex, goal))})<br/>'
            statements = makeHTMLList(vertex.state.statements.statements, 'State', 'black')
            preds = makeHTMLList(vertex.state.allPredictionStatements(), 'Preds', 'blue')
            remaining = makeHTMLList(goal.unsatisfiedStatements(vertex.state), 'Unsatisfied', 'red')
            false = makeHTMLList(goal.falseStatements(vertex.state), 'False', 'red2')
            return '<' + header + statements + preds + remaining + false + '>'

        def vertex_to_id(vertex):
            label = vertex_to_label(vertex)
            if label not in node_to_label:
                #id = str(len(node_to_label))
                the_id = str(id(vertex))
                node_to_label[label] = the_id
                color = 'white'
                if goal.falseGivenState(vertex.state):
                    color = 'violet'
                elif goal.satisfiedByState(vertex.state):
                    color = 'green'
                elif goal_statement.trueGivenStatementList(vertex.state.statements):
                    color = 'deepskyblue'
                dot.attr('node', fillcolor=color, style='filled')
                dot.node(the_id, label)
            else:
                the_id = node_to_label[label]
            return the_id

        initial_num_false_statements = goal.statements.countFalseGivenStatementList(
            self.start_vertex.state.statements)

        res = []
        queue = [(self.start_vertex, Path.initFromVertex(self.start_vertex))]
        visited = set()
        while queue:
            (vertex, path) = queue.pop(0)
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
                    dot.edge(vertex_to_id(vertex), vertex_to_id(
                        neighbor.vertex), repr(neighbor.edge))
                if neighbor.vertex in visited:
                    continue
                num_false = goal.statements.countFalseGivenStatementList(
                    neighbor.vertex.state.statements)
                # Don't allow utts that cause the goal to be false, unless they make things better.
                if num_false and num_false >= initial_num_false_statements:
                    # if goal.falseGivenState(neighbor.vertex.state):
                    # print('Goal contradicted by state')
                    continue
                if goal_statement.trueGivenStatementList(neighbor.vertex.state.statements):
                # if goal.satisfiedByState(neighbor.vertex.state):
                    # print('Satisfied!')
                    res.append(path + neighbor)
                    max_path_length = len(path)
                elif len(path) < max_path_length:
                    # print('Will explore.')
                    queue.append((neighbor.vertex, path + neighbor))
                else:
                    pass
        if plot:
            dot.attr(label=f'Goal: {goal.name}\nGoal statement: {repr(goal_statement)}')
            dot.attr(labelloc='t')
            dot.view(f'/tmp/botdot{time.time()}.gv')
        # graph.view()
        return res


def getActiveGoal(state, goals):
    for goal in goals:
        if goal.canBeTrueGivenState(state):
            if state.predictions:
                new_goal = goal.clone()
                new_goal.name = 'INTEREST + ' + goal.name
                predictions = statement.GoalStatementList.fromStatementList(state.predictions)
                new_goal.statements.statements = predictions.statements + new_goal.statements.statements
                # print(new_goal)
                return new_goal
            return goal


def getNextUtt(state, robot_utts, goals) -> Utt:
    # print('Start state:', state)
    goal = getActiveGoal(state, goals)
    print('Goal:', goal.name)
    if goal.satisfiedByState(state):
        print(f'{colors.C("*** ALL DONE***", colors.HEADER)}')
        return [robot_utts[-1]]
    state.resetPredictions()
    dg = DialogGraph(robot_utts, state)
    goal_statement = goal.firstUnsatisfiedStatement(state.statements)
    assert goal_statement
    # print(goal_statement)
    paths = dg.bfs(goal, goal_statement, plot=False)
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
