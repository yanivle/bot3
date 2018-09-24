from itertools import chain, combinations
import pprint
import utt
import goal as goal_module
import state as state_module
import colors
import event_log
import dialog_graph
import bot_driver
import statement
from deducer import Deducer

bot_module_base = 'modules/rr'
# bot_module_base = 'modules/haggler'
robot_utts = utt.parseUttSpec(bot_module_base + '/robot_utts')
human_utts = utt.parseUttSpec(bot_module_base + '/human_utts')
goals = goal_module.parseGoalsSpec(bot_module_base + '/goal_spec')
initial_state = state_module.State.fromFile(bot_module_base + '/initial_state')
deducer = Deducer(bot_module_base + '/deductions')

for goal in goals:
    print(goal)

all_vars = initial_state.statements.vars() | set.union(*(goal.statements.vars() for goal in goals)) | set.union(*((utt.state.statements.vars() | utt.state.predictions.vars()
                                                                                                                   | utt.state.positive_predictions.vars()) for utt in robot_utts))
R_vars_to_params = {}
H_vars_to_params = {}
neutral_vars_to_params = {}
for var in all_vars:
    if var.startswith('R:'):
        s = R_vars_to_params
    elif var.startswith('H:'):
        s = H_vars_to_params
    else:
        s = neutral_vars_to_params
    if '[' in var:
        base = var.split('[')[0]
        param = var.split('[')[1].split('=')[0]
        if base not in s:
            s[base] = set()
        s[base].add(param)
    else:
        if var not in s:
            s[var] = set()
print('R-Arrtibutes:')
for v, params in R_vars_to_params.items():
    print(v)
    if params:
        print('  Params:', params)
print()
print('H-Arrtibutes:')
for v, params in H_vars_to_params.items():
    print(v)
    if params:
        print('  Params:', params)
print()
print('Neutral-Arrtibutes:')
for v, params in neutral_vars_to_params.items():
    print(v)
    if params:
        print('  Params:', params)
print()


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


def testLogic():
    while True:
        goal = goals[0]
        print("Enter state:")
        human_utt = getHumanUttFreeform()
        state = state_module.State(human_utt.state.statements)
        if goal.satisfiedByState(state):
            print("Goal satisfied")
        else:
            print("Goal not satisfied - remaining:")
            print('\n'.join(repr(s) for s in goal.unsatisfiedStatements(state)))


def runTests(state):
    tests = {
        'BASIC': [[], [], ['@positive'], [], ['@positive']],
        'ASK_FOR_DETAILS': [[], ['R:DATE=?', '*R:DATE=*'], ['R:FIRST_NAME=?', '*R:FIRST_NAME=*', 'H:BUSINESS_NEEDS_NAME=True'], [], ['@positive']],
        'VERIFY_WRONG_DETAILS': [[], ['R:FIRST_NAME=John', '@R:FIRST_NAME=John', '*R:FIRST_NAME=*', 'H:BUSINESS_NEEDS_NAME=True'], ['R:DATE=today', '@R:DATE=today', '*R:DATE=*'], [], ['@positive']],
        'NO_RESERVATIONS': [[], ['H:AVAILABILITY=False'], ['@positive'], ['H:ESTIMATED_WAIT=short']],
        'NO_RESERVATIONS_FOR_7pm': [[], ['H:AVAILABILITY[TIME=7pm]=False'], ['@positive'], ['H:AVAILABILITY[TIME=7:30pm]=True', 'TIME=7:30pm']],
        'NO_RESERVATIONS_FOR_7pm_2': [[], ['H:AVAILABILITY[TIME=7pm]=False'], ['H:AVAILABILITY[TIME=7:30pm]=True', 'R:FIRST_NAME=?', '*R:FIRST_NAME=*', 'H:BUSINESS_NEEDS_NAME=True'], ['AGREED_TIME=7:30pm']],
        'NO_RESERVATIONS_FOR_7pm_AND_730pm': [[], ['H:AVAILABILITY[TIME=7pm]=False', 'H:AVAILABILITY[TIME=7:30pm]=False'], ['H:AVAILABILITY[TIME=8pm]=True'], ['@positive'], ['AGREED_TIME=8pm']],
        'NO_RESERVATIONS_FOR_7pm_AND_730pm_AND_8pm': [[], ['H:AVAILABILITY[TIME=7pm]=False', 'H:AVAILABILITY[TIME=7:30pm]=False'], ['H:AVAILABILITY[TIME=8pm]=False'], ['H:WALKINGS_ACCEPTED=True', 'H:ESTIMATED_WAIT=long']],
        'VERIFY_WRONG_DETAILS_SIMULTANEOUSLY': [[], ['R:FIRST_NAME=John', 'H:BUSINESS_NEEDS_NAME=True', 'R:DATE=today', '*R:DATE=*', '*R:FIRST_NAME=*'], ['R:DATE=tomorrow'], [], ['@positive']],
        'SAYING_YES': [[], ['R:FIRST_NAME=?', '*R:FIRST_NAME=*', '@R:FIRST_NAME=Yaniv', 'H:BUSINESS_NEEDS_NAME=True'], ['AGREED_TIME=7pm']],
        'NO_AVAILABILITY_FOR_DAY': [[], ['H:AVAILABILITY[DATE=tomorrow]=False'], ['H:WALKINGS_ACCEPTED=True'], ['H:ESTIMATED_WAIT=unknown']],
        'AVAILABILITY_FOR_OTHER_TIMES': [[], ['H:AVAILABILITY[TIME=7:30pm]=True', 'H:AVAILABILITY[TIME=8pm]=True', 'H:AVAILABILITY[TIME=7pm]=False', '*AGREED_TIME=*', 'AGREED_TIME=?'], ['R:FIRST_NAME=?', '*R:FIRST_NAME=*', 'H:BUSINESS_NEEDS_NAME=True'], []],
        'AVAILABILITY_FOR_THIS_TIME': [[], ['H:AVAILABILITY[TIME=7pm]=False'], ['H:AVAILABILITY[TIME=$TIME]=True'], ['@positive'], ['AGREED_TIME=$TIME']],
        'CC_REQUIRED': [[], ['H:CREDIT_CARD_REQUIRED[PARTY_SIZE=5]=True']],
        'CC_REQUIRED_WRONG_PARTY_SIZE': [[], ['H:CREDIT_CARD_REQUIRED[PARTY_SIZE=10]=True', 'R:PARTY_SIZE=10'], ['H:AVAILABILITY[PARTY_SIZE=5]=False', 'H:WALKINGS_ACCEPTED=True', 'H:ESTIMATED_WAIT=short']],
    }

    for test_name, test in tests.items():
        print(f'Test: {colors.C(test_name, colors.FAIL)}')
        state = initial_state.clone()
        driver = bot_driver.BotDriver(initial_state, robot_utts, goals, deducer)
        while test:
            human_utt = getHumanUttFromTest(test)
            # bot_driver.BotDriver.printUtt(human_utt)
            driver.handle(human_utt)


def interactiveMode(state):
    driver = bot_driver.BotDriver(initial_state, robot_utts, goals, deducer)

    while True:
        human_utt = getHumanUttFreeform()
        print(colors.C(human_utt.text, colors.OKBLUE))

        bot_driver.BotDriver.printUtt(human_utt)
        driver.handle(human_utt)


runTests(initial_state)
# interactiveMode(initial_state)
# testLogic()
