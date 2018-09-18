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
    tests = {
        'BASIC': [[], [], ['@positive'], [], ['@positive']],
        'ASK_FOR_DETAILS': [[], ['R:DATE=?', '*R:DATE=*'], ['R:FIRST_NAME=?', 'H:BUSINESS_NEEDS_NAME=True', '*R:FIRST_NAME=*'], [], ['@positive']],
        # BUG: the below line (and others) don't work:
        # The temporary goal, of getting *any* value for FIRST_NAME is immediately
        # satisfied.
        # We should probably change the syntax of prediction to instead be focus
        # and just boost the value of that variable from the goal (and if it's not in the goal, go to previous goals until we find it?)
        'VERIFY_WRONG_DETAILS': [[], ['R:FIRST_NAME=John', 'H:BUSINESS_NEEDS_NAME=True', '*R:FIRST_NAME=*'], ['R:DATE=today'], [], ['@positive']],
        'NO_RESERVATIONS': [[], ['H:AVAILABILITY=False'], ['H:ESTIMATED_WAIT=short']],
        'NO_RESERVATIONS_FOR_7pm': [[], ['H:AVAILABILITY[TIME=7pm]=False'], ['@positive'], ['@positive'], ['AGREED_TIME=7:30pm']],
        'NO_RESERVATIONS_FOR_7pm_AND_730pm': [[], ['H:AVAILABILITY[TIME=7pm]=False', 'H:AVAILABILITY[TIME=7:30pm]=False'], ['@positive'], ['@positive'], ['AGREED_TIME=8pm']],
        'NO_RESERVATIONS_FOR_7pm_AND_730pm_AND_8pm': [[], ['H:AVAILABILITY[TIME=7pm]=False', 'H:AVAILABILITY[TIME=7:30pm]=False'], ['H:AVAILABILITY[TIME=8pm]=False'], ['H:ESTIMATED_WAIT=long']],
        'VERIFY_WRONG_DETAILS_SIMULTANEOUSLY': [[], ['R:FIRST_NAME=John', 'H:BUSINESS_NEEDS_NAME=True', 'R:DATE=today', '*R:FIRST_NAME=*', '*R:DATE=*'], ['R:DATE=tomorrow'], [], ['@positive']],
        'SAYING_YES': [[], ['*R:FIRST_NAME=*', '@R:FIRST_NAME=Yaniv', 'H:BUSINESS_NEEDS_NAME=True']],
    }

    for test_name, test in tests.items():
        print(f'Test: {colors.C(test_name, colors.FAIL)}')
        state = initial_state.clone()
        state_history = [state]
        while test:
            human_utt = getHumanUttFromTest(test)

            state = human_utt.applyToState(state)
            state_history.append(state)
            # print(colors.C(human_utt.text, colors.OKBLUE))
            # print(state)

            possible_robot_utts = dialog_graph.getNextUtt(state, robot_utts, human_utts, goals)
            robot_utt, alternatives = possible_robot_utts[0], possible_robot_utts[1:]
            print(colors.C(f'{robot_utt.text}', colors.OKGREEN))
            for alternative in set(alternatives) - {robot_utt}:
                print(f'  Alt: {alternative.text}')
            state = robot_utt.applyToState(state)


def interactiveMode(state):
    while True:
        human_utt = getHumanUttFreeform()

        state = human_utt.applyToState(state)
        print(colors.C(human_utt.text, colors.OKBLUE))
        # print(state)

        possible_robot_utts = dialog_graph.getNextUtt(state, robot_utts, human_utts, goals)
        robot_utt, alternatives = possible_robot_utts[0], possible_robot_utts[1:]
        print(colors.C(f'{robot_utt.text}', colors.OKGREEN))
        for alternative in set(alternatives) - {robot_utt}:
            print(f'  Alt: {alternative.text}')
        state = robot_utt.applyToState(state)
        # print(state)


runTests(initial_state)
interactiveMode(initial_state)
