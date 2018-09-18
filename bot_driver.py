import colors
import dialog_graph
from statement import StatementList

class BotDriver(object):
    def __init__(self, initial_state, robot_utts, goals):
        self.state = initial_state
        self.robot_utts = robot_utts
        self.goals = goals
        self.state_history = [initial_state]

    def applyUttToState(self, utt):
        self.state = utt.applyToState(self.state)
        self.state_history.append(self.state)

    def rewindState(self, amount):
        self.state_history = self.state_history[:-amount]
        self.state = self.state_history[-1]
        self.state.predictions = self.state.positive_predictions = StatementList()

    @staticmethod
    def printUtt(utt, alternatives=None):
        print(colors.C(f'{utt.text}', colors.OKGREEN))
        if alternatives:
            for alternative in set(alternatives) - {utt}:
                print(f'  Alt: {alternative.text}')

    def handle(self, human_utt):
        if human_utt.sorry:
            self.rewindState(1)
        else:
            self.applyUttToState(human_utt)
        possible_robot_utts = dialog_graph.getNextUtt(self.state, self.robot_utts, self.goals)
        robot_utt, alternatives = possible_robot_utts[0], possible_robot_utts[1:]
        BotDriver.printUtt(robot_utt, alternatives)
        self.applyUttToState(robot_utt)
