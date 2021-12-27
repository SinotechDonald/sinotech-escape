import copy
import logging


class Axis:
    """網格的軸。

    Attributes:
        __equation (source.util.structure.linear.Linear): 本軸線的線性方程式
        __obstacles ([float]): 和本軸線相交的障礙物列表，列表裡面的值為與自身代表的軸正交的座標

    Args:
        linear (source.util.structure.linear.Linear): 本軸線的線性方程式
        
    Raises:
        TypeError: 如果linear的型別錯誤
    
    """

    def __init__(self, linear):
        """Axis 建構子。

        Args:
            linear (source.util.structure.linear.Linear): 本軸線的線性方程式
        
        Raises:
            TypeError: 如果linear的型別錯誤
        
        """
        if type(linear).__name__ != 'Linear':
            logging.error("Axis 的 linear 參數型別錯誤")
            raise TypeError("Axis 的 linear 參數型別錯誤")

        self.__equation = copy.deepcopy(linear)
        self.__obstacles = list()

    def get_equation(self):
        """取得本軸之方程式。

        Returns:
            source.util.structure.linear.Linear: 本軸的方程式
        
        """
        return copy.deepcopy(self.__equation)

    def get_intersections(self, obstacle_linear, mode=None, threshold=0):
        """計算本軸與障礙物的交點列表。

        Args:
            obstacle_linear (source.util.structure.linear.Linear): 障礙物的線性方程式
            mode (str): 本軸為垂直'x'軸或垂直'y'軸
            threshold (float): 容忍值
        
        Raises:
            TypeError: 如果obstaclue_linear型別有誤
            ValueError: 如果mode為'x', 'y'以外的值或容忍值小於零
        
        """
        if type(obstacle_linear).__name__ != 'Linear':
            logging.error("get_intersections 的 obstacle_linear 參數型別錯誤")
            raise TypeError("get_intersections 的 obstacle_linear 參數型別錯誤")
        elif mode != 'x' and mode != 'y' and mode != None:
            logging.error("mode 不為'x'或'y'或 None")
            raise ValueError("mode 不為'x'或'y'或 None")
        elif threshold < 0:
            logging.error("threshold 小於 0")
            raise ValueError("threshold 小於 0")

        _ = self.__equation.get_intersection(obstacle_linear, mode, threshold)
        if _ != None:
            self.__obstacles.append(_)

    # def add_obstacle_point(self, point): seems usless?
    #     self.obstacles.append(point)

    def get_obstacles(self):
        """取得本軸與障礙物交點列表。

        Returns:
            [float]: 本軸與障礙物交點列表
        
        """
        return copy.deepcopy(self.__obstacles)

    def display(self):
        """印出本軸與障礙物資訊。
        
        """
        logging.debug("Axis infos:\n\t", end='')
        self.__equation.display()
        logging.debug("\t", self.__obstacles, sep='')
