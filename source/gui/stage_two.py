import gc
import sys
import time
import logging
import numpy as np
import matplotlib.pyplot as plt

from io import BytesIO
from typing import List
from tkinter import messagebox
from tkinter import Tk, StringVar, OptionMenu, Button

from util.structure.graph import Graph
from util.structure.contour import Contour
from util.structure.transportation import Transportation


class Selector:

    def __init__(self, contour: Contour, graph: Graph, transportations: Transportation, elevation, density, ttc_path=None) -> None:
        self.__contour = contour
        self.__transportations = transportations
        self.__grid_graph = graph
        self.__elevation = elevation
        self.__density = density
        self.__selected = None
        self.end_point_id = None

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

    def __onclick(self, event):

        if event.xdata and event.ydata:
            try:
                xidx, yidx, x, y = self.__get_idx_and_coordinate_by_location(
                    event.xdata,
                    event.ydata
                )
                if self.__selected:
                    self.__selected.remove()
                    self.__selected = None
                self.__selected = plt.scatter(x, y, s=3.0, c="red")
                plt.title("({}, {})".format(xidx, yidx))
                plt.draw()
                logging.debug(
                    "點擊 idx：({}, {}) = ({}, {})".format(xidx, yidx, x, y)
                )
                self.end_point_id = "{}_{}_{}".format(
                    xidx, yidx, self.__elevation)
            except:
                logging.debug("點擊到 UI 之外")

    def select(self) -> str:

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
        self.__all_points_x = np.arange(np.min(self.__all_points_x), np.max(
            self.__all_points_x) + self.__density + 1, self.__density)
        self.__all_points_y = np.arange(np.min(self.__all_points_y), np.max(
            self.__all_points_y) + self.__density + 1, self.__density)

        logging.debug("花 {} 秒畫圖～".format(
            time.perf_counter() - start_plotting_time))

        __buf__ = BytesIO()
        plt.savefig(__buf__)
        plt.close()
        gc.collect()

        fig = plt.figure(figsize=(25, 10), dpi=200)
        fig.canvas.mpl_connect('button_release_event', self.__onclick)

        __buf__.seek(0)
        plt.imshow(plt.imread(__buf__), extent=[
                   xmin, xmax, ymin, ymax], zorder=0)
        del __buf__
        gc.collect()

        plt.show()

        plt.close("all")
        gc.collect()
        plt.switch_backend('Agg')

        is_saving = (messagebox.askquestion(
            "", "確定選擇 {} 嗎？".format(self.end_point_id)) == "yes")
        logging.info("Saving: {}".format(is_saving))

        return self.end_point_id if is_saving else None


def get_prevent_zone_id(title: str, choices: List[str]) -> str:
    root = Tk()
    root.title(title)
    root.geometry("360x240")

    variable = StringVar(root)
    variable.set(choices[0])

    w = OptionMenu(root, variable, *choices)
    w.pack()

    selection = []

    def onChange():
        selection.append(variable.get())
        w.destroy()
        button.destroy()
        root.quit()

    button = Button(root, text="OK", command=onChange)
    button.pack()

    root.mainloop()
    root.withdraw()

    # delete the confirmation prompt
    # messagebox.showinfo("", "選擇：{}".format(selection[-1]))
    return selection[-1]
