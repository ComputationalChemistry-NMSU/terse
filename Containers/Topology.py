if __name__ == "__main__":
    import sys
    sys.path.append('..')

import logging
from Top import Top

log = logging.getLogger(__name__)


class Topology(Top):
    """
    Basically, it is just a named dictionary of dictionaries,
    adapted to store connectivity matrix

    For NBO topologies, atomic indexing starts from 1!
    """
    def __init__(self,name):
        self.name = name
        self.data = {}

    def __len__(self):
        return len(self.data)

    def increaseOrder(self,at1,at2):
        if not at1 in self.data:
            self.data[at1] = {}
        if not at2 in self.data[at1]:
            self.data[at1][at2] = 0
        self.data[at1][at2] += 1


#
#
#
#
#
if __name__ == "__main__":
    t = Topology('test')
    t.increaseOrder(1,2)
    t.increaseOrder(1,2)
    t.increaseOrder(2,3)
    t.increaseOrder(3,4)
    t.increaseOrder(3,4)
    print t
