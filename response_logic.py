import colors
import diff as diff_module

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


def distanceToGoal(state, diff_to_goal):
    dist = 0
    for diff in diff_to_goal.statement_diffs:
        if diff.type == diff_module.DiffType.CHANGED:
            dist += 1000
        elif diff.type == diff_module.DiffType.ADDED:
            if not state.gets(diff.statement2.var):
                dist += 100
        elif diff.type == diff_module.DiffType.REMOVED:
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


def scoreUtt(state, goal, utt):
    score = 0
    new_state, diff = applyUttAndDiff(state, utt)
    diff_to_goal = diff_module.diffStates(new_state, goal.state)
    distance_to_goal = -distanceToGoal(new_state, diff_to_goal)
    redundant_actions = -10 * redundantActions(diff_module.diffStates(utt.state, state))
    redundant_interests = -2 * redundantInterests(diff_to_goal, utt.state.interests)
    answers_interest = 200 if answersInterest(state, utt) else 0
    score = distance_to_goal + redundant_actions + answers_interest + redundant_interests
    score_components = (distance_to_goal, redundant_actions, answers_interest, redundant_interests)
    return score, score_components


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


def scoreForGoal(state, goal, utts):
    res = []
    for utt in utts:
        score, score_components = scoreUtt(state, goal, utt)
        res.append([score, score_components, utt])
    return res


def scoreForAllGoals(state, goals, utts):
    res = []
    for goal in goals:
        scores_for_goal = scoreForGoal(state, goal, utts)
        res += [x + [goal] for x in scores_for_goal]
    return res


def bestReplyForAllGoals(state, goals, utts):
    all_scores = scoreForAllGoals(state, goals, utts)
    srtd = sorted(all_scores, key=lambda x: x[0], reverse=True)
    if VERBOSE:
        for candidate in srtd[:5]:
            print(f'Score:{colors.C(str(candidate[0]), colors.WARNING)} ({candidate[1]}) {candidate[3].name} - {colors.C(candidate[2].text, colors.WARNING)}')
    best = srtd[0]
    return best[3], best[2], best[0]


def choseReply(state, goals):
    for goal in goals:
        paths = bfs_paths(state, goal)
