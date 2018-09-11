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


def getHumanUttFromTest(test):
    inp = test.pop(0)
    print(colors.C('>>> ' + repr(inp), colors.BOLD))
    lines = ['<TEST>'] + inp
    res = utt.Utt.fromText('\n'.join(lines))
    return res


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


def runTests(state):
    BASIC_FLOW = [[], [], [], ['@positive']]
    ASK_FOR_DETAILS = [[], ['*R:DATE=*', 'R:DATE=?'],
                       ['*R:FIRST_NAME=*', 'R:FIRST_NAME=?'], [], ['@positive']]
    NO_RESERVATIONS_FLOW = [[], ['H:RESERVATIONS_ACCEPTED=False'], ['H:ESTIMATED_WAIT=short']]
    NO_RESERVATIONS_FOR_7pm = [[], ['H:RESERVATIONS_ACCEPTED[TIME=7pm]=False'], [
        '@positive'], [], ['AGREED_TIME=7:30pm']]
    NO_RESERVATIONS_FOR_7pm_and_730pm = [[], ['H:RESERVATIONS_ACCEPTED[TIME=7pm]=False', 'H:RESERVATIONS_ACCEPTED[TIME=7:30pm]=False'], [
        '@positive'], [], ['AGREED_TIME=8pm']]
    tests = [BASIC_FLOW, ASK_FOR_DETAILS, NO_RESERVATIONS_FLOW,
             NO_RESERVATIONS_FOR_7pm, NO_RESERVATIONS_FOR_7pm_and_730pm]
    for test in tests:
        print(colors.C(f'Resetting state', colors.FAIL))
        state = initial_state.clone()
        while test:
            human_utt = getHumanUttFromTest(test)

            state = human_utt.applyToState(state)
            # print(colors.C(human_utt.text, colors.OKBLUE))
            # print(state)

            goal = dialog_graph.getActiveGoal(state, goals)

            robot_utt = dialog_graph.getNextUtt(state, robot_utts, human_utts, goals)
            print(colors.C(f'{robot_utt.text}', colors.OKGREEN))
            state = robot_utt.applyToState(state)


def interactiveMode(state):
    while True:
        human_utt = getHumanUttFreeform(BASIC_FLOW)

        state = human_utt.applyToState(state)
        print(colors.C(human_utt.text, colors.OKBLUE))
        # print(state)

        goal = dialog_graph.getActiveGoal(state, goals)

        robot_utt = dialog_graph.getNextUtt(state, robot_utts, human_utts, goals)
        print(colors.C(f'{robot_utt.text}', colors.OKGREEN))
        state = robot_utt.applyToState(state)
        # print(state)

        # diff_to_goal = diff_module.diffFromStateToGoal(state, goal)
        # print(f'Diff towards goal "{colors.C(goal.name, colors.HEADER)}":')
        # if diff_to_goal.contradicted:
        #     print(f'  contradicted: {diff_to_goal.contradicted}')
        # if diff_to_goal.satisfied:
        #     print(f'  satisfied: {diff_to_goal.satisfied}')
        # if diff_to_goal.remaining:
        #     print(f'  remaining: {diff_to_goal.remaining}')


runTests(initial_state)
