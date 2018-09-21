from itertools import chain, combinations
import pprint
import utt
import goal as goal_module
import state as state_module
import colors
import event_log
import dialog_graph
import bot_driver

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
        'ASK_FOR_DETAILS': [[], ['R:DATE=?', '*R:DATE=*'], ['R:FIRST_NAME=?', '*R:FIRST_NAME=*', 'H:BUSINESS_NEEDS_NAME=True'], [], ['@positive']],
        'VERIFY_WRONG_DETAILS': [[], ['R:FIRST_NAME=John', '@R:FIRST_NAME=John', '*R:FIRST_NAME=*', 'H:BUSINESS_NEEDS_NAME=True'], ['R:DATE=today', '@R:DATE=today', '*R:DATE=*'], [], ['@positive']],
        'NO_RESERVATIONS': [[], ['H:AVAILABILITY=False'], ['@positive'], ['H:ESTIMATED_WAIT=short']],
        'NO_RESERVATIONS_FOR_7pm': [[], ['H:AVAILABILITY[TIME=7pm]=False'], ['@positive'], ['@positive'], ['AGREED_TIME=7:30pm']],
        'NO_RESERVATIONS_FOR_7pm_2': [[], ['H:AVAILABILITY[TIME=7pm]=False'], ['@positive', 'R:FIRST_NAME=?', '*R:FIRST_NAME=*', 'H:BUSINESS_NEEDS_NAME=True'], ['AGREED_TIME=7:30pm']],
        'NO_RESERVATIONS_FOR_7pm_AND_730pm': [[], ['H:AVAILABILITY[TIME=7pm]=False', 'H:AVAILABILITY[TIME=7:30pm]=False'], ['@positive'], ['@positive'], ['AGREED_TIME=8pm']],
        'NO_RESERVATIONS_FOR_7pm_AND_730pm_AND_8pm': [[], ['H:AVAILABILITY[TIME=7pm]=False', 'H:AVAILABILITY[TIME=7:30pm]=False'], ['H:AVAILABILITY[TIME=8pm]=False'], ['H:WALKINGS_ACCEPTED=True', 'H:ESTIMATED_WAIT=long']],
        # This is not working, because no single intent can fix the state. Need to change the logic to something that improves instead of fixes.
        'VERIFY_WRONG_DETAILS_SIMULTANEOUSLY': [[], ['R:FIRST_NAME=John', 'H:BUSINESS_NEEDS_NAME=True', 'R:DATE=today', '*R:DATE=*', '*R:FIRST_NAME=*'], ['R:DATE=tomorrow'], [], ['@positive']],
        # Why is "Yes" not working for the next test?
        'SAYING_YES': [[], ['R:FIRST_NAME=?', '*R:FIRST_NAME=*', '@R:FIRST_NAME=Yaniv', 'H:BUSINESS_NEEDS_NAME=True'], ['AGREED_TIME=7pm']],
        'NO_AVAILABILITY_FOR_DAY': [[], ['H:AVAILABILITY[DATE=tomorrow]=False'], ['H:WALKINGS_ACCEPTED=True'], ['H:ESTIMATED_WAIT=unknown']],
        'AVAILABILITY_FOR_OTHER_TIMES': [[], ['H:AVAILABILITY[TIME=7:30pm]=True', 'H:AVAILABILITY[TIME=8pm]=True', 'H:AVAILABILITY[TIME=7pm]=False', '*AGREED_TIME=*', 'AGREED_TIME=?']],
    }

    for test_name, test in tests.items():
        print(f'Test: {colors.C(test_name, colors.FAIL)}')
        state = initial_state.clone()
        driver = bot_driver.BotDriver(initial_state, robot_utts, goals)
        while test:
            human_utt = getHumanUttFromTest(test)
            # bot_driver.BotDriver.printUtt(human_utt)
            driver.handle(human_utt)


def interactiveMode(state):
    driver = bot_driver.BotDriver(initial_state, robot_utts, goals)

    while True:
        human_utt = getHumanUttFreeform()
        print(colors.C(human_utt.text, colors.OKBLUE))

        bot_driver.BotDriver.printUtt(human_utt)
        driver.handle(human_utt)


runTests(initial_state)
interactiveMode(initial_state)
