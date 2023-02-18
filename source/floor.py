import os
import sys
import copy
import logging
import numpy as np

from rich import print
from matplotlib.font_manager import FontProperties

from util.structure.linear import Linear
from util.structure.preventzone import PreventZone
from util.structure.vertex import Vertex
from util.structure.axis import Axis
from util.structure.graph import Graph
from util.raycasting import isPointinPolygon
from gui.editor import Editor
from gui.stage_two import Selector
from util.dijkstra import Dijkstra


class Floor:
    """樓層。

    Attributes:
        __name (str): 該樓層的名字
        __obstacles ([Obstacle]): 障礙物列表
        __elevation (float): 樓層的海拔高度
        __transportations ([Transportation]): 傳送點列表
        __contour (Contour): 建築輪廓物件
        __equation_layer ([Linear]): 建物擺設方程式列表
        __border ({float}): 建物的座標邊界
            e.g. { "x_min": 0.3, "x_max": 0.5, "y_min": 0.1, "y_max": 0.7 }
        __density (float): 網格單位長度(英吋)
        __vertical_to_xs ([Axis]): 網格正交於 x 軸方程式
        __vertical_to_ys ([Axis]): 網格正交於 y 軸方程式
        __grid_graph (Graph): 格子點圖
        __connected_components ([ConnectedComponent]): 連接圖列表
        __threshold (int): 誤差容忍值
        prevent_zones ([PreventZone]): 防煙區劃列表

        path_tmp: 繪圖用的路徑暫存變數
        vertex_prevent_dict ({[str]}): 以 prevent_zone_id 為 key ，防煙區劃內的點列表

    Args:
        name (str): 該樓層的名字
        elevation (float): 樓層的海拔高度
        density(float)

    Raises:
        TypeError: 初始化的型別錯誤

    """

    def __init__(self, name, elevation, density):
        """Floor 建構子。

        Args:
            name (str): 該樓層的名字
            elevation (float): 樓層的海拔高度

        Raises:
            TypeError: 初始化的型別錯誤

        """
        if type(elevation).__name__ != "float":
            logging.critical("elevation型別錯誤")
            raise TypeError("elevation型別錯誤")
        self.__name = name
        self.__obstacles = list()
        self.__elevation = elevation
        self.__transportations = list()
        self.__contour = None
        self.__equation_layer = list()
        self.__border = dict()
        self.__density = density
        self.__vertical_to_xs = list()
        self.__vertical_to_ys = list()
        self.__grid_graph = Graph()

        self.__routes = list()
        self.__threshold = 0.2

        self.path_tmp = None
        self.prevent_zones = list()
        self.vertex_prevent_dict = dict()

    def add_obstacle(self, obstacle):
        """在樓層中增加一個障礙物。

        Args:
            obstacle (source.util.structure.obstacle.Obstacle): 障礙物

        Raises:
            TypeError: 初始化的型別錯誤

        """
        if type(obstacle).__name__ != 'Obstacle':
            logging.critical("add_obstacle 的 obstacle 參數型別錯誤")
            raise TypeError("add_obstacle 的 obstacle 參數型別錯誤")

        self.__obstacles.append(copy.deepcopy(obstacle))

    def add_contour(self, contour):
        """加入建築輪廓。

        Args:
            contour (source.util.structure.contour.Contour): 要加入的建築輪廓物件

        Raises:
            TypeError: 初始化的型別錯誤

        """
        if type(contour).__name__ != 'Contour':
            logging.critical("add_contour 的 contour 參數型別錯誤")
            raise TypeError("add_contour 的 contour 參數型別錯誤")

        self.__contour = copy.deepcopy(contour)

    def add_transportation(self, transportation):
        """加入傳送點。

        Args:
            transportation (source.util.structure.transportation.Transportation): 要加入的傳送點物件

        Raises:
            TypeError: 初始化的型別錯誤

        """
        if type(transportation).__name__ != 'Transportation':
            logging.critical("add_transportation 的 transportation 參數型別錯誤")
            raise TypeError("add_transportation 的 transportation 參數型別錯誤")
        self.__transportations.append(copy.deepcopy(transportation))

    def plot(self, ax, prevent_zone_id, plot_mode):
        """繪製輪廓與障礙物圖片。

        Args:
            prevent_zone_id (str): 失效防煙區劃id
            plot_mode (str): 有點有線請為'1'，沒點沒線為'2'，有點沒線為'3'

        """

        logging.info("開始繪製平面圖 ...")
        # 字型(Windows內建字體)
        if os.path.exists(os.path.join("util", "msjh.ttc")):
            font = FontProperties(fname=os.path.join("util", "msjh.ttc"), size=2)
        else:
            try:
                font = FontProperties(fname=os.path.join(sys._MEIPASS, "ttc", "msjh.ttc"), size=2)
            except:
                font = FontProperties(fname=r"c:\windows\fonts\msjh.ttc", size=2)

        # 以下字體非商用
        # if os.path.exists(os.path.join("util", "DFLiHei-Bd.ttc")):
        #     font = FontProperties(fname=os.path.join("util", "DFLiHei-Bd.ttc"), size=1)
        # else:
        #     try:
        #         font = FontProperties(fname=os.path.join(sys._MEIPASS, "ttc", "DFLiHei-Bd.ttc"), size=1)
        #     except:
        #         font = FontProperties(fname=r"C:/Prj/Python/sinotech-escape/tools/DFLiHei-Bd.ttc",size=1)
        
        if self.__contour != None:
            logging.debug("plot contour")
            for line in self.__contour.get_lines():
                xs, ys = zip(
                    *[(line.get_start_point()[0], line.get_start_point()[1]), (line.get_end_point()[0], line.get_end_point()[1])])
                # 沒有讓它封閉
                ax.plot(xs, ys, linewidth=0.2)

        if len(self.__obstacles) != 0:
            logging.debug("plot obstacle")
            for obs in self.__obstacles:
                for line in obs.get_contour().get_lines():
                    xs, ys = zip(*[(line.get_start_point()[0], line.get_start_point()[1]),
                                   (line.get_end_point()[0], line.get_end_point()[1])])
                    ax.plot(xs, ys, linewidth=0.2)

                ax.annotate(obs.get_name(), (line.get_start_point()[
                    0], line.get_start_point()[1]), fontproperties=font)

        if len(self.__transportations) != 0:
            logging.debug("plot transportation")
            trans_x = []
            trans_y = []
            for transportation in self.__transportations:
                trans_x.append(transportation.get_coordinate()[0])
                trans_y.append(transportation.get_coordinate()[1])
            ax.scatter(trans_x, trans_y, s=3, marker='X', c='r', alpha=0.8)
            # for x, y in zip(trans_x, trans_y):
            #     ax.annotate("傳送點", (x, y), fontproperties=font, c="r")

        logging.debug("plot vertex")

        if prevent_zone_id in self.vertex_prevent_dict:
            prevent_v_ids = self.vertex_prevent_dict[prevent_zone_id]
            xs = list()
            ys = list()
            for v_id in prevent_v_ids:
                if v_id.count("_") == 1:  # is transportation
                    splited_v_id = v_id.split("_")
                    xs.append(self.__grid_graph.get_vertex_by_id(
                        splited_v_id[0]).get_coordinate()[0])
                    ys.append(self.__grid_graph.get_vertex_by_id(
                        splited_v_id[0]).get_coordinate()[1])
                else:
                    xs.append(self.__grid_graph.get_vertex_by_id(
                        v_id).get_coordinate()[0])
                    ys.append(self.__grid_graph.get_vertex_by_id(
                        v_id).get_coordinate()[1])
            ax.scatter(xs, ys, s=0.1, c='brown', alpha=0.5)

        if plot_mode == '1' or plot_mode == '3':
            ax.scatter(self.__grid_graph.get_xs(),
                       self.__grid_graph.get_ys(), s=0.1, c='k', alpha=0.5)

        if plot_mode == '1':
            xs = list()
            ys = list()
            logging.debug("appending vertex list")
            # TODO double plot issue
            adj_list = self.__grid_graph.get_adj_dict()
            for start_id_ in adj_list:
                if len(adj_list[start_id_]) != 0:
                    start_x = self.__grid_graph.get_vertex_by_id(
                        start_id_).get_coordinate()[0]
                    start_y = self.__grid_graph.get_vertex_by_id(
                        start_id_).get_coordinate()[1]
                    for end_id in adj_list[start_id_]:
                        end_x = self.__grid_graph.get_vertex_by_id(
                            end_id).get_coordinate()[0]
                        end_y = self.__grid_graph.get_vertex_by_id(
                            end_id).get_coordinate()[1]
                        xs.append(start_x)
                        ys.append(start_y)
                        xs.append(end_x)
                        ys.append(end_y)

            logging.debug("making vstack")
            xx = np.vstack([xs[0::2], xs[1::2]])
            yy = np.vstack([ys[0::2], ys[1::2]])

            logging.debug("plot edges")
            ax.plot(xx, yy, linewidth=0.1, c='k')

        xs = list()
        ys = list()
        logging.debug("appending sol path coordinate list")
        if self.path_tmp:
            for idx, start_id_ in enumerate(self.path_tmp):
                if idx == len(self.path_tmp) - 1:
                    break
                if start_id_.count("_") == 1:
                    start_id_ = start_id_.split("_")[0]

                # print(self.__grid_graph.get_adj_dict())
                # print(start_id_)
                start_x = self.__grid_graph.get_vertex_by_id(
                    start_id_).get_coordinate()[0]
                start_y = self.__grid_graph.get_vertex_by_id(
                    start_id_).get_coordinate()[1]

                end_id = self.path_tmp[idx + 1]
                if end_id.count("_") == 1:
                    end_id = end_id.split("_")[0]

                end_x = self.__grid_graph.get_vertex_by_id(
                    end_id).get_coordinate()[0]
                end_y = self.__grid_graph.get_vertex_by_id(
                    end_id).get_coordinate()[1]
                xs.append(start_x)
                ys.append(start_y)
                xs.append(end_x)
                ys.append(end_y)

                ax.scatter(start_x, start_y, c="green", s=0.2)
                ax.scatter(end_x, end_y, c="green", s=0.2)
        #顯示路徑長度：步行點數 * 0.2開根號
        path_points = len(self.path_tmp)
        path_length = round((path_points - 1) * 0.2 ** 0.5, 4)
        if path_length < 0:
            path_length = 0
        # s = 'Points: {points}, Distance: {length}'.format(points=path_points, length=test)
        s = "Points: %.0f"%path_points + ", Distance: %.4f"%path_length
        ax.set_xlabel(s, family='serif', color='r', size=12)

        logging.debug("making vstack")
        xx = np.vstack([xs[0::2], xs[1::2]])
        yy = np.vstack([ys[0::2], ys[1::2]])

        logging.debug("plot edges")

        ax.plot(xx, yy, linewidth=0.4, c='b')

    def get_name(self):
        """取得樓層的名稱。

        Returns:
            樓層的名稱

        """
        return self.__name

    def get_obstacles(self):
        """取得樓層的障礙物列表。

        Returns:
            [source.util.structure.obstacle.Obstacle]: 樓層的障礙物列表

        """
        return copy.deepcopy(self.__obstacles)

    def get_elevation(self):
        """取得樓層的海拔高度。

        Returns:
            float: 樓層的海拔高度

        """
        return self.__elevation

    def get_contour(self):
        """取得建築物輪廓。

        Returns:
            source.util.structure.contour.Contour: 建築物輪廓

        """
        return copy.deepcopy(self.__contour)

    def get_equation(self, by_ref_only=False):
        if by_ref_only:
            return self.__equation_layer
        return copy.deepcopy(self.__equation_layer)

    def get_transportations(self):
        """取得樓層的傳送點列表。

        Returns:
            [source.util.structure.transportation.Transportation]: 樓層的傳送點列表

        """
        return copy.deepcopy(self.__transportations)

    def __to_equation_layer(self):
        """將樓層資訊以方程式描繪。
        """
        if len(self.__obstacles) != 0:
            for obstacle in self.__obstacles:
                for line in obstacle.get_contour().get_lines():
                    self.__equation_layer.append(
                        Linear(line.get_start_point(), line.get_end_point()))
                    # self.__equation_layer[len(self.__equation_layer)-1].display()

        if self.__contour != None:
            for line in self.__contour.get_lines():
                try:
                    self.__equation_layer.append(
                        Linear(line.get_start_point(), line.get_end_point()))
                except ValueError:
                    pass

    def __define_border(self):

        """(改寫)查詢transportation的最大最小xy值"""
        ""
        min_x = min(self.__transportations, key=lambda s: s.get_coordinate()[0]).get_coordinate()[0]-1
        max_x = max(self.__transportations, key=lambda s: s.get_coordinate()[0]).get_coordinate()[0]+1
        min_y = min(self.__transportations, key=lambda s: s.get_coordinate()[1]).get_coordinate()[1]-1
        max_y = max(self.__transportations, key=lambda s: s.get_coordinate()[1]).get_coordinate()[1]+1

        """(改寫)傳送點座標與equation_layer比較xy最大最小值"""
        ""

        if min([_.get_start_point()[0] for _ in self.__equation_layer]) < min_x:
            min_x = min([_.get_start_point()[0] for _ in self.__equation_layer])
        if max([_.get_start_point()[0] for _ in self.__equation_layer]) > max_x:
            max_x = max([_.get_start_point()[0] for _ in self.__equation_layer])
        if min([_.get_start_point()[1] for _ in self.__equation_layer]) < min_y:
            min_y = min([_.get_start_point()[1] for _ in self.__equation_layer])
        if max([_.get_start_point()[1] for _ in self.__equation_layer]) > max_y:
            max_y = max([_.get_start_point()[1] for _ in self.__equation_layer])

        """(改寫)將界線以座標標出。障礙物與傳送點都要比對最大最小xy值, 減少發生"transportation 的值超出邊界"的可能性
        """
        self.__border = {
            "x_min": min_x,
            "x_max": max_x,
            "y_min": min_y,
            "y_max": max_y
            # 原台大寫法
            # "x_min": min([_.get_start_point()[0] for _ in self.__equation_layer]),
            # "x_max": max([_.get_start_point()[0] for _ in self.__equation_layer]),
            # "y_min": min([_.get_start_point()[1] for _ in self.__equation_layer]),
            # "y_max": max([_.get_start_point()[1] for _ in self.__equation_layer])
        }

    def __define_axis(self):
        """定義網格方程式。
        """
        x_coordinate = self.__border["x_min"]
        while x_coordinate <= self.__border["x_max"]:
            self.__vertical_to_xs.append(Axis(Linear(
                (x_coordinate, self.__border["y_min"]), (x_coordinate, self.__border["y_max"]))))
            x_coordinate += self.__density

        y_coordinate = self.__border["y_min"]
        while y_coordinate <= self.__border["y_max"]:
            self.__vertical_to_ys.append(Axis(Linear(
                (self.__border["x_min"], y_coordinate), (self.__border["x_max"], y_coordinate))))
            y_coordinate += self.__density

    def __calculate_obstacle_points(self):
        """計算障礙物的方程式。
        """
        for vertical_to_x in self.__vertical_to_xs:
            for linear in self.__equation_layer:
                vertical_to_x.get_intersections(
                    linear, mode="x", threshold=self.__threshold)
            # vertical_to_x.display()

        for vertical_to_y in self.__vertical_to_ys:
            for linear in self.__equation_layer:
                vertical_to_y.get_intersections(
                    linear, mode="y", threshold=self.__threshold)
            # vertical_to_y.get_equation().display()

    def __generate_grid_graph(self):
        """將各 Vertex 和 transportation 可前進的方向儲存為 adjacency list。
        """
        # TODO: 傳送點border 和從格子點到傳送點的 adjList 修改

        for i, vertical_to_x in enumerate(self.__vertical_to_xs):
            x = float(-vertical_to_x.get_equation().get_coefficients()
                      [2] / vertical_to_x.get_equation().get_coefficients()[0])
            for j, vertical_to_y in enumerate(self.__vertical_to_ys):
                # vertical_to_y.get_equation().display()
                y = float(-vertical_to_y.get_equation().get_coefficients()
                          [2] / vertical_to_y.get_equation().get_coefficients()[1])
                adj_list = list()
                # upper
                if y + self.__density <= self.__border["y_max"]:
                    blocked = False
                    for block in vertical_to_x.get_obstacles():
                        if y <= block and y + self.__density >= block:
                            blocked = True
                            break
                    if not blocked:
                        adj_list.append("{}_{}_{}".format(
                            i, j+1, self.__elevation))

                # lower
                if y - self.__density >= self.__border["y_min"]:
                    blocked = False
                    for block in vertical_to_x.get_obstacles():
                        if y >= block and y - self.__density <= block:
                            blocked = True
                            break
                    if not blocked:
                        adj_list.append("{}_{}_{}".format(
                            i, j-1, self.__elevation))
                # right
                if x + self.__density <= self.__border["x_max"]:
                    blocked = False
                    for block in vertical_to_y.get_obstacles():
                        if x <= block and x + self.__density >= block:
                            blocked = True
                            break
                    if not blocked:
                        adj_list.append("{}_{}_{}".format(
                            i+1, j, self.__elevation))

                # left
                if x - self.__density >= self.__border["x_min"]:
                    blocked = False
                    for block in vertical_to_y.get_obstacles():
                        if x >= block and x - self.__density <= block:
                            blocked = True
                            break
                    if not blocked:
                        adj_list.append("{}_{}_{}".format(
                            i-1, j, self.__elevation))

                v = Vertex(x, y, self.__elevation,
                           "{}_{}_{}".format(i, j, self.__elevation))
                self.__grid_graph.add_vertex(v, adj_list)

                for transportation in self.__transportations:
                    if transportation.get_coordinate()[0] > self.__border['x_max'] or \
                            transportation.get_coordinate()[0] < self.__border['x_min'] or \
                            transportation.get_coordinate()[1] > self.__border['y_max'] or \
                            transportation.get_coordinate()[1] < self.__border['y_min']:
                        logging.warning("transportation 的值超出邊界")
                        raise ValueError("transportation 的值超出邊界")
                    if x <= transportation.get_coordinate()[0] and x + self.__density >= transportation.get_coordinate()[0] and \
                            y <= transportation.get_coordinate()[1] and y + self.__density >= transportation.get_coordinate()[1]:
                        transportation_adj_list = list()
                        for i_ in [i, i+1]:
                            for j_ in [j, j+1]:
                                has_intersection = False  # TODO for demo, add back in real case
                                # for linear in self.__equation_layer:
                                #     if linear.has_intersection_with((transportation.get_coordinate()[0], transportation.get_coordinate()[1]),
                                #                                     (i_*self.__density+self.__border["x_min"], j_*self.__density+self.__border["y_min"])):
                                #         has_intersection = True
                                #         break
                                if has_intersection == False:
                                    transportation_adj_list.append(
                                        "{}_{}_{}".format(i_, j_, self.__elevation))
                                # transportation_adj_list.append("{}_{}_{}".format(i_, j_, self.__elevation)) # TODO delete  in real case
                        v = Vertex(transportation.get_coordinate()[0], transportation.get_coordinate()[1], self.__elevation,
                                   transportation.get_id())
                        self.__grid_graph.add_vertex(
                            v, transportation_adj_list)

        for transportation in self.__transportations:
            grid_list = self.__grid_graph.get_adj_list_by_id(
                transportation.get_id())
            for grid in grid_list:
                self.__grid_graph.add_vertex_to_adj_list_by_id(
                    grid, transportation.get_id())

    def __construct_prevent_zone(self):
        """建構防煙區劃。
        """
        for prevent_zone in self.prevent_zones:  # prevent_zone is a PreventZone object
            self.vertex_prevent_dict[prevent_zone.id] = list()
            boundaries = prevent_zone.boundaries
            xs = [boundaries[0].get_start_point()[0]]
            ys = [boundaries[0].get_start_point()[1]]
            end_x = boundaries[0].get_end_point()[0]
            end_y = boundaries[0].get_end_point()[1]
            for _ in range(len(boundaries)):
                for boundary in boundaries:
                    start = boundary.get_start_point()
                    if end_x == start[0] and end_y == start[1]:
                        xs.append(start[0])
                        ys.append(start[1])
                        end_x = boundary.get_end_point()[0]
                        end_y = boundary.get_end_point()[1]
                        break

            # get prevent zone border
            max_x = max(xs)
            min_x = min(xs)
            max_y = max(ys)
            min_y = min(ys)

            vertex_ids = self.__grid_graph.get_vertex_ids()
            for vertex_id in vertex_ids:
                x, y, __ = self.__grid_graph.get_coordinate_by_vertex_id(
                    vertex_id)
                in_border = x <= max_x and x >= min_x and y <= max_y and y >= min_y
                if in_border:
                    # is in current prevent zone
                    if isPointinPolygon([x, y], list(zip(xs, ys))):
                        is_transportation = False
                        for transportation in self.__transportations:

                            if vertex_id == transportation.get_id():
                                is_transportation = True
                                break
                        if is_transportation:
                            self.vertex_prevent_dict[prevent_zone.id].append(
                                "{}_{}".format(vertex_id, str(self.__elevation)))
                        else:
                            self.vertex_prevent_dict[prevent_zone.id].append(
                                vertex_id)

    def to_grid_graph(self, from_cache):
        """將樓層資訊轉為抽象圖，存入self.__grid_graph。

        Args: 
            from_cache (bool): 是否使用快取

        """
        if not from_cache:
            logging.debug("to equation layer（將樓層資訊以方程式描繪）")
            self.__to_equation_layer()
            logging.debug("define border（將界線以座標標出）")
            self.__define_border()
            logging.debug("define axis（定義網格方程式）")
            self.__define_axis()
            logging.debug("calculate obstacle points（計算障礙物的方程式）")
            self.__calculate_obstacle_points()
            logging.debug(
                "{} generate grid graph（儲存至 adjacency list）".format(self.__name))
            self.__generate_grid_graph()
            logging.debug("{} 建構防煙區劃".format(self.__name))
            self.__construct_prevent_zone()
        else:
            logging.debug("使用快取，因此不計算 grid graph")
        # logging.debug("calculate connected components（計算連通分量）")
        # self.__calculate_connected_components()

    def edit_graph_gui(self, use_cache):
        """開啟編輯視窗，對圖進行人工編輯。

        Args: 
            use_cache (bool): 是否使用快取

        """
        logging.info("開始編輯 Graph")
        # if self.__name == '平均地面高程':
        editor = Editor(self.__contour, self.__grid_graph,
                        self.__transportations, self.__elevation, self.__density)
        isSaveGraph = editor.start_editor(use_cache)
        self.__grid_graph = isSaveGraph[0]
        is_saving = isSaveGraph[1]
        
        return is_saving

        # else:
        #     logging.warning("先 pass 這些層！")

    def get_graph(self):
        """取得抽象圖。
        """
        return self.__grid_graph

    def get_prevent_zone_by_id(self, prevent_zone_id: str) -> PreventZone:
        for prevent_zone in self.prevent_zones:
            if prevent_zone.id == prevent_zone_id:
                return prevent_zone
        return None

    def select_point(self) -> str:
        selector = Selector(self.__contour, self.__grid_graph,
                            self.__transportations, self.__elevation, self.__density)
        end_point_id = selector.select()
        return end_point_id
