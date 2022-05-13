import os
import math
import pickle
import hashlib
import logging
from posixpath import basename
import threading
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk

from rich import print
from typing import List
from bs4 import BeautifulSoup
from tkinter import messagebox
from tkinter import filedialog
from datetime import datetime

from floor import Floor
from util.structure.graph import Graph
from util.structure.contour import Contour
from util.structure.line import Line
from util.structure.vertex import Vertex
from util.solution import Solution
from util.structure.transportation import Transportation
from util.structure.preventzone import PreventZone
from util.dijkstra import Dijkstra
from gui.stage_two import get_prevent_zone_id


class Building:
    """建築物本體。

    Args:
        meta_infos_path (str): 建物元資訊相對路徑
        density (float)
        use_cache (bool): 是否使用快取
        cache_dir (str): 快取檔案路徑
        output_dir (str): 結果輸出檔案路徑

    Raises:
        Exception: if floor.json 格式錯誤!

    Attributes:
        __floors ([source.floor.Floor]): 存放建物中每一樓層資訊的陣列
        __density (float): 抽象圖中點跟點的距離（公尺）
        __use_cache (bool): 是否使用快取
        __cache_dir (str): 快取存放資料夾
        __output_dir (str): 輸出路徑資料夾


        __from_cache (bool): floor 是否從快取讀
        __total_graph (Graph): 存放抽象圖
        solutions (Solution): 最終處理結果
        path_counter (int): 有多少路徑
        __xml_md5 (str): xml 檔案的 md5 hash
        prjNS, prjWE, angle (float): xml 位置資訊

    """

    def __init__(self, density, use_cache, cache_dir, output_dir):
        """Building 建構子。

        Args:
            meta_infos_path (str): 建物元資訊相對路徑

        Raises:
            Exception: if floor.json 格式錯誤!

        """
        self.__density = density
        self.__use_cache = use_cache
        self.__cache_dir = cache_dir
        self.__output_dir = output_dir
        self.__from_cache = False
        self.__total_graph = Graph()
        self.solutions = dict()
        self.path_counter = 0

        self.upper_bounds = list()
        self.algo_res = list()
        self.lower_bounds = list()

    def __rotate(self, origin, point, angle, z):
        """
        Rotate a point counterclockwise by a given angle around a given origin.
        The angle should be given in radians.

        """

        angle = -angle * math.pi / 180.0

        ox, oy = origin
        px, py = point

        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)

        return np.array([qx, qy, z])

    def __id_join(self, id1, id2):
        """Join two element id into one with "_" separated.

        Args:
            id1 (str): 要串接的第一個id
            id2 (str): 要串接的第二個id

        """
        return "{}_{}".format(id1, id2)

    def __get_cache_path(self, floor_name):
        """取得樓層快取儲存路徑。

        Args:
            floor_name (str): 欲取得快取的樓層名稱

        Returns:
            str: 該樓層快取儲存路徑。

        """
        return os.path.join(
            self.__cache_dir,
            "{}_{}.pickle".format(
                hashlib.md5(floor_name.encode('utf-8')).hexdigest(),
                self.__xml_md5
            )
        )

    def load_infos(self, contours_path, msgBox):
        """建物資訊讀取介面。

        Args:
            contours (bool): 是否讀取建物輪廓
            obstacles (bool): 是否由json讀取障礙物
            transportations (bool): 是否由json讀取障礙物
            contours_path (str): 建物輪廓相對路徑
            obstacles_path (str): 障礙物相對路徑
            transportations_path (str): 傳送點資訊相對路徑

        """

        self.__xml_md5 = "{}_{}".format(
            hashlib.md5(open(contours_path, 'rb').read()).hexdigest(),
            self.__density
        )

        if self.__use_cache:
            for file_name in os.listdir(self.__cache_dir):
                if self.__xml_md5 in file_name:
                    """
                    如果 xml 檔案沒被改過（md5 一樣），就直接 load pickle
                    """
                    logging.info("使用處理過的 xml 檔案，直接讀快取 ...")
                    self.__from_cache = True
                    floor_cache_paths = list([
                        x for x in os.listdir(self.__cache_dir) if self.__xml_md5 in x
                    ])
                    self.__floors = list()
                    for cache_path in floor_cache_paths:
                        try:
                            with open(os.path.join(self.__cache_dir, cache_path), "rb") as f:
                                self.__floors.append(pickle.load(f))
                        except:
                            logging.info("cache資料損毀")
                    # 依高程排序
                    self.__floors = sorted(self.__floors, key= lambda s: s.get_elevation())
                    return

        threads = list()
        threads.append(threading.Thread(
            target=self.__load_contours,
            args=(contours_path, msgBox)
        ))
        threads[-1].start()

        for thread in threads:
            thread.join()

        logging.info('Done loading!')

    def __load_contours(self, contours_path, msgBox):
        """解析xml檔案中的輪廓，並將資訊存入在self.__floors中對應的樓層物件中。

        Args:
            contours_path (str): 建物輪廓相對路徑

        """
        with open(contours_path, "rb") as f:
            logging.info("讀取 gbXML 檔案 ...")
            buf = f.read()
            logging.info("建立搜索樹 ...")
            soup = BeautifulSoup(buf, 'xml')

        base_points = soup.find("BasePoint")
        self.prjNS = float(base_points.find("prjNS").text)
        self.prjWE = float(base_points.find("prjWE").text)
        self.angle = float(base_points.find("angle").text)

        accept_layers = ["ExteriorWall", "InteriorWall", "Shade",
                         "UndergroundWall", "UndergroundSlab"]

        sent_points = soup.find("SentPoint").find_all("Element")
        # 修改內容, 把樓梯都更換為電扶梯
        if msgBox == 'yes':
            for sent_point in sent_points:
                if sent_point.attrs['Category'] == '樓梯':
                    sent_point.attrs['Category'] = '電扶梯'
            
        # We need stable-unique so this magic operation is neccessary
        floor_names = np.array([point.get("Level") for point in sent_points])
        floor_names = floor_names[sorted(
            np.unique(floor_names, return_index=True)[1]
        )]
        elevations_accuracy = 4
        floor_elevations = np.array([
            np.round(
                float(point.find_all("Coordinate")[2].text),
                elevations_accuracy + 1
            )
            for point in sent_points
        ])
        floor_elevations = floor_elevations[sorted(
            np.unique(floor_elevations, return_index=True)[1]
        )]

        self.__floors = list()
        for name, elevation in zip(
            floor_names,
            floor_elevations
        ):
            self.__floors.append(
                Floor(
                    name=str(name),
                    elevation=float(elevation),
                    density=self.__density
                )
            )

        for floor in self.__floors:

            logging.info("正在新增 {}".format(floor.get_name()))
            lines = list()
            for sf in soup.find_all("Surface"):
                type_ = sf.get("surfaceType")
                if type_ in accept_layers:

                    vertex = sf.find("PolyLoop").find_all("CartesianPoint")
                    flag = False
                    start_point = list()

                    vertex_parsed = list()
                    for p in vertex:
                        _tmp = p.find_all("Coordinate")
                        vertex_parsed.append(
                            [float(_tmp[i].text) for i in range(3)])
                    vertex_parsed = np.vstack(
                        (vertex_parsed, vertex_parsed[0]))

                    for p1, p2 in zip(vertex_parsed[:-1], vertex_parsed[1:]):

                        p1 = self.__rotate(
                            origin=[self.prjNS, self.prjWE], point=[p1[0], p1[1]], angle=self.angle, z=p1[2])
                        p2 = self.__rotate(
                            origin=[self.prjNS, self.prjWE], point=[p2[0], p2[1]], angle=self.angle, z=p2[2])

                        p, t = p1, (np.array(p2) - np.array(p1))

                        for add_height in range(1, 20, 1):
                            # TODO: 端點在切割平面上
                            z0 = floor.get_elevation() + add_height / 10.0
                            if (p1[2] > z0 and p2[2] < z0) or (p1[2] < z0 and p2[2] > z0):
                                t_value = ((z0 - p[2]) / t[2]) if t[2] else 0
                                if not flag:
                                    flag = True
                                    start_point = (p1 + t_value * t)
                                else:
                                    flag = False
                                    end_point = (p1 + t_value * t)
                                    lines.append(
                                        Line((start_point[0], start_point[1]),
                                             (end_point[0], end_point[1])))
                            elif p[2] == z0 and t[2] == 0:
                                lines.append(
                                    Line((p1[0], p1[1]),
                                         (p2[0], p2[1])))

            floor.add_contour(Contour(lines))

            logging.info("讀取傳送點檔案 ...")

            send_points = soup.find("SentPoint").find_all("Element")

            for send_point in send_points:
                if floor.get_name() == send_point["Level"]:
                    coordinate = send_point.find_all("Coordinate")
                    p1 = [float(coordinate[0].text), float(
                        coordinate[1].text), float(coordinate[2].text)]
                    p1 = self.__rotate(
                        origin=[self.prjNS, self.prjWE], point=[p1[0], p1[1]], angle=self.angle, z=p1[2])
                    floor.add_transportation(Transportation(
                        send_point["Name"], str(
                            send_point["Id"]), send_point["Category"],
                        (float(p1[0]), float(p1[1])), send_point["IsEnd"]))
                    # print(send_point["Id"], send_point["IsEnd"])

            logging.info("讀取防煙區劃 ...")
            prevent_zones = soup.find("PreventZones").find_all("Area")
            for prevent_zone in prevent_zones:
                if floor.get_name() == prevent_zone["Level"]:
                    pz = PreventZone(prevent_zone["Id"], prevent_zone["Name"])
                    prevent_zone_curves = prevent_zone.find(
                        "PolyLoop").find_all("Curve")
                    for prevent_zone_curve in prevent_zone_curves:
                        start_coordinate = prevent_zone_curve.find_all(
                            "StartCoordinate")
                        end_coordinate = prevent_zone_curve.find_all(
                            "EndCoordinate")

                        p1 = [float(start_coordinate[0].text), float(
                            start_coordinate[1].text), float(start_coordinate[2].text)]
                        p2 = [float(end_coordinate[0].text), float(
                            end_coordinate[1].text), float(start_coordinate[2].text)]

                        p1 = self.__rotate(
                            origin=[self.prjNS, self.prjWE], point=[
                                p1[0], p1[1]], angle=self.angle, z=p1[2]
                        )
                        p2 = self.__rotate(
                            origin=[self.prjNS, self.prjWE], point=[
                                p2[0], p2[1]], angle=self.angle, z=p2[2]
                        )
                        pz.add_line(Line((p1[0], p1[1]), (p2[0], p2[1])))

                    floor.prevent_zones.append(pz)
            logging.info("完成新增 {}".format(floor.get_name()))

        logging.info("讀取並轉換成功！")

    def to_grid_graph(self):
        """合成各樓層轉換成的抽象圖，存入self.__grid_graph。
        """
        threads = list()
        floor_names = list()
        for floor in self.__floors:
            threads.append(threading.Thread(
                target=floor.to_grid_graph, args=(self.__from_cache,)))
            threads[-1].start()
            floor_names.append(floor.get_name())

        for thread, f in zip(threads, floor_names):
            thread.join()
            logging.debug("完成樓層：{}".format(f))
        if self.__use_cache:
            for floor in self.__floors:
                with open(self.__get_cache_path(floor.get_name()), "wb") as f:
                    pickle.dump(floor, f)
        logging.info("成功將資訊轉換成 Graph！")

    def edit_graph_gui(self):
        """開啟編輯視窗，對圖進行人工編輯。
        """
        floor_idx_dict = dict({
            floor.get_name(): i
            for i, floor in enumerate(self.__floors)
        })
        selected_floor_idx = floor_idx_dict[
            get_prevent_zone_id(
                "Select floor to edit",
                list(floor_idx_dict.keys())
            )
        ]

        is_saving = self.__floors[selected_floor_idx].edit_graph_gui(self.__use_cache)        

        if is_saving:
            root = tk.Tk()
            root.withdraw()
            self.__cache_dir = filedialog.askdirectory(parent=root)            

        if self.__use_cache:
            with open(self.__get_cache_path(self.__floors[selected_floor_idx].get_name()), "wb") as f:
                pickle.dump(self.__floors[selected_floor_idx], f)

    def connect_floors(self):
        """將各樓層抽象圖串接。
        """
        logging.info("將各樓層抽象圖串接")
        transportation_dict = dict()

        for floor in self.__floors:

            f_graph = floor.get_graph()
            f_graph_adj_dict = f_graph.get_adj_dict()
            transportations_ids = [trans.get_id()
                                   for trans in floor.get_transportations()]

            for vertex_id in f_graph_adj_dict:
                if vertex_id not in transportations_ids:  # 該點不為傳送點.
                    vertex_obj = f_graph.get_vertex_by_id(vertex_id)
                    self.__total_graph.add_vertex(
                        vertex_obj, f_graph_adj_dict[vertex_id])

            for vertex_id in f_graph_adj_dict:
                if vertex_id in transportations_ids:  # 該點為傳送點
                    vertex_obj = f_graph.get_vertex_by_id(vertex_id)
                    self.__total_graph.add_vertex(Vertex(vertex_obj.get_coordinate()[0], vertex_obj.get_coordinate()[
                                                  1], floor.get_elevation(), self.__id_join(vertex_id, floor.get_elevation())), f_graph_adj_dict[vertex_id])

                    # 修改原先graph的adj list
                    for neighbor_id in f_graph_adj_dict[vertex_id]:
                        self.__total_graph.set_adj_list_by_id(
                            neighbor_id, vertex_id, self.__id_join(vertex_id, floor.get_elevation()))

                    if vertex_id not in transportation_dict.keys():  # 未出現過
                        transportation_dict[vertex_id] = (self.__id_join(
                            vertex_id, floor.get_elevation()), floor.get_elevation())
                    else:  # 出現過
                        # 先假設平面移動速度是1，垂直移動速度是0.25，則density=0.4的時候，垂直距離為1時，要放1 / 0.4 / 0.25個點
                        logging.debug("連接傳送點 {}".format(vertex_id))
                        elevation_gap = abs(floor.get_elevation(
                        ) - transportation_dict[vertex_id][1])  # 新減舊
                        vertical_moving_speed = 1 # 修改垂直距離佈點
                        parallel_moving_speed = 1
                        # 模擬垂直距離佈點數
                        append_num = np.ceil(elevation_gap / self.__density / (
                            vertical_moving_speed / parallel_moving_speed)).astype(int)  # ceiling
                        # # 連結佈點只留起終點, 盡量減低垂直距離計算
                        # append_num = 2
                        for cnt in range(append_num):
                            if cnt == 0:  # 頭
                                self.__total_graph.add_vertex(Vertex(vertex_obj.get_coordinate()[0], vertex_obj.get_coordinate()[1], floor.get_elevation(
                                ), self.__id_join(vertex_id, cnt)), [self.__id_join(vertex_id, floor.get_elevation()), self.__id_join(vertex_id, cnt + 1)])
                                self.__total_graph.add_vertex_to_adj_list_by_id(self.__id_join(
                                    vertex_id, floor.get_elevation()), self.__id_join(vertex_id, cnt))
                            elif cnt == append_num - 1:
                                self.__total_graph.add_vertex(Vertex(vertex_obj.get_coordinate()[0], vertex_obj.get_coordinate()[1], floor.get_elevation(
                                ), self.__id_join(vertex_id, cnt)), [self.__id_join(vertex_id, cnt - 1), transportation_dict[vertex_id][0]])
                                self.__total_graph.add_vertex_to_adj_list_by_id(
                                    transportation_dict[vertex_id][0], self.__id_join(vertex_id, cnt))
                            else:
                                self.__total_graph.add_vertex(Vertex(vertex_obj.get_coordinate()[0], vertex_obj.get_coordinate()[1], floor.get_elevation(
                                ), self.__id_join(vertex_id, cnt)), [self.__id_join(vertex_id, cnt - 1), self.__id_join(vertex_id, cnt + 1)])

        logging.info("各樓層抽象圖串接完成")

    def __generate_solution(self, dijkstra_obj, failed_transportation_id, failed_block_id, failed_vertex, situation, transportation_id="", floor_elavation=""):
        """
        Args:
            dijkstra_obj(Dijkstra)
            failed_transportation_id(str): 維護中傳送點 id
            failed_block_id(str): 失效防煙區劃 id
            failed_vertex(list of str): 失效的所有點 id
            situation(int): 情況
            transportation_id(str)
            floor_elavation(str)

        """
        current_solution = Solution(failed_transportation_id, failed_block_id)
        if situation == 1:
            self.__total_graph.generate_instance(
                failed_vertex_id="",
                failed_block=failed_vertex
            )
        if situation == 2:
            self.__total_graph.generate_instance(
                failed_vertex_id=failed_transportation_id,
                failed_block=failed_vertex
            )

        self.__path_analysis(dijkstra_obj, current_solution)
        # set distance to inf if start points not in failed prevent zone
        if situation == 1:
            for end_point_id in current_solution.shortest_paths:
                distance_dict = current_solution.shortest_paths[end_point_id][1]
                for start_point_id in distance_dict:
                    if self.which_preventzone(start_point_id) != failed_block_id:
                        current_solution.shortest_paths[end_point_id][1][start_point_id] = np.inf

        if situation == 1 or situation == 2:
            self.__total_graph.restore_instance()

        if situation == 0:
            instance_str = "none"
        elif situation == 1:
            instance_str = self.__id_join(
                "in" + failed_block_id, self.__id_join(transportation_id, floor_elavation))
        elif situation == 2:
            instance_str = self.__id_join(
                failed_block_id, failed_transportation_id)
        self.solutions[instance_str] = current_solution

    def __calculate_connected_components(self, graph, dfs_start_point_id):
        """計算連通分量。

        Args:
            graph (Graph): 預計算連通分量之抽象圖
            dfs_start_point_id (str): dfs起點

        """

        return graph.calculate_connected_components(dfs_start_point_id)

    def instances_analysis(self):
        """防煙區劃與傳送點失效情境分析。
        start point in prevent zone: 防煙區劃的路徑維持，只有傳送點失效。 (instance_str = "preventZoneId_transportationId")

        """

        floor_cache_md5 = list()
        for floor in self.__floors:
            floor_cache_md5.append("{}".format(
                hashlib.md5(
                    open(self.__get_cache_path(floor.get_name()), 'rb').read()
                ).hexdigest()
            ))

        sol_cache_path = os.path.join(
            self.__cache_dir,
            "{}.pickle".format("_".join(floor_cache_md5))
        )
        logging.info("Cache path: {}".format(sol_cache_path))

        if os.path.exists(sol_cache_path):
            logging.info("Solution cache exists, using cache")
            with open(sol_cache_path, 'rb') as f:
                self.solutions = pickle.load(f)
                logging.debug("Done reading cache")

        else:
            all_vertex_ids = list()
            for vertex_id in self.__total_graph.get_vertex_ids():
                all_vertex_ids.append(vertex_id)
            dijkstra = Dijkstra(all_vertex_ids)

            failed_block = None
            failed_vertex_id = None
            logging.info(
                "開始計算案例--失火區域：{}，維護中傳送點{}".format(failed_block, failed_vertex_id))
            self.__generate_solution(
                dijkstra, failed_vertex_id, failed_block, list(), 0)
            logging.info(
                "案例--失火區域：{}，維護中傳送點{} 計算完成".format(failed_block, failed_vertex_id))

            for floor in self.__floors:
                transportation_ids = [self.__id_join(trans.get_id(), str(floor.get_elevation()))
                                      for trans in floor.get_transportations()]
                for prevent_zone_id in floor.vertex_prevent_dict:
                    calculated_transportation = list()
                    for floor_ in self.__floors:
                        for transportation in floor_.get_transportations():

                            failed_vertex_ids = list()
                            # 會進行維護的傳送點
                            calculated = (transportation.get_id()
                                          in calculated_transportation)
                            if (transportation.is_end_point() or transportation.always_valid()) or calculated:
                                continue
                            calculated_transportation.append(
                                transportation.get_id())
                            failed_vertex_ids.append(
                                self.__id_join(transportation.get_id(), str(floor_.get_elevation())))  # 維護中傳送點
                            failed_block = floor.vertex_prevent_dict[prevent_zone_id]
                            for vertex_id in failed_block:
                                # 因為在失效防煙區劃而失效的傳送點
                                if vertex_id in transportation_ids and (not vertex_id in failed_vertex_ids):
                                    failed_vertex_ids.append(vertex_id)
                            logging.info(
                                "開始計算案例--失火區域：{}，失效傳送點{}".format(prevent_zone_id, failed_vertex_ids))
                            failed_transportation_ids = ",".join(
                                failed_vertex_ids)
                            self.__generate_solution(
                                dijkstra, failed_transportation_ids, prevent_zone_id, failed_vertex_ids, 1, transportation.get_id(), str(floor_.get_elevation()))

            for floor in self.__floors:
                for prevent_zone_id in floor.vertex_prevent_dict:
                    calculated_transportation = list()
                    failed_block = floor.vertex_prevent_dict[prevent_zone_id]
                    for floor_ in self.__floors:
                        for transportation in floor_.get_transportations():

                            if transportation.is_end_point() or transportation.always_valid():
                                continue
                            if not transportation.get_id() in calculated_transportation:

                                calculated_transportation.append(
                                    transportation.get_id())
                                failed_vertex_id = self.__id_join(
                                    transportation.get_id(), floor_.get_elevation())

                                logging.info(
                                    "開始計算案例--失火區域：{}，維護中傳送點{}".format(prevent_zone_id, failed_vertex_id))
                                self.__generate_solution(
                                    dijkstra, failed_vertex_id, prevent_zone_id, failed_block, 2)
                                logging.info(
                                    "案例--失火區域：{}，維護中傳送點{} 計算完成".format(prevent_zone_id, failed_vertex_id))

            logging.info("共分析了 {} 條路徑".format(self.path_counter))

            with open(sol_cache_path, 'wb') as handle:
                pickle.dump(self.solutions, handle,
                            protocol=pickle.HIGHEST_PROTOCOL)

    def __path_analysis(self, dijkstra, sol_obj):
        """最短路徑分析。

        Args:
            instance_graph (Graph): 該情境的抽象圖
            sol_obj (Solution): 解答儲存物件

        """
        for floor in self.__floors:
            transportations = floor.get_transportations()
            for transportation in transportations:
                if transportation.is_end_point():
                    end_point_id = self.__id_join(
                        transportation.get_id(), floor.get_elevation())

                    # ~= 0.07s
                    try:
                        connected_component_ids = self.__calculate_connected_components(
                            self.__total_graph, dfs_start_point_id=end_point_id)
                    except:
                        logging.error("Final Graph 內容有誤，請開啟gui mode重新編輯檢查。")
                        raise Exception

                    logging.info("以終點 {} 為源點運行 dijkstra 演算法".format(
                        transportation.get_id()))

                    # run 0.2s
                    try:
                        distance, parent = dijkstra.run(
                            connected_component_ids, self.__total_graph.get_adj_dict(gen_new=False), end_point_id)
                    except Exception as e:
                        print(repr(e))
                        logging.error("Final Graph 內容有誤，請開啟gui mode重新編輯檢查。")
                        raise Exception

                    sol_obj.shortest_paths[self.__id_join(
                        transportation.get_id(), floor.get_elevation())] = (parent, distance)
                    self.path_counter += len(connected_component_ids)

    def plot_sol(self, plot_mode, vertex_id, instance_str="none"):
        """繪圖介面。

        Args:
            plot_mode (str): 有點有線請為'1'，沒點沒線為'2'，有點沒線為'3'
            vertex_id (str): 起點id
            instance_str (str): 情境描述字串，格式為{失效防煙區劃id}_{失效傳送點_id}

        """
        failed_endpoint_ids = list()
        if not instance_str in self.solutions:
            raise ValueError("invalid instance string!")
        # 找到self.floors的最小值當起點(ex.'_99.45')
        lowest_floor = min(self.__floors, key=lambda x: x.get_elevation())
        for floor in self.__floors:
            transportations = floor.get_transportations()
            for transportation in transportations:
                if transportation.is_end_point():
                    try:
                        # get path
                        end_point_id = self.__id_join(
                            transportation.get_id(), floor.get_elevation())
                        dijk_parent_dict = self.solutions[instance_str].shortest_paths[end_point_id][0]
                        # dijk_distance = self.solutions[instance_str].shortest_paths[end_point_id][1][vertex_id]

                        # 查詢同一情境, 不同出口的最遠起點
                        findTheStart = self.solutions[instance_str].shortest_paths[end_point_id][1]
                        starts = dict()
                        for start in findTheStart:
                            if '_' + str(lowest_floor.get_elevation()) in start:
                                starts[start] = findTheStart[start]
                        vertex_id = max(starts, key=starts.get)
                        vertex_ids = sorted(starts, key=starts.get) # 依所有路徑長度排序

                        sameDistances = dict()
                        for sameDistance in starts:
                            if findTheStart[vertex_id] == starts[sameDistance]:
                                sameDistances[sameDistance] = starts[sameDistance]

                        if not vertex_id in dijk_parent_dict:
                            raise ValueError("Invalid start point.")

                        path_ = [vertex_id]
                        while path_[-1] != end_point_id:
                            path_.append(dijk_parent_dict[path_[-1]])

                        for f in self.__floors:
                            f.path_tmp = [v_id for v_id in path_ if str(
                                f.get_elevation()) in v_id]

                        # plot start
                        self.__plot_all_floor(
                            instance_str, end_point_id, plot_mode)
                    except:
                        logging.info("不存在起點{}到終點{}的路徑".format(
                            vertex_id, end_point_id))
                        failed_endpoint_ids.append(end_point_id)
                        # return False
        return failed_endpoint_ids

    def calculate_reverse_table(self):
        """計算反向查找表。

        sol_table_dict -> instance -> startpoint -> endpoint -> distancevalue

        """

        logging.info("正在轉換最險峻路徑表格")
        self.sol_table_dict = dict()

        all_vertex_ids = list(self.solutions["none"].shortest_paths.values())[
            0][0].keys()
        end_point_ids = list(self.solutions["none"].shortest_paths.keys())

        # "none" case
        try:
            self.sol_table_dict[("none", "none")] = dict()
            for start_point_id in all_vertex_ids:
                self.sol_table_dict[("none", "none")][start_point_id] = dict()
                for end_point_id in end_point_ids:
                    self.sol_table_dict[
                        ("none", "none")
                    ][start_point_id][end_point_id] = \
                        self.solutions["none"].shortest_paths[end_point_id][1][start_point_id]
        except KeyError:
            logging.error("建物抽象圖編輯錯誤！")
            messagebox.showerror("", "建物抽象圖編輯錯誤，請檢查是否合法有逃生路徑失效。")

        # 找到self.floors的最小值當起點(ex.'_99.45')
        min_elev = self.__floors[0].get_elevation()
        for f in self.__floors:
            if f.get_elevation() < min_elev:
                min_elev = f.get_elevation()
        
        lowest_floor = min(self.__floors, key=lambda x: x.get_elevation())
        min_elev = lowest_floor.get_elevation()
        
        # initialization and start point not in failed prevent zone cases
        for instance_str in self.solutions:
            if "in" in instance_str or instance_str == "none":
                continue

            instance_info = instance_str.split("_")
            failed_preventzone_id = instance_info[0]
            failed_transportation_id = "{}_{}".format(
                instance_info[1], instance_info[2])

            self.sol_table_dict[(failed_preventzone_id,
                                 failed_transportation_id)] = dict()

            # init.
            for start_point_id in all_vertex_ids:
                if str(min_elev) in start_point_id:
                    if start_point_id == failed_transportation_id:
                        continue
                    self.sol_table_dict[(
                        failed_preventzone_id, failed_transportation_id)][start_point_id] = dict()
                    for end_point_id in end_point_ids:
                        if start_point_id in self.solutions[instance_str].shortest_paths[end_point_id][1]:
                            self.sol_table_dict[(failed_preventzone_id, failed_transportation_id)
                                                ][start_point_id][end_point_id] = self.solutions[instance_str].shortest_paths[end_point_id][1][start_point_id]
                        else:
                            self.sol_table_dict[(
                                failed_preventzone_id, failed_transportation_id)][start_point_id][end_point_id] = np.inf

        # update distance of start point which is in failed zone
        for instance_str in self.solutions:
            if "in" in instance_str:  # "in" prefix
                instance_info = instance_str.replace("in", "").split("_")
                failed_preventzone_id = instance_info[0]
                failed_transportation_id = "{}_{}".format(
                    instance_info[1], instance_info[2])

                for end_point_id in end_point_ids:
                    for start_point_id in self.solutions[instance_str].shortest_paths[end_point_id][1]:
                        if start_point_id == failed_transportation_id:
                            continue
                        # vertex in failed prevent zone
                        try:
                            if self.solutions[instance_str].shortest_paths[end_point_id][1][start_point_id] != np.inf:
                                self.sol_table_dict[(failed_preventzone_id, failed_transportation_id)
                                                    ][start_point_id][end_point_id] = self.solutions[instance_str].shortest_paths[end_point_id][1][start_point_id]
                        except:
                            error = 'error'

    def dump_sol_table(self):
        """整理 Solution 結果，輸出 csv。
        """
        logging.info("正在輸出最險峻路徑表格")

        sol_table = pd.DataFrame(
            columns=["instance_str", "起點", "失效防煙區劃", "失效傳送點", "最險峻路徑長度", "起點位於防煙區劃", "終點", "終點編號", "路徑經過防煙區劃", "無法逃生座標點列表"])
        for preventzone_id, transportation_id in self.sol_table_dict:  # for each instance
            new_row = dict()

            # 失效防煙區劃 and 失效傳送點
            new_row["失效防煙區劃"] = self.get_preventzone_name_by_id(preventzone_id)
            new_row["失效傳送點"] = self.get_transportation_name_by_id(
                transportation_id.split("_")[0])

            # 最險峻路徑長度(跑得到終點的最遠長度) and 起點 and 無法逃生座標點列表
            start_to_end_point = dict()  # key: start_point_id, value:(endpointid, distance)
            dead_point_ids = list()
            # sol_table_dict -> instance -> startpoint -> endpoint
            untraversed_start_point_ids = list(
                self.sol_table_dict[(preventzone_id, transportation_id)].keys())
            while len(untraversed_start_point_ids) != 0:
                # 最低樓層(ex.'_99.45')
                current_start_id = untraversed_start_point_ids[0]
                nearest_end_point_id = min(self.sol_table_dict[(preventzone_id, transportation_id)][current_start_id], key=self.sol_table_dict[(
                    preventzone_id, transportation_id)][current_start_id].get)
                nearest_distance = self.sol_table_dict[(
                    preventzone_id, transportation_id)][current_start_id][nearest_end_point_id]
                if nearest_distance != np.inf:  # way to live
                    start_to_end_point[current_start_id] = (
                        nearest_end_point_id, nearest_distance)
                else:  # dead point
                    dead_point_ids.append(current_start_id)
                untraversed_start_point_ids.remove(current_start_id)
            try:
                most_dangerous_start_point_id = max(
                    start_to_end_point, key=lambda start_point: start_to_end_point[start_point][1])
                new_row["最險峻路徑長度"] = start_to_end_point[most_dangerous_start_point_id][1] * self.__density
                new_row["起點"] = most_dangerous_start_point_id
                new_row["無法逃生座標點列表"] = dead_point_ids

                # 起點位於防煙區劃
                new_row["起點位於防煙區劃"] = self.get_preventzone_name_by_id(self.which_preventzone(
                    most_dangerous_start_point_id))

                # 終點
                most_dangerous_end_point_id = start_to_end_point[most_dangerous_start_point_id][0]
                new_row["終點"] = self.get_transportation_name_by_id(
                    most_dangerous_end_point_id.split("_")[0])

                # 終點編號
                new_row["終點編號"] = most_dangerous_end_point_id

                # 路徑經過防煙區劃 and instance_str
                if preventzone_id == 'none' and transportation_id == 'none':
                    instance_str = "none"
                # read instance_str with "in"
                elif self.which_preventzone(most_dangerous_start_point_id) == preventzone_id:
                    instance_str = "in{}".format(
                        self.__id_join(preventzone_id, transportation_id))
                else:  # read instance_str without "in"
                    instance_str = self.__id_join(
                        preventzone_id, transportation_id)
                # print(instance_str, most_dangerous_end_point_id)
                dijk_parent_dict = self.solutions[instance_str].shortest_paths[
                    most_dangerous_end_point_id][0]
                new_row["instance_str"] = instance_str

                # if new_row["最險峻路徑長度"] != np.inf:
                path_ = [most_dangerous_start_point_id]
                # print(most_dangerous_start_point_id)
                while path_[-1] != most_dangerous_end_point_id:
                    path_.append(dijk_parent_dict[path_[-1]])

                path_preventzone_list = [self.which_preventzone(path_[0])]
                for point in path_:
                    point_lies_in = self.which_preventzone(point)
                    if path_preventzone_list[-1] != point_lies_in:
                        path_preventzone_list.append(point_lies_in)

                path_preventzone_name_list = [self.get_preventzone_name_by_id(
                    p_id) for p_id in path_preventzone_list]

                new_row["路徑經過防煙區劃"] = path_preventzone_name_list

                sol_table = sol_table.append(
                    new_row, ignore_index=True)
            except:
                error = 'error'

        # dump sol table to file
        nowTime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') #取得當前時間
        # 路徑資料夾名
        basename = os.path.basename(self.__output_dir) + "_" + nowTime
        sol_table.to_csv(os.path.join(self.__output_dir,
                         'results_' + basename + '.csv'), index=False, encoding="utf_8_sig")

    def which_preventzone(self, vertex_id):
        """給定 vertex_id 並回傳其所在防煙區劃之 id。

        Args:
            vertex_id (str): 點 id

        Returns:
            str: 防煙區劃 id

        """
        for floor in self.__floors:
            for prevent_zone_id in floor.vertex_prevent_dict:
                if vertex_id in floor.vertex_prevent_dict[prevent_zone_id]:
                    return prevent_zone_id
        return None

    def get_transportation_name_by_id(self, transportation_id):
        """給定 transportation 並回傳其名稱。

        Args:
            transportation_id (str): 傳送點 id

        Returns:
            str: 傳送點名稱

        """
        for floor in self.__floors:
            transportations = floor.get_transportations()
            for transportation in transportations:
                if transportation_id == transportation.get_id():
                    return transportation.get_name()

        return None

    def get_preventzone_name_by_id(self, preventzone_id):
        """給定 preventzone_id 並回傳該防煙區劃之名稱。

        Args:
            preventzone_id (str): 防煙區劃 id

        Returns:
            str: 防煙區劃名稱

        """
        for floor in self.__floors:
            for preventzone in floor.prevent_zones:
                if preventzone_id == preventzone.get_id():
                    return preventzone.get_name()
        return None

    def get_total_graph(self):
        return self.__total_graph

    def get_floors(self):
        return self.__floors

    def get_floor_with_idx(self, idx):
        return self.__floors[idx]

    def __plot_all_floor(self, instance_str, end_point_id, plot_mode):
        """繪製各樓層圖檔。

        Args:
            plot_mode (str): 有點有線請為'1'，沒點沒線為'2'，有點沒線為'3'
            end_point_id (str): 終點id
            instance_str (str): 情境描述字串，格式為{失效防煙區劃id}_{失效傳送點_id}

        """

        plots_dir = os.path.join(self.__output_dir, "plots")
        os.makedirs(plots_dir, exist_ok=True)

        prevent_zone_id = instance_str.split("_")[0]
        if "in" in prevent_zone_id:
            prevent_zone_id = prevent_zone_id[2:]
        # print(prevent_zone_id)
        threads = list()
        floor_names = list()
        figs, axes = list(), list()
        for floor in self.__floors:
            _fig, _ax = plt.subplots(figsize=(25, 10), dpi=100)
            figs.append(_fig)
            axes.append(_ax)
            threads.append(threading.Thread(target=floor.plot,
                           args=(axes[-1], prevent_zone_id, plot_mode)))
            threads[-1].start()
            floor_names.append(floor.get_name())

        for i, (thread, f) in enumerate(zip(threads, floor_names)):
            thread.join()
            if plot_mode == "2":  # 沒點沒線
                figs[i].savefig(os.path.join(plots_dir, "{}_{}_{}.svg").format(
                    instance_str, end_point_id, f))
            else:
                figs[i].savefig(os.path.join(plots_dir, "{}_{}_{}.png").format(
                    instance_str, end_point_id, f))
            logging.debug("完成樓層：{}".format(f))
        logging.info("成功繪製各樓層圖檔！")
        
    def __shorten_path(
        self,
        distance: dict,
        parent: dict,
        start_point_id: str,
        end_point_id: str,
        prevent_zone_obj: PreventZone
    ):
        def __has_intersect(equation_layer, x1, y1, x2, y2):
            for linear in equation_layer:
                if linear.has_intersection_with((x1, y1), (x2, y2)):
                    return True
            return False

        def __recursive_cutedge(equation_layer, paths, vids_list, removed_vids):
            if len(paths) < 3:
                return
            idx = 1
            is_anything_removed = False
            while idx < (len(paths) - 1):
                if len(paths[idx - 1]) != 3 or len(paths[idx + 1]) != 3:
                    idx += 1
                    continue
                try:
                    x1, y1, z = paths[idx - 1]
                    x2, y2, z = paths[idx + 1]
                    if not __has_intersect(equation_layer, x1, y1, x2, y2) and \
                            not __has_intersect(prevent_zone_obj.linear_boundaries, x1, y1, x2, y2):
                        removed_vids.append(vids_list[idx])
                        paths.pop(idx)
                        vids_list.pop(idx)
                        is_anything_removed = True
                    else:
                        idx += 1
                except Exception as e:
                    logging.warning(repr(e))
            if is_anything_removed:
                __recursive_cutedge(equation_layer, paths,
                                    vids_list, removed_vids)

        all_paths = [end_point_id]
        while all_paths[-1] != start_point_id:
            all_paths.append(parent[all_paths[-1]])
        floor_paths = [[[float(x) for x in v_id.split("_")] for v_id in all_paths if str(
            f.get_elevation()) in v_id] for f in self.__floors]
        floor_path_ids = [[v_id for v_id in all_paths if str(
            f.get_elevation()) in v_id] for f in self.__floors]

        removed_vids = list()
        for i, floor in enumerate(self.__floors):
            equation_layer = floor.get_equation(by_ref_only=True)
            for j, path in enumerate(floor_paths[i]):
                if len(path) == 3:
                    x, y, z = floor.get_graph().get_vertex_by_id(
                        floor_path_ids[i][j]).get_coordinate()
                    floor_paths[i][j] = [x, y, z]
            __recursive_cutedge(
                equation_layer, floor_paths[i], floor_path_ids[i], removed_vids
            )
        return removed_vids

    def __stage_two_algorithm_core(
        self, distance, parent,
        start_point_id, prevent_zone_id=None
    ) -> List[str]:
        """
        """
        logging.info("Analysing: {} with {} disabled".format(
            start_point_id,
            prevent_zone_id
        ))

        removed_vids = list()
        not_available_ids = list()

        try:
            shortest_dis = np.inf
            shortest_key = None

            prevent_zone_obj = None
            for floor in self.__floors:
                pz_temp_obj = floor.get_prevent_zone_by_id(prevent_zone_id)
                if pz_temp_obj:
                    prevent_zone_obj = pz_temp_obj
                    break

            for floor in self.__floors:
                transportations = floor.get_transportations()
                for transportation in transportations:
                    if transportation.is_end_point():
                        end_point_id = self.__id_join(
                            transportation.get_id(),
                            floor.get_elevation()
                        )

                        try:
                            logging.debug("Distance to {} is {}".format(
                                end_point_id,
                                distance[end_point_id]
                            ))
                        except KeyError:
                            not_available_ids.append(end_point_id)
                            logging.info("Route does not exist with [{}]".format(end_point_id))
                            continue

                        if distance[end_point_id] < shortest_dis:
                            shortest_key = end_point_id
                            shortest_dis = distance[end_point_id]

                        removed_vids.extend(self.__shorten_path(
                            distance,
                            parent,
                            start_point_id,
                            end_point_id,
                            prevent_zone_obj
                        ))

        except Exception as e:
            logging.warning(repr(e))
            messagebox.showwarning("錯誤", "所選之點在失效防煙區劃內或不在合法乘客區內。")
            return

        lower_bound = 0.0
        algorithm_result = 0.0
        uppper_bound = 0.0

        for floor in self.__floors:
            transportations = floor.get_transportations()
            for transportation in transportations:
                if transportation.is_end_point():
                    end_point_id = self.__id_join(
                        transportation.get_id(),
                        floor.get_elevation()
                    )

                    if end_point_id in not_available_ids:
                        continue

                    dijk_parent_dict = parent

                    if not start_point_id in dijk_parent_dict:
                        raise ValueError("Invalid start point.")

                    path_ = [end_point_id]
                    while path_[-1] != start_point_id:
                        path_.append(dijk_parent_dict[path_[-1]])

                    for i, f in enumerate(self.__floors):
                        def d(x1, y1, x2, y2):
                            return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

                        stage_two_path = np.array([v_id for v_id in path_ if str(
                            f.get_elevation()) in v_id and v_id not in removed_vids])
                        f.path_tmp = stage_two_path.tolist()

                        def _calculate_distance_from_path_ids(path_ids):
                            dis_sum = 0
                            for p1, p2 in zip(path_ids[:-1], path_ids[1:]):
                                if p1.count("_") == 1:
                                    x1, y1, _ = f.get_graph().get_vertex_by_id(
                                        str(p1.split("_")[0])).get_coordinate()
                                else:
                                    x1, y1, _ = f.get_graph().get_vertex_by_id(str(p1)).get_coordinate()
                                if p2.count("_") == 1:
                                    x2, y2, _ = f.get_graph().get_vertex_by_id(
                                        str(p2.split("_")[0])).get_coordinate()
                                else:
                                    x2, y2, _ = f.get_graph().get_vertex_by_id(str(p2)).get_coordinate()
                                dis_sum += d(x1, y1, x2, y2)
                            return dis_sum

                        if len(stage_two_path):
                            if stage_two_path[0].count("_") == 1:
                                x1, y1, _ = f.get_graph().get_vertex_by_id(
                                    str(stage_two_path[0].split("_")[0])).get_coordinate()
                            else:
                                x1, y1, _ = f.get_graph().get_vertex_by_id(
                                    str(stage_two_path[0])).get_coordinate()
                            if stage_two_path[-1].count("_") == 1:
                                x2, y2, _ = f.get_graph().get_vertex_by_id(
                                    str(stage_two_path[-1].split("_")[0])).get_coordinate()
                            else:
                                x2, y2, _ = f.get_graph().get_vertex_by_id(
                                    str(stage_two_path[-1])).get_coordinate()

                            lower_bound += d(x1, y1, x2, y2)
                            algorithm_result += _calculate_distance_from_path_ids(
                                stage_two_path)
                            uppper_bound += _calculate_distance_from_path_ids(np.array([
                                v_id for v_id in path_ if str(f.get_elevation()) in v_id
                            ]))

                    self.__plot_all_floor("{}_{}_{}".format(
                        prevent_zone_id, None, end_point_id
                    ), start_point_id, "2")

        return not_available_ids

    def real_time_escape(self, prevent_zone_id, start_point_id):
        """
        """

        all_vertex_ids = list()
        for vertex_id in self.__total_graph.get_vertex_ids():
            all_vertex_ids.append(vertex_id)
        dijkstra = Dijkstra(all_vertex_ids)

        for floor in self.__floors:
            if prevent_zone_id in floor.vertex_prevent_dict:
                failed_block = floor.vertex_prevent_dict[prevent_zone_id]
                logging.debug("防煙區劃 {} 位於：{}".format(
                    prevent_zone_id, floor.get_name()
                ))
                break

        if start_point_id in failed_block:
            ids_of_transportation_in_block = list()
            for floor_ in self.__floors:
                for transportation in floor_.get_transportations():
                    current_transportation_id = self.__id_join(
                        transportation.get_id(),
                        str(floor_.get_elevation())
                    )
                    if current_transportation_id in failed_block:
                        ids_of_transportation_in_block.append(
                            current_transportation_id
                        )

            self.__total_graph.generate_instance(
                "",
                ids_of_transportation_in_block
            )
        else:
            self.__total_graph.generate_instance("", failed_block)

        connected_component_ids = self.__calculate_connected_components(
            self.__total_graph,
            dfs_start_point_id=start_point_id
        )
        distance, parent = dijkstra.run(
            connected_component_ids,
            self.__total_graph.get_adj_dict(gen_new=False),
            start_point_id
        )

        self.__total_graph.restore_instance()

        not_available_ids = self.__stage_two_algorithm_core(
            distance,
            parent,
            start_point_id,
            prevent_zone_id=prevent_zone_id
        )
        logging.info("Stage two completed, not available ids = {}".format(
            ", ".join(not_available_ids)
        ))

    def get_all_preventzone_ids(self):
        '''取得所有防煙區劃編號列表
        Returns:
            [str]: 防煙區劃編號列表
        '''
        all_preventzones = list()
        for floor in self.__floors:
            prevent_zone_ids = [pz.id for pz in floor.prevent_zones]
            all_preventzones += prevent_zone_ids

        return all_preventzones

    def get_all_may_fail_transportation_ids(self):
        '''取得所有可能維護的傳送點編號列表
        Returns:
            [str]: 可能維護的傳送點編號列表
        '''
        all_transportations_may_failed = list()
        for instance_str in self.solutions:
            failed_transportation_id = self.solutions[instance_str].failed_transportation_id
            if failed_transportation_id == None:
                continue
            if "," in failed_transportation_id:
                continue
            all_transportations_may_failed.append(failed_transportation_id)
        all_transportations_may_failed = list(
            set(all_transportations_may_failed))

        return all_transportations_may_failed

    def update_output_dir(self, output_dir: str) -> None:
        self.__output_dir = output_dir
