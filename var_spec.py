from dataclasses import dataclass, field
from typing import List


@dataclass
class Variable(object):
    name: str
    correctible: bool = False

    @staticmethod
    def fromText(text):
        name


@dataclass
class VarSpec(object):
    vars: List[Variable]


# def getKeysFromState(state):
#     return set(state.statements.statements.keys()) | set(state.predictions.statements.keys())
#
#
# def getKeysFromStateContainer(container):
#     return getKeysFromState(container.state)
#
#
# def getKeysFromStateContainerList(container_list):
#     return functools.reduce(lambda x, y: x | y, (getKeysFromStateContainer(container) for container in container_list), set())
#
#
# class VarSpec(prioritized_keys.PrioritizedKeys):
#     def extendFromStateContainers(self, container_list, default_priority=0.0):
#         keys_set = getKeysFromStateContainerList(container_list)
#         for key in keys_set:
#             if key not in self.keys:
#                 self.keys[key] = default_priority
#
#     @staticmethod
#     def fromFileAndUpdate(filename, container_list):
#         var_spec = VarSpec({})
#         var_spec.load(filename)
#         var_spec.extendFromStateContainers(container_list)
#         var_spec.save(filename)
#         return var_spec
