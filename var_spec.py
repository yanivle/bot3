from dataclasses import dataclass, field
from typing import Dict
from util import flatten
import parse
import functools


def getVarsFromState(state):
    return set(state.statement_list.statements.keys())


def getVarsFromStateContainer(container):
    return getVarsFromState(container.state)


def getVarsFromStateContainerList(container_list):
    return functools.reduce(lambda x, y: x | y, (getVarsFromStateContainer(container) for container in container_list), set())


@dataclass
class VarSpec(object):
    vars: Dict[str, float]

    def extendFromStateContainers(self, container_list, default_priority=0.0):
        vars_set = getVarsFromStateContainerList(container_list)
        for var in vars_set:
            if var not in self.vars:
                self.vars[var] = default_priority

    def save(self, filename):
        f = open(filename, "w")
        for var_priority in sorted(self.vars.items(), key=lambda x: (x[1], x[0]), reverse=True):
            f.write(f"{var_priority[0]}:{var_priority[1]}\n")
        f.close()

    def load(self, filename):
        f = open(filename, "r")
        txt = f.read()
        lines = txt.split('\n')
        for line in lines:
            r = parse.parse("{var}:{priority}", line)
            if r:
                self.vars[r['var']] = float(r['priority'])
