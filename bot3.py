from itertools import chain, combinations
import pprint
import utt
import response_logic
import goal
import state as state_module
import colors
import diff as diff_module
from diff import DiffType
import var_spec

robot_utts = utt.parseUttSpec('robot_utts')
human_utts = utt.parseUttSpec('human_utts')
goals = goal.parseGoalsSpec('goal_spec')

vs = var_spec.VarSpec({})
vs.load('var_spec')
vs.extendFromStateContainers(robot_utts + human_utts + goals)
vs.save('var_spec')

initial_state = state_module.State.fromText('''
RESERVATIONS_ACCEPTED=True
''')


def getHumanUtt():
    for i, utt in enumerate(human_utts):
        print(f'{i}) {utt.text}')
    idx = int(input('>>> '))
    return human_utts[idx]


def interactiveMode(state):
    while True:
        human_utt = getHumanUtt()
        state, diff = response_logic.applyUttAndDiff(state, human_utt)
        print(colors.C(human_utt.text, colors.OKBLUE))
        pprint.pprint(diff)

        goal, utt, score = response_logic.bestReplyForAllGoals(state, goals, robot_utts)
        print(f'Advancing towards {colors.C(goal.name, colors.HEADER)} (score={score})')
        state, diff = response_logic.applyUttAndDiff(state, utt)
        print(colors.C(f'{utt.text}', colors.OKGREEN))
        pprint.pprint(diff)

        diff_to_goal = diff_module.diffStatementLists(
            state.statement_list, goal.state.statement_list, allowed_types=[DiffType.ADDED, DiffType.CHANGED])
        print(f'Diff towards goal "{colors.C(goal.name, colors.HEADER)}" {diff_to_goal}')


response_logic.VERBOSE = True

# initial_state = response_logic.applyUtt(initial_state, human_utts[3])
interactiveMode(initial_state)
