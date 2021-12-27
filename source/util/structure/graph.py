import sys
import copy

sys.setrecursionlimit(900000)


class ConnectedComponent:
    """全連接圖。

    Attributes:
        vertices([source.util.structure.vertex.Vertex])
        transportation_ids

    Args:
        vertices([source.util.structure.vertex.Vertex])
        transportation_ids

    """

    def __init__(self, vertices, transportation_ids):
        self.vertices = vertices
        self.transportation_ids = transportation_ids

    def contains(self, vertex_id):
        for vertex in self.vertices:
            if vertex_id == vertex.get_id():
                return True
        return False


class Graph:
    """圖。

    Attributes:
        __adj_dict ({[str]}): 本圖的鄰接表
            e.g. { "1_2_3": ["2_3_4", "5_6_7"], "2_3_4": ["1_2_3"], "5_6_7": ["1_2_3"] }
        __vertices ([Vertex]): 圖中有的點列表
        __vertex_id_dict ({Vertex}): 圖中有的點列表
        __vertex_coord_dict ({Vertex}): 圖中有的點列表

    """

    def __init__(self):
        """Graph 建構子。
        """
        self.__adj_dict = dict()
        self.__vertices = list()
        self.__vertex_id_dict = dict()
        self.__vertex_coord_dict = dict()

    def add_vertex(self, vertex, adj_list):
        """增加點與其連結資訊。

        Args:
            vertex (source.util.structure.vertex.Vertex): 要新增的點的資訊
            adj_list ([str]): 該新增點之 adjacency list

        Raises:
            TypeError: 參數型別錯誤

        """
        if type(vertex).__name__ != 'Vertex':
            raise TypeError('add_vertex 的參數 vertex 型別錯誤')
        elif type(adj_list).__name__ != 'list':
            raise TypeError('add_vertex 的參數 adj_list 型別錯誤')

        self.__vertices.append(vertex)
        self.__vertex_id_dict[vertex.get_id()] = vertex
        self.__vertex_coord_dict[vertex.get_coordinate()] = vertex
        ID = vertex.get_id()
        self.__adj_dict[ID] = adj_list

    def get_xs(self):
        """取得所有點的 x 座標。

        Returns:
            [float]: 所有點的 x 座標

        """
        return [v.get_coordinate()[0] for v in self.__vertices]

    def get_ys(self):
        """取得所有點的 y 座標。

        Returns:
            [float]: 所有點的 y 座標

        """
        return [v.get_coordinate()[1] for v in self.__vertices]

    def get_adj_dict(self, gen_new=True):
        """取得所有點的 adjacency list。

        Returns:
            {[str]}: 所有點的 adjacency list

        """
        if gen_new:
            return copy.deepcopy(self.__adj_dict)
        return self.__adj_dict

    def get_coordinate_by_vertex_id(self, ID):
        """利用 ID 取得點的座標。

        Returns:
            (float, float, float): 點的座標
            None: 若找不到該點

        Raises:
            TypeError: 如果 ID 型別錯誤

        """
        if type(ID).__name__ != "str":
            raise TypeError("id型別錯誤")
        try:
            return self.__vertex_id_dict[ID].get_coordinate()
        except:
            print("找不到點{}".format(ID))
            return None

    def get_vertex_by_id(self, ID):
        """利用 id 取得點的資訊。

        Args:
            ID (str): 要取得的點的id

        Returns:
            source.util.structure.vertex.Vertex: 點的資訊

        Raises:
            TypeError: 如果 ID 型別錯誤

        """
        if type(ID).__name__ != "str":
            raise TypeError("id型別錯誤")
        try:
            return copy.deepcopy(self.__vertex_id_dict[ID])
        except:
            print("找不到點{}".format(ID))
            return None

    def get_vertex_ids(self):
        """取得所有點的 id。

        Returns:
            [str]: 所有點的 id

        """
        return list(self.__vertex_id_dict.keys())

    def get_vetex_by_coordinate(self, coordinate):
        """利用 coordinate 取得點的資訊。

        Args:
            coordinate (tuple(float, float, float)): 要取得的點的網格座標

        Returns:
            source.util.structure.vertex.Vertex: 點的資訊

        Raises:
            TypeError: 如果 coordinate 型別錯誤

        """
        if type(coordinate).__name__ != "tuple":
            raise TypeError("coordinate 型別錯誤")
        try:
            return copy.deepcopy(self.__vertex_coord_dict[coordinate])
        except:
            return None

    def get_adj_list_by_id(self, ID):
        """利用 id 取得此點的 adjacency list。

        Args:
            ID (str): 要取得的點的id

        Returns:
            [str]: 點的 adjacency list

        Raises:
            TypeError: 如果 ID 型別錯誤

        """
        if type(ID).__name__ != "str":
            raise TypeError("id 型別錯誤")
        return copy.deepcopy(self.__adj_dict[ID])

    def add_vertex_to_adj_list_by_id(self, ID, v_id):
        """增加 id 的 adjacency list 對應到的點。

        Args:
            ID (str): 要被修改 adjacency list 的點的 id
            v_id (str): 新增點的 id

        Raises:
            TypeError: 如果 ID 或 v_id 型別錯誤

        """
        if type(ID).__name__ != "str":
            raise TypeError("id 型別錯誤")
        elif type(v_id).__name__ != "str":
            raise TypeError("v_id 型別錯誤")

        self.__adj_dict[ID].append(v_id)

    def connect_vertex_by_id(self, v_id1, v_id2):
        """連接兩個 vertex 並加到 adj_list 及其他資料結構。

        Args:
            v_id1 (str): 點 id 1
            v_id2 (str): 點 id 2

        Raises:
            TypeError: 如果 v_id1 或 v_id2 型別錯誤

        """
        if type(v_id1).__name__ != "str":
            raise TypeError("v_id1 型別錯誤")
        elif type(v_id2).__name__ != "str":
            raise TypeError("v_id2 型別錯誤")

        self.__adj_dict[v_id1].append(v_id2)
        self.__adj_dict[v_id2].append(v_id1)

    def disconnect_vertex_by_id(self, v_id1, v_id2):
        """斷開兩個 vertex 並從 adj_list 刪除。

        Args:
            v_id1 (str): 點 id 1
            v_id2 (str): 點 id 2

        Raises:
            TypeError: 如果 v_id1 或 v_id2 型別錯誤

        """
        if type(v_id1).__name__ != "str":
            raise TypeError("v_id1 型別錯誤")
        elif type(v_id2).__name__ != "str":
            raise TypeError("v_id2 型別錯誤")

        self.__adj_dict[v_id1].remove(v_id2)
        self.__adj_dict[v_id2].remove(v_id1)

    def DFS_util(self, id):
        """DFS function（遞迴在 Windows 上會 stack overflow，因此改成 Loop）。

        Args:
            connected_components ([str]): 目前 connected_components
            id (str): 欲新增點的 id
            visited ({bool}): 記錄點是否已被造訪
            e.g.
            {
                "0_0_99.45": True,
                "0_1_99.45": False
            }

        Returns:
            [str]: new connected_components

        Raises:
            TypeError: 如果 ID 或 v_id 型別錯誤

        """

        stack = list()
        stack.append(id)
        visited = dict({key: False for key in self.__adj_dict.keys()})
        connected_components = list()

        while stack:
            current_id = stack.pop(-1)
            if not visited[current_id]:
                visited[current_id] = True
                connected_components.append(current_id)
                for connected_node_id in self.__adj_dict[current_id]:
                    stack.append(connected_node_id)

        return connected_components

    def calculate_connected_components(self, transportation_id):
        """計算並取得傳送點所在之 connected components。

        Args:
            transportation_id ([str]): 傳送點的 ID

        Returns:
            [str]: connected components

        Raises:
            IndexError: 在 adjacency list 裡面找不到該傳送點 ID

        """
        if transportation_id not in self.__adj_dict.keys():
            raise IndexError(
                'calculate_connected_components 的 graph 找不到該 transportation_id'
            )
        return copy.deepcopy(self.DFS_util(transportation_id))

    def set_adj_list_by_id(self, target_id, old_id, new_id):
        """對目標點的 adj_list 做更動，將對應到的 old_id 改成 new_id。

        Args:
            target_id (str): 目標點的 id
            old_id (str): 舊點的 id
            new_id (str): 新點的 id

        """
        for idx, element in enumerate(self.__adj_dict[target_id]):
            if element == old_id:
                self.__adj_dict[target_id][idx] = new_id
                break

    def generate_instance(self, failed_vertex_id, failed_block) -> None:
        """將某案例的傳送點和在防煙區劃中的點從 adj_list 中移除。

        Args:
            failed_vertex_id (str): 傳送點的 id
            failed_block ([str]): 防煙區劃中點的 id

        """
        self.__clear_records = list()  # list([id: dst])

        # remove failed vertex
        if failed_vertex_id in self.__adj_dict:
            to_delete = self.__adj_dict[failed_vertex_id]
            self.__adj_dict[failed_vertex_id] = list()
            for vertex_id in to_delete:
                self.__clear_records.append([failed_vertex_id, vertex_id])
                self.__adj_dict[vertex_id].remove(failed_vertex_id)
        else:
            if failed_vertex_id != "":
                raise ValueError("failed vertex id not in instance graph")

        # remove failed block
        for failed_vertex_id in failed_block:
            to_delete = self.__adj_dict[failed_vertex_id]
            self.__adj_dict[failed_vertex_id] = list()
            for vertex_id in to_delete:
                self.__clear_records.append([failed_vertex_id, vertex_id])
                self.__adj_dict[vertex_id].remove(failed_vertex_id)

    def restore_instance(self):
        """將案例復原。
        """
        for failed_vertex_id, vertex_id in self.__clear_records:
            self.__adj_dict[failed_vertex_id].append(vertex_id)
            self.__adj_dict[vertex_id].append(failed_vertex_id)
