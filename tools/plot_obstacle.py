import os
import json
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


def plot_obstacles_from_json(path):

    with open(path, "r") as f:
        obstacles = json.load(f)

    plt.figure(dpi=2000)
    font = FontProperties(fname=r"DFLiHei-Bd.ttc", size=4)

    for obs in obstacles:

        if obs["level"] == "月台層":

            coords = [(json.loads(curve_point["startPoint"])[0], json.loads(
                curve_point["startPoint"])[1]) for curve_point in obs["curvePointList"]]
            coords.append(coords[0])
            xs, ys = zip(*coords)
            plt.plot(xs, ys, linewidth=0.5)

            plt.annotate(obs["name"], (json.loads(obs["curvePointList"][0]["startPoint"])[
                         0], json.loads(obs["curvePointList"][0]["startPoint"])[1]), fontproperties=font)

    plt.savefig("obstacles.png")


plot_obstacles_from_json("./source/json/obstacles_20210324.json")
