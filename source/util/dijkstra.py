import heapq

import numpy as np


class DijkNode:
    """Maintain for future usage (maybe).
    """

    def __init__(self, idx, dis):
        self.idx = idx
        self.dis = dis

    def __lt__(self, other):
        """define the behaviour of pq.
        """
        return self.dis < other.dis


class Dijkstra:
    def __init__(self, all_id):
        self.__distance_template = dict((id_, np.inf) for id_ in all_id)
        self.__visited_template = dict((id_, False) for id_ in all_id)
        self.__parent_template = dict((id_, None) for id_ in all_id)

    def __clear_prev_results(self):
        for id_ in self.__distance_template:
            self.__distance_template[id_] = np.inf
        for id_ in self.__visited_template:
            self.__visited_template[id_] = False
        for id_ in self.__parent_template:
            self.__parent_template[id_] = None

    def run(self, connected_component_id, grid_graph, source_id):

        self.__clear_prev_results()

        self.__distance_template[source_id] = 0
        self.__visited_template[source_id] = False
        self.__parent_template[source_id] = source_id
        h = []  # from document, do NOT modify
        heapq.heappush(h, DijkNode(source_id, 0))

        cc_length = len(connected_component_id)
        for _ in range(cc_length):

            id_ = None
            while len(h):
                id_ = h[0].idx
                if self.__visited_template[id_]:
                    heapq.heappop(h)
                else:
                    break

            if id_ == None:
                break
            self.__visited_template[id_] = True

            for node_id in grid_graph[id_]:
                if self.__visited_template[node_id] == False and self.__distance_template[id_] + 1 < self.__distance_template[node_id]:
                    self.__distance_template[node_id] = self.__distance_template[id_] + 1
                    self.__parent_template[node_id] = id_
                    heapq.heappush(h, DijkNode(
                        node_id, self.__distance_template[node_id]))

        distance_ret = dict()
        for id_ in connected_component_id:
            distance_ret[id_] = self.__distance_template[id_]
        parent_ret = dict()
        for id_ in connected_component_id:
            parent_ret[id_] = self.__parent_template[id_]

        return distance_ret, parent_ret
