from dataclasses import dataclass, field
import colors
import diff as diff_module
from var_spec import VarSpec
import event_log

VERBOSE = False


def neighbors(state, utts):
    '''return set() of neighbor State.'''
    res = set()
    for utt in utts:
        res.add(applyUtt(state, utt))
    return res


def applyUtt(state, utt):
    state = state.clone()
    for var, statement in utt.state.statements.items():
        state.statement_list.addStatement(statement)
    state.interests = utt.state.interests
    return state


def applyUttAndDiff(org_state, utt):
    state = org_state.clone()
    for var, statement in utt.state.statement_list.statements.items():
        state.statement_list.addStatement(statement)
    state.interests = utt.state.interests
    return state, diff_module.diffStates(org_state, state)


def answersInterest(state, utt):
    for interest in state.interests:
        if utt.state.sets(interest.var):
            return True
    return False


def distanceToGoalNotWrongs(state, diff_to_goal_not_wrongs, scoring_params):
    dist = 0
    for diff in diff_to_goal_not_wrongs.statement_diffs:
        if diff.type == diff_module.DiffType.CHANGED:
            dist += 1000 + scoring_params.config.var_spec.priority(diff.statement1.var)
    return dist


def distanceToGoal(state, diff_to_goal, scoring_params):
    dist = 0
    for diff in diff_to_goal.statement_diffs:
        if diff.type == diff_module.DiffType.CHANGED:
            # Variable messed up from goal
            dist += 1000 + scoring_params.config.var_spec.priority(diff.statement1.var)
        elif diff.type == diff_module.DiffType.ADDED:
            # Variable in goal but not set now
            if not state.gets(diff.statement2.var):
                dist += 100 + scoring_params.config.var_spec.priority(diff.statement2.var)
        elif diff.type == diff_module.DiffType.REMOVED:
            # Variable exists here but not in goal
            dist += 10
    return dist


def redundantActions(diff):
    return sum(1 for d in diff.statement_diffs if d.type == diff_module.DiffType.NOOP)


def redundantInterests(diff, interests):
    res = 0
    needed_vars = [
        statement_diff.statement2.var for statement_diff in diff.statement_diffs if statement_diff.type == diff_module.DiffType.ADDED]
    for interest in interests:
        var = interest.var
        if interest.var not in needed_vars:
            res += 1
    return res


class Score(object):
    def __init__(self):
        self.score = 0
        self.components = []

    def addComponent(self, name, score):
        self.score += score
        self.components.append((name, score))

    def __repr__(self):
        items = [f'{self.score}']
        for name, score in self.components:
            if score:
                items.append(f'{name}={score}')
        return '(' + ', '.join(items) + ')'


def scoreUtt(state, goal, utt, scoring_params):
    score = Score()
    new_state, diff = applyUttAndDiff(state, utt)
    diff_to_goal = diff_module.diffStatementLists(
        new_state.statement_list, goal.statements)

    distance_to_goal = -distanceToGoal(new_state, diff_to_goal, scoring_params)
    score.addComponent('distance_to_goal', distance_to_goal)

    diff_to_goal_not_wrongs = diff_module.diffStatementLists(
        new_state.statement_list, goal.not_wrongs_statements)
    distance_to_goal_not_wrongs = - \
        distanceToGoalNotWrongs(new_state, diff_to_goal_not_wrongs, scoring_params)
    score.addComponent('not_wrongs', distance_to_goal_not_wrongs)

    redundant_actions = -10 * redundantActions(diff_module.diffStates(utt.state, state))
    score.addComponent('redundant_actions', redundant_actions)

    redundant_interests = -2 * redundantInterests(diff_to_goal, utt.state.interests)
    score.addComponent('redundant_interests', redundant_interests)

    answers_interest = 200 if answersInterest(state, utt) else 0
    score.addComponent('answers_interest', answers_interest)

    repeated_utt_demotion = -scoring_params.config.repeated_utt_demotion * \
        scoring_params.event_log.utts.count(utt)

    score.addComponent('repeated_utt_demotion', repeated_utt_demotion)

    score.addComponent('goal_priority', goal.priority)

    return score


def bfsPaths(start, goal, max_depth=10):
    res = []
    queue = [(start, [start])]
    while queue:
        (vertex, path) = queue.pop(0)
        for next in neighbors(vertex) - set(path):
            if goal.satisfied_by(next):
                res.append(path + [next])
            else:
                if len(path) < max_depth:
                    queue.append((next, path + [next]))
    return res


def scoreForGoal(state, goal, utts, scoring_params):
    '''Returns [[score, utt]]'''
    res = []
    for utt in utts:
        score = scoreUtt(state, goal, utt, scoring_params)
        res.append([score, utt])
    return res


def scoreForAllGoals(state, goals, utts, scoring_params):
    '''Returns [[score, utt, goal]]'''
    res = []
    for goal in goals:
        scores_for_goal = scoreForGoal(state, goal, utts, scoring_params)
        res += [x + [goal] for x in scores_for_goal]
    return res


@dataclass
class Config(object):
    var_spec: VarSpec
    repeated_utt_demotion: int


@dataclass
class ScoringParams(object):
    event_log: event_log.EventLog
    config: Config


def bestReplyForAllGoals(state, goals, utts, scoring_params):
    '''Returns (goal, robot_utt, score)'''
    all_scores = scoreForAllGoals(state, goals, utts, scoring_params)
    srtd = sorted(all_scores, key=lambda x: x[0].score, reverse=True)
    if VERBOSE:
        for candidate in srtd[:5]:
            print(f'{candidate[0]} {candidate[2].name} - {colors.C(candidate[1].text, colors.WARNING)}')
    best = srtd[0]
    return best[2], best[1], best[0]


def choseReply(state, goals):
    for goal in goals:
        paths = bfs_paths(state, goal)
