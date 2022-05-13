from doctest import OutputChecker
import os
import gc
from pathlib import WindowsPath
import sys
import time
import copy
import logging
import numpy as np
import matplotlib.pyplot as plt

from io import BytesIO
from tkinter import messagebox
from matplotlib.font_manager import FontProperties

from util.structure.graph import Graph
from util.structure.contour import Contour
from util.structure.transportation import Transportation


class Editor:

    def __init__(self, contour: Contour, graph: Graph, transportations: Transportation, elevation, density, ttc_path=None) -> None:
        self.__contour = contour
        self.__transportations = transportations
        self.__grid_graph = graph
        self.__elevation = elevation
        self.__density = density
        self.__start_x, self.__start_y = None, None
        self.__scattered = None
        self.__added_lines = dict()
        if not ttc_path:
            if os.path.exists(os.path.join("util", "DFLiHei-Bd.ttc")):
                self.__font = FontProperties(fname=os.path.join("util", "DFLiHei-Bd.ttc"), size=1)
            else:
                try:
                    self.__font = FontProperties(fname=os.path.join(sys._MEIPASS, "ttc", "DFLiHei-Bd.ttc"), size=1)
                except:
                    self.__font = FontProperties(fname=r"C:/Prj/Python/sinotech-escape/tools/DFLiHei-Bd.ttc",size=1)
        else:
            self.__font = FontProperties(fname=ttc_path)
        self.__press_time = None
        self.history_stack = History()
        self.future_stack = History()

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
        x1 = self.__all_points_x[x1_idx]
        y1 = self.__all_points_y[y1_idx]
        x2 = self.__all_points_x[x2_idx]
        y2 = self.__all_points_y[y2_idx]
        # gui part
        try:
            if self.__added_lines[(x1_idx, y1_idx, x2_idx, y2_idx)] == "init":
                plt.plot([x1, x2], [y1, y2],
                         linewidth=0.2, c='red')
            else:
                self.__added_lines[(x1_idx, y1_idx, x2_idx, y2_idx)].remove()
            del self.__added_lines[(x1_idx, y1_idx, x2_idx, y2_idx)]
        except:
            if self.__added_lines[(x2_idx, y2_idx, x1_idx, y1_idx)] == "init":
                plt.plot([x2, x1], [y2, y1],
                         linewidth=0.5, c='red')
            else:
                self.__added_lines[(x2_idx, y2_idx, x1_idx, y1_idx)].remove()
            del self.__added_lines[(x2_idx, y2_idx, x1_idx, y1_idx)]
        # internal part
        v_id1 = "{}_{}_{}".format(x1_idx, y1_idx, self.__elevation)
        v_id2 = "{}_{}_{}".format(x2_idx, y2_idx, self.__elevation)
        self.__grid_graph.disconnect_vertex_by_id(v_id1, v_id2)

    def __add_line(self, x1_idx, y1_idx, x2_idx, y2_idx, init_=False):
        # preprocess part
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
        # gui part
        if not self.__line_exists(x1_idx, y1_idx, x2_idx, y2_idx):
            # need to check because init_ has lots of directions
            if init_:
                self.__added_lines[(x1_idx, y1_idx, x2_idx, y2_idx)] = "init"
            else:
                line, = plt.plot([x1, x2], [y1, y2], linewidth=0.5, c='green')
                self.__added_lines[(x1_idx, y1_idx, x2_idx, y2_idx)] = line
        # internal part
        if not init_:
            """
            如果是初始畫圖時，就不用去更動 Graph 結構
            """
            v_id1 = "{}_{}_{}".format(x1_idx, y1_idx, self.__elevation)
            v_id2 = "{}_{}_{}".format(x2_idx, y2_idx, self.__elevation)
            self.__grid_graph.connect_vertex_by_id(v_id1, v_id2)

    def __onoperations(self, event):
        self.__press_time = time.time()

    def __onclick(self, event):

        if not self.__press_time:
            logging.debug("Unknown mouse behaviour")
            return
        if time.time() - self.__press_time > 0.25:
            logging.debug("Zoom/Move")
            return

        def __process_lines(x1, y1, x2, y2, opt: Operations):
            if self.__line_exists(x1, y1, x2, y2):
                self.__delete_line(x1, y1, x2, y2)
                opt.add_one(1, x1, y1, x2, y2)
            else:
                self.__add_line(x1, y1, x2, y2)
                opt.add_one(0, x1, y1, x2, y2)

        def __iterate_rectangles(sx, sy, ex, ey):
            lower_left = [min(sx, ex), min(sy, ey)]
            upper_right = [max(sx, ex), max(sy, ey)]
            new_operations = Operations()
            for y_prime in range(lower_left[1], upper_right[1] + 1):
                for x_prime in range(lower_left[0], upper_right[0]):
                    __process_lines(x_prime, y_prime, x_prime +
                                    1, y_prime, new_operations)
            for x_prime in range(lower_left[0], upper_right[0] + 1):
                for y_prime in range(lower_left[1], upper_right[1]):
                    __process_lines(x_prime, y_prime, x_prime,
                                    y_prime + 1, new_operations)
            self.history_stack.push(new_operations)
            self.future_stack = History()

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

    def __onpress(self, event):
        # "shift+ctrl+z"
        # "ctrl+z"
        print(event.key)
        if event.key == "ctrl+z":
            print("Undo")
            last_operations = self.history_stack.pop()
            if last_operations:
                for opt in last_operations.get_all():
                    if opt[0] == 0:
                        self.__delete_line(opt[1], opt[2], opt[3], opt[4])
                    else:
                        self.__add_line(opt[1], opt[2], opt[3], opt[4])
                last_operations.revere()
                self.future_stack.push(last_operations)

            else:
                messagebox.showinfo("", "Already oldest change")
        # elif event.key == "shift+ctrl+z":
        elif event.key == "ctrl+y":
            print("Redo")
            next_operations = self.future_stack.pop()
            if next_operations:
                for opt in next_operations.get_all():
                    if opt[0] == 0:
                        self.__delete_line(opt[1], opt[2], opt[3], opt[4])
                    else:
                        self.__add_line(opt[1], opt[2], opt[3], opt[4])
                next_operations.revere()
                self.history_stack.push(next_operations)

            else:
                messagebox.showinfo("", "Already latest change")
        plt.title("")
        plt.draw()

    # def start_editor(self, use_cache) -> Graph:
    def start_editor(self, use_cache):
        if not use_cache:
            if messagebox.askquestion("Not using cache, run GUI for test only?") != "yes":
                return self.__grid_graph

        backup_grid_graph = copy.deepcopy(self.__grid_graph)

        if sys.platform == "darwin":
            plt.switch_backend('TkAgg')
        elif sys.platform == "win32":
            plt.switch_backend('TkAgg')
        elif sys.platform == "linux":
            plt.switch_backend('agg')

        start_plotting_time = time.perf_counter()

        fig = plt.figure(figsize=(25, 10), dpi=200)
        plt.gca().set_axis_off()
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0,
                            hspace=0, wspace=0)
        plt.margins(0, 0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())

        xmin, ymin = np.inf, np.inf
        xmax, ymax = -np.inf, -np.inf
        for line in self.__contour.get_lines():
            xs, ys = zip(
                *[(line.get_start_point()[0], line.get_start_point()[1]), (line.get_end_point()[0], line.get_end_point()[1])])
            xmin = min(xmin, np.min(xs))
            ymin = min(ymin, np.min(ys))
            xmax = max(xmax, np.max(xs))
            ymax = max(ymax, np.max(ys))
            plt.plot(xs, ys, c="b", linewidth=0.2)

        trans_x = []
        trans_y = []
        for transportation in self.__transportations:
            x, y = transportation.get_coordinate()
            trans_x.append(x)
            trans_y.append(y)
        plt.scatter(trans_x, trans_y, s=3, marker='X', c='r', alpha=0.8)

        self.__all_points_x = self.__grid_graph.get_xs()
        self.__all_points_y = self.__grid_graph.get_ys()

        plt.scatter(self.__all_points_x, self.__all_points_y,
                    s=0.1, c='k', alpha=0.5)

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
                xs.append(x1)
                ys.append(y1)
                xs.append(x2)
                ys.append(y2)

        plt.plot(np.vstack([xs[0::2], xs[1::2]]), np.vstack(
            [ys[0::2], ys[1::2]]), linewidth=0.1, c='k')

        logging.debug("花 {} 秒畫圖～".format(
            time.perf_counter() - start_plotting_time))

        __buf__ = BytesIO()
        plt.savefig(__buf__)
        plt.close()
        gc.collect()

        fig = plt.figure(figsize=(25, 10), dpi=200)
        fig.canvas.mpl_connect('button_press_event', self.__onoperations)
        fig.canvas.mpl_connect('button_release_event', self.__onclick)
        fig.canvas.mpl_connect('key_press_event', self.__onpress)

        __buf__.seek(0)
        plt.imshow(plt.imread(__buf__), extent=[
                   xmin, xmax, ymin, ymax], zorder=0)
        del __buf__
        gc.collect()

        plt.show()

        plt.close("all")
        gc.collect()
        plt.switch_backend('Agg')

        is_saving = (messagebox.askquestion("", "要儲存目前變更嗎？") == "yes")

        logging.info("Saving: {}".format(is_saving))

        return (self.__grid_graph, is_saving) if is_saving else (backup_grid_graph, is_saving)


class Operations:

    def __init__(self) -> None:
        """
        """
        self.__operations = list()

    def add_one(self, type: int, x1, y1, x2, y2) -> None:
        """
        type: add or delete, 0 is add, 1 is delete
        """
        self.__operations.append(list([type, x1, y1, x2, y2]))

    def get_all(self) -> list():
        return self.__operations

    def revere(self) -> None:
        for i in range(len(self.__operations)):
            if self.__operations[i][0] == 0:
                self.__operations[i][0] = 1
            else:
                self.__operations[i][0] = 0


class History:

    def __init__(self) -> None:
        """
        """
        self.history = list()

    def push(self, operations: Operations) -> None:
        self.history.append(operations)

    def pop(self) -> Operations:
        if self.history:
            return self.history.pop(-1)
        return None
