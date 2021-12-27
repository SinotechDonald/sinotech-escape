import copy


class Transportation:
    """傳送點。

    Attributes:
        __name (str): 傳送點名稱
        __id (str): 傳送點編號
        __category (str): 傳送點類別
        __coordinate ((float, float)): 座標位置(2D)
        __end_point (bool): 是否為終點

    Args:
        name (str): 傳送點名稱
        id (str): 傳送點編號
        category (str): 傳送點類別
        coordinate ((float, float)): 座標位置(2D)

    Raises:
        TypeError: 如果輸入值型別錯誤
        ValueError: 如果輸入格式錯誤

    """

    def __init__(self, name, id_, category, coordinate, end_point):
        """Transportation 建構子。

        Args:
            name (str): 傳送點名稱
            id (str): 傳送點編號
            category (str): 傳送點類別
            coordinate ((float, float)): 座標位置(2D)

        Raises:
            TypeError: 如果輸入值型別錯誤
            ValueError: 如果輸入格式錯誤

        """
        if type(name).__name__ != 'str':
            raise TypeError("Transportation 的 name 參數型別錯誤")
        elif type(id_).__name__ != 'str':
            raise TypeError("Transportation 的 id 參數型別錯誤")
        elif type(category).__name__ != 'str':
            raise TypeError("Transportation 的 category 參數型別錯誤")
        elif len(coordinate) != 2:
            raise ValueError("Transportation 的 coordinate 參數不為二維")
        elif type(coordinate[0]).__name__ != 'float' or type(coordinate[1]).__name__ != 'float':
            raise TypeError("Transportation 的 coordinate 參數型別錯誤")
        elif end_point != '是' and end_point != '否':
            raise ValueError("end_point 的值格式錯誤")
        self.__name = name
        self.__id = id_
        self.__category = category
        self.__coordinate = coordinate
        self.__end_point = False
        self.__define_end_point(end_point)
        # self.__to_upper = None

    # def set_to_upper(self, to_upper):
    #     self.__to_upper = to_upper

    # def get_to_upper(self):
    #     return self.__to_upper

    def __define_end_point(self, end_point):
        """給定終點布林值。

        Args:
            end_point (bool): 是否為終點

        """
        self.__end_point = True if end_point == '是' else False

    def is_end_point(self):
        return self.__end_point

    def get_name(self):
        """取得障礙物名稱。

        Returns:
            str: 障礙物名稱

        """
        return self.__name

    def get_id(self):
        """取得障礙物編號。

        Returns:
            str: 障礙物編號

        """
        return self.__id

    def get_category(self):
        """取得障礙物類別。

        Returns:
            str: 障礙物類別

        """
        return self.__category

    def get_coordinate(self):
        """取得障礙物座標。

        Returns:
            (float, float): 障礙物座標

        """
        return copy.deepcopy(self.__coordinate)

    def always_valid(self):
        """判斷障礙物屬性是否會失效。

        """
        return self.__category == "樓梯"
        # return False
