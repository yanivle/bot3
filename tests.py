import util

class Test(object):
    @staticmethod
    def fromText(text):
        lines = [line.strip() for line in text.split('\n')]
        name = lines.pop(0)

        human_utts = []
        robot_utts = []
