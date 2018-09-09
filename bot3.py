from itertools import chain, combinations
import pprint
import utt
import goal as goal_module
import state as state_module
import colors
import diff as diff_module
from diff import DiffType
import event_log
import dialog_graph

bot_module_base = 'modules/rr'
# bot_module_base = 'modules/haggler'
robot_utts = utt.parseUttSpec(bot_module_base + '/robot_utts')
human_utts = utt.parseUttSpec(bot_module_base + '/human_utts')
goals = goal_module.parseGoalsSpec(bot_module_base + '/goal_spec')
initial_state = state_module.State.fromFile(bot_module_base + '/initial_state')

for goal in goals:
    print(goal)


def getHumanUttFreeform():
    # print('Vars: ' + ', '.join(var_spec.keys.keys()))
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
# var_spec = var_spec.VarSpec.fromFileAndUpdate(
#     bot_module_base + '/var_spec', robot_utts + human_utts)
# config = response_logic.Config(var_spec, repeated_utt_demotion=1)
# scoring_params = response_logic.ScoringParams(event_log.EventLog([]), config)


def interactiveMode(state):
    while True:
        human_utt = getHumanUttFreeform()
        # human_utt = getHumanUtt()

        new_state = human_utt.applyToState(state)
        # diff = diff_module.diffStates(state, new_state)
        state = new_state
        print(colors.C(human_utt.text, colors.OKBLUE))
        print(state)
        # pprint.pprint(diff)

        goal = dialog_graph.getActiveGoal(state, goals)

        robot_utt = dialog_graph.getNextUtt(state, robot_utts, human_utts, goals)
        print(colors.C(f'{robot_utt.text}', colors.OKGREEN))
        new_state = robot_utt.applyToState(state)
        # diff = diff_module.diffStates(state, new_state)
        state = new_state
        print(state)
        # pprint.pprint(diff)

        diff_to_goal = diff_module.diffFromStateToGoal(state, goal)
        print(f'Diff towards goal "{colors.C(goal.name, colors.HEADER)}":')
        if diff_to_goal.contradicted:
            print(f'  contradicted: {diff_to_goal.contradicted}')
        if diff_to_goal.satisfied:
            print(f'  satisfied: {diff_to_goal.satisfied}')
        if diff_to_goal.remaining:
            print(f'  remaining: {diff_to_goal.remaining}')


interactiveMode(initial_state)
