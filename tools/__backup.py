import os
import sys
import time
import numpy as np
import logging
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from matplotlib.font_manager import FontProperties

from util.contour import Contour
from util.graph import Graph
from util.transportation import Transportation


class Editor:

    def __init__(self, contour: Contour, graph: Graph, transportations: Transportation, elevation, density, ttc_path=os.path.join("util", "DFLiHei-Bd.ttc")) -> None:
        self.__contour = contour
        self.__transportations = transportations
        self.__grid_graph = graph
        self.__elevation = elevation
        self.__density = density
        self.__start_x, self.__start_y = None, None
        self.__scattered = None
        self.__added_lines = {}
        self.__font = FontProperties(fname=ttc_path)

    def __get_idx_and_coordinate_by_location(self, x, y):
        xidx = 0
        for idx, (tmp_x1, tmp_x2) in enumerate(zip(self.__all_points_x[:-1], self.__all_points_x[1:])):
            if x == tmp_x2:
                xidx = idx + 1
                break
            if tmp_x1 <= x and x < tmp_x2:
                if x - tmp_x1 < tmp_x2 - x:
                    xidx = idx
                else:
                    xidx = idx + 1
        yidx = 0
        for idx, (tmp_y1, tmp_y2) in enumerate(zip(self.__all_points_y[:-1], self.__all_points_y[1:])):
            if y == tmp_y2:
                yidx = idx + 1
                break
            if tmp_y1 <= y and y < tmp_y2:
                if y - tmp_y1 < tmp_y2 - y:
                    yidx = idx
                else:
                    yidx = idx + 1
        return xidx, yidx, self.__all_points_x[xidx], self.__all_points_y[yidx]

    def __line_exists(self, x1, y1, x2, y2):
        return (x1, y1, x2, y2) in self.__added_lines or (x2, y2, x1, y1) in self.__added_lines

    def __delete_line(self, x1_idx, y1_idx, x2_idx, y2_idx):
        try:
            self.__added_lines[(x1_idx, y1_idx, x2_idx, y2_idx)].remove()
            del self.__added_lines[(x1_idx, y1_idx, x2_idx, y2_idx)]
        except:
            self.__added_lines[(x2_idx, y2_idx, x1_idx, y1_idx)].remove()
            del self.__added_lines[(x2_idx, y2_idx, x1_idx, y1_idx)]
        v_id1 = "{}_{}_{}".format(x1_idx, y1_idx, self.__elevation)
        v_id2 = "{}_{}_{}".format(x2_idx, y2_idx, self.__elevation)
        self.__grid_graph.disconnect_vertex_by_id(v_id1, v_id2)

    def __add_line(self, x1_idx, y1_idx, x2_idx, y2_idx, init_=False):
        if init_:
            x1_idx, y1_idx, x1, y1 = self.__get_idx_and_coordinate_by_location(
                x1_idx, y1_idx)
            x2_idx, y2_idx, x2, y2 = self.__get_idx_and_coordinate_by_location(
                x2_idx, y2_idx)
        else:
            x1 = self.__all_points_x[x1_idx]
            y1 = self.__all_points_y[y1_idx]
            x2 = self.__all_points_x[x2_idx]
            y2 = self.__all_points_y[y2_idx]
        if np.sqrt((x1_idx - x2_idx) ** 2 + (y1_idx - y2_idx) ** 2) > 1:
            return
        if not self.__line_exists(x1_idx, y1_idx, x2_idx, y2_idx):
            # need to check because init_ has lots of directions
            # line, = plt.plot([x1, x2], [y1, y2], linewidth=0.1, c='k')
            self.__fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2], mode="lines", line=dict(color='gray', width=0.5)))
            self.__added_lines[(x1_idx, y1_idx, x2_idx, y2_idx)] = 1  # line
        if not init_:
            """
            如果是初始畫圖時，就不用去更動 Graph 結構
            """
            v_id1 = "{}_{}_{}".format(x1_idx, y1_idx, self.__elevation)
            v_id2 = "{}_{}_{}".format(x2_idx, y2_idx, self.__elevation)
            self.__grid_graph.connect_vertex_by_id(v_id1, v_id2)

    def __onclick(self, event):

        def __process_lines(x1, y1, x2, y2):
            if self.__line_exists(x1, y1, x2, y2):
                self.__delete_line(x1, y1, x2, y2)
            else:
                self.__add_line(x1, y1, x2, y2)

        def __iterate_rectangles(sx, sy, ex, ey):
            lower_left = [min(sx, ex), min(sy, ey)]
            upper_right = [max(sx, ex), max(sy, ey)]
            for y_prime in range(lower_left[1], upper_right[1] + 1):
                for x_prime in range(lower_left[0], upper_right[0]):
                    __process_lines(x_prime, y_prime, x_prime + 1, y_prime)
            for x_prime in range(lower_left[0], upper_right[0] + 1):
                for y_prime in range(lower_left[1], upper_right[1]):
                    __process_lines(x_prime, y_prime, x_prime, y_prime + 1)

        plt.title("")
        if event.xdata and event.ydata:
            try:
                xidx, yidx, x, y = self.__get_idx_and_coordinate_by_location(
                    event.xdata, event.ydata)
                logging.debug(
                    "點擊 idx：({}, {}) = ({}, {})".format(xidx, yidx, x, y))
                if self.__scattered:
                    __iterate_rectangles(
                        self.__start_x, self.__start_y, xidx, yidx)
                    self.__scattered.remove()
                    self.__scattered = None
                    plt.title("結束選擇：({}, {})".format(x, y),
                              fontproperties=self.__font, c="b")
                else:
                    self.__scattered = plt.scatter(x, y, s=5.0, c="red")
                    self.__start_x, self.__start_y = (xidx, yidx)
                    plt.title("開始選擇，起始點：({}, {})".format(
                        x, y), fontproperties=self.__font, c="b")
                plt.draw()
            except:
                logging.debug("點擊到 UI 之外")

    def start_editor(self) -> Graph:

        if sys.platform == "darwin":
            plt.switch_backend('MacOSX')
        elif sys.platform == "win32":
            plt.switch_backend('TkAgg')
        elif sys.platform == "linux":
            plt.switch_backend('agg')

        start_plotting_time = time.perf_counter()

        self.__fig = go.Figure()
        self.__fig.update_layout(showlegend=False, plot_bgcolor="#fff")

        for line in self.__contour.get_lines():
            xs, ys = zip(
                *[(line.get_start_point()[0], line.get_start_point()[1]), (line.get_end_point()[0], line.get_end_point()[1])])
            self.__fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines",
                                            line=dict(color='royalblue', width=1)))

        trans_x = []
        trans_y = []
        for transportation in self.__transportations:
            x, y = transportation.get_coordinate()
            trans_x.append(x)
            trans_y.append(y)
        # plt.scatter(trans_x, trans_y, s=3, marker='X', c='r', alpha=0.8)
        self.__fig.add_trace(go.Scatter(x=trans_x, y=trans_y, name="Transportations",
                             mode="markers", marker=dict(color="royalblue", size=2)))

        self.__all_points_x = self.__grid_graph.get_xs()
        self.__all_points_y = self.__grid_graph.get_ys()

        def handle_click(trace, points, state):
            c = list(scatter.marker.color)
            s = list(scatter.marker.size)
            for i in points.point_inds:
                c[i] = '#bae2be'
                s[i] = 20
                scatter.marker.color = c
                scatter.marker.size = s

        self.__fig.add_trace(go.Scatter(x=self.__all_points_x,
                                        y=self.__all_points_y, mode="markers"))

        scatter = self.__fig.data[-1]
        scatter.marker.color = ["#a3a7e4"]
        scatter.marker.size = [10] * len(self.__all_points_x)

        scatter.on_click(handle_click)

        print(self.__fig)

        self.__all_points_x = np.arange(np.min(self.__all_points_x), np.max(
            self.__all_points_x) + self.__density + 1, self.__density)
        self.__all_points_y = np.arange(np.min(self.__all_points_y), np.max(
            self.__all_points_y) + self.__density + 1, self.__density)

        adj_list = self.__grid_graph.get_adj_dict()
        xs = list()
        ys = list()

        for start_id in adj_list:
            for end_id in adj_list[start_id]:

                x1, y1, _ = self.__grid_graph.get_vertex_by_id(
                    start_id).get_coordinate()
                x2, y2, _ = self.__grid_graph.get_vertex_by_id(
                    end_id).get_coordinate()

                if not x1 or not y1 or not x2 or not y2:
                    continue

                self.__add_line(x1, y1, x2, y2, init_=True)

        self.__fig.show()

        logging.debug("花 {} 秒畫圖～".format(
            time.perf_counter() - start_plotting_time))

        # plt.show()

        # plt.close("all")
        plt.switch_backend('Agg')

        exit()

        return self.__grid_graph
