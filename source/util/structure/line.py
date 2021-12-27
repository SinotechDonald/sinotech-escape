

class Line:
    """線段。

    Attributes:
        __start_point ((float, float)): 線段的起點(2D空間中)
        __end_point ((float, float)): 線段的終點(2D空間中)
    
    Args:
        start_point ((float, float)): 線段的起點(2D空間中)
        end_point ((float, float)): 線段的終點(2D空間中)

    Raises:
        ValueError: 如果線段起點或終點不為二維
        TypeError: 如果參數型別錯誤

    """

    def __init__(self, start_point, end_point):
        """Line 建構子。

        Args:
            start_point ((float, float)): 線段的起點(2D空間中)
            end_point ((float, float)): 線段的終點(2D空間中)

        Raises:
            ValueError: 如果線段起點或終點不為二維
            TypeError: 如果參數型別錯誤
        
        """
        self.__start_point = (float(start_point[0]), float(start_point[1]))
        self.__end_point = (float(end_point[0]), float(end_point[1]))

        if not self.__check_dim():
            raise ValueError("線段起點或終點不為二維")
        if type(start_point).__name__ != 'tuple':
            raise TypeError("Line 的 start 參數型別錯誤")
        elif type(end_point).__name__ != 'tuple':
            raise TypeError("Line 的 end 參數型別錯誤")

    def __check_dim(self):
        """檢查線段的起終點維度。

        Returns:
            bool: 如果2D則True，否則False。
        
        """
        if len(self.__start_point) != 2 or len(self.__end_point) != 2:
            return False

        return True

    def get_start_point(self):
        """取得線段起點。

        Returns:
            (float, float): 線段起點2D座標
        
        """
        return self.__start_point

    def get_end_point(self):
        """取得線段終點。

        Returns:
            (float, float): 線段終點2D座標
        
        """
        return self.__end_point
