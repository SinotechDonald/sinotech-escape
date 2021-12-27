import logging
import numpy as np


class Linear:
    """線性函數 ax + by + c = 0

    Attributes:
        __a (float): 如上變數
        __b (float): 如上變數
        __c (float): 如上變數
        __start((float, float)): 起始點
        __end((float, float)): 終點

    Args:
        start ((float, float)): 起始點
        end ((float, float)): 終點

    Raises:
        TypeError: 如果a,b,c輸入型別錯誤

    """

    def __init__(self, start, end):
        """線性函數建構子。

        Args:
            start ((float, float)): 起始點
            end ((float, float)): 終點

        Raises:
            TypeError: 如果a,b,c輸入型別錯誤

        """
        if type(start).__name__ != 'tuple':
            raise TypeError("Linear 的 start 參數型別錯誤")
        elif type(end).__name__ != 'tuple':
            raise TypeError("Linear 的 end 參數型別錯誤")

        self.__start = start
        self.__end = end

        if not self.__check_dim():
            raise ValueError("線段起點或終點不為二維")

        if not self.__check_point():
            raise TypeError("Linear 的起終點參數型別錯誤")

        if self.__start[0] == self.__end[0] and self.__start[1] == self.__end[1]:
            raise ValueError("起點和終點重疊")

        self.__compute_equation()

    def __check_dim(self):
        """檢查線段的起終點維度。

        Returns:
            bool: 如果2D則True，否則False。

        """
        if len(self.__start) != 2 or len(self.__end) != 2:
            return False

        return True

    def __check_point(self):
        """檢查線段的起終點型別。

        Returns:
            bool: 如果均為float則True，否則False。

        """
        if type(self.__start[0]).__name__ != 'float' or \
                type(self.__start[1]).__name__ != 'float' or \
                type(self.__end[0]).__name__ != 'float' or \
                type(self.__end[1]).__name__ != 'float':
            return False

        return True

    def __compute_equation(self):
        """計算線段的方程式。
        線性函數 ax + by + c = 0

        Args:
            a (float): 如上變數
            b (float): 如上變數
            c (float): 如上變數

        """
        try:
            self.__a, self.__c = np.linalg.solve(
                np.array([
                    [self.__start[0], 1],
                    [self.__end[0], 1]
                ]),
                np.array([-self.__start[1], -self.__end[1]])
            )
            self.__b = 1
        except np.linalg.LinAlgError:
            if abs(self.__start[0] - self.__end[0]) < \
                    abs(self.__start[1] - self.__end[1]):
                self.__a = 1
                self.__b = 0
                self.__c = -self.__start[0]
            else:
                self.__a = 0
                self.__b = 1
                self.__c = -self.__start[1]

    def get_coefficients(self):
        """取得方程式係數。

        Returns:
            (float, float, float): 係數(a, b, c)

        """
        return (self.__a, self.__b, self.__c)

    def display(self):
        """印出方程式。

        """
        logging.debug(
            "方程式：{}x + {}y + {} = 0".format(self.__a, self.__b, self.__c))

    def get_start_point(self):
        """取得線性函數起始點。

        Returns:
            (float, float): 線性函數起始始點

        """
        return self.__start

    def get_end_point(self):
        """取得線性函數終點。

        Returns:
            (float, float): 線性函數終點
        """
        return self.__end

    def get_intersection(self, linear, mode=None, threshold=0):
        """取得兩線性函數交點之 x 或 y 座標。

        Args:
            linear (source.util.structure.linear.Linear): 障礙物的線性方程式
            mode (str): 本軸為垂直'x'軸或垂直'y'軸
            threshold (float): 容忍值

        Returns:
            (float, float) or None: 如果兩線性函數有交點且 mode 為'x'則回傳交點之 y;如果兩線性函數有交點且 mode 為'y'則回傳交點之 x;否則None。

        """
        try:
            x, y = np.linalg.solve(np.array([[self.__a, self.__b],
                                             [linear.get_coefficients()[0], linear.get_coefficients()[1]]]),
                                   np.array([-self.__c, -linear.get_coefficients()[2]]))
            if x <= max(linear.get_start_point()[0], linear.get_end_point()[0]) + threshold and \
               x >= min(linear.get_start_point()[0], linear.get_end_point()[0]) - threshold and \
               y <= max(linear.get_start_point()[1], linear.get_end_point()[1]) + threshold and \
               y >= min(linear.get_start_point()[1], linear.get_end_point()[1]) - threshold:
                if mode == 'x':
                    return y
                elif mode == 'y':
                    return x
            else:
                return None
        except:
            return None

    def has_intersection_with(self, start, end):
        """判斷兩線性函數是否有交點。

        Args:
            start ((float, float)): 起始點
            end ((float, float)): 終點

        Returns:
            bool: 如果兩線性函數有交點則 true; 否則 false。

        """
        # print("({:.1f}, {:.1f}) <-> ({:.1f}, {:.1f}) X ({}, {}) <-> ({}, {})".format(self.get_start_point()[0], self.get_start_point()[
        #       1], self.get_end_point()[0], self.get_end_point()[1], start[0], start[1], end[0], end[1]))
        if (self.__a*start[0] + self.__b*start[1] + self.__c)*(self.__a*end[0] + self.__b*end[1] + self.__c) <= 0:
            a, b, c = Linear(start, end).get_coefficients()
            if (a*self.get_start_point()[0] + b*self.get_start_point()[1] + c)*(a*self.get_end_point()[0] + b*self.get_end_point()[1] + c) <= 0:
                return True
        return False
