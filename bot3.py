from itertools import chain, combinations
import pprint
import utt
import response_logic
import goal as goal_module
import state as state_module
import colors
import diff as diff_module
from diff import DiffType
import var_spec
import event_log
import dialog_graph

bot_module_base = 'modules/rr'
# bot_module_base = 'modules/haggler'
robot_utts = utt.parseUttSpec(bot_module_base + '/robot_utts')
human_utts = utt.parseUttSpec(bot_module_base + '/human_utts')
goal_module.parseGoalsSpec(bot_module_base + '/goal_spec')
goals = [goal for goal in goal_module.all_goals.values() if goal.priority > 0]

for i, goal in enumerate(goals):
    print(f'Goal {i}: {goal}\n')

initial_state = state_module.State.fromFile(bot_module_base + '/initial_state')


def getHumanUttFreeform():
    print('Vars: ' + ', '.join(var_spec.keys.keys()))
    lines = ['<INTERACTIVE>']
    line = input('>>> ')
    while line:
        lines.append(line)
        line = input('>>> ')
    res = utt.Utt.fromText('\n'.join(lines))
    print(res)
    return res


def getHumanUtt():
    for i, utt in enumerate(human_utts):
        print(f'{i}) {utt.text}')
    idx = int(input('>>> '))
    return human_utts[idx]


# TODO: not initiating var_spec from Goal - fix.
var_spec = var_spec.VarSpec.fromFileAndUpdate(
    bot_module_base + '/var_spec', robot_utts + human_utts)
config = response_logic.Config(var_spec, repeated_utt_demotion=1)
scoring_params = response_logic.ScoringParams(event_log.EventLog([]), config)


def interactiveMode(state):
    while True:
        dg = dialog_graph.DialogGraph(robot_utts, human_utts, state)
        paths_to_goal = dg.bfs(goals[0])
        print(f'Found total of {len(paths_to_goal)} paths to goal.')
        for path in paths_to_goal:
            print(path)

        human_utt = getHumanUtt()
        # human_utt = getHumanUttFreeform()
        scoring_params.event_log.add(human_utt)
        new_state = human_utt.applyToState(state)
        diff = diff_module.diffStates(state, new_state)
        state = new_state
        print(colors.C(human_utt.text, colors.OKBLUE))
        pprint.pprint(diff)

        goal, robot_utt, score = response_logic.bestReplyForAllGoals(
            state, goals, robot_utts, scoring_params)
        scoring_params.event_log.add(robot_utt)
        print(f'Advancing towards {colors.C(goal.name, colors.HEADER)} (score={score})')
        new_state = robot_utt.applyToState(state)
        diff = diff_module.diffStates(state, new_state)
        state = new_state
        print(colors.C(f'{robot_utt.text}', colors.OKGREEN))
        pprint.pprint(diff)

        diff_to_goal = diff_module.diffStatementLists(
            state.statements, goal.statements, allowed_types=[DiffType.ADDED, DiffType.CHANGED])
        print(f'Diff towards goal "{colors.C(goal.name, colors.HEADER)}" {diff_to_goal}')


response_logic.VERBOSE = True

interactiveMode(initial_state)
