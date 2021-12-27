import logging
from util.structure.linear import Linear
from util.structure.line import Line


class PreventZone:
    """防煙區劃。

    Attributes:
        id (str): 防煙區劃編號
        name (str): 防煙區劃名稱
        boundaries ([source.util.structure.line.Line]): 防煙區劃輪廓

    Args:
        id_ (str): 該防煙區劃的id
        name (str): 該防煙區劃的名稱

    Raises:
        TypeError: 如果參數型別錯誤

    """

    def __init__(self, id_, name):
        """Constructor of PreventZone

        Args:
            id_ (str): 該防煙區劃的id
            name (str): 該防煙區劃的名稱

        Raises:
            TypeError: 如果參數型別錯誤

        """
        if type(id_).__name__ != 'str':
            logging.critical("PreventZone 建構子 的 id_ 參數型別錯誤")
            raise TypeError("PreventZone 建構子 的 id_ 參數型別錯誤")
        if type(name).__name__ != 'str':
            logging.critical("PreventZone 建構子 的 name 參數型別錯誤")
            raise TypeError("PreventZone 建構子 的 name 參數型別錯誤")
        self.name = name
        self.id = id_

        self.boundaries = list()
        self.linear_boundaries = list()

    def add_line(self, line: Line):
        """增加防煙區劃的輪廓邊界。

        Args:
            line (source.util.structure.line.Line): 邊界輪廓的線段

        """
        if type(line).__name__ != 'Line':
            logging.critical("add_line 的 line 參數型別錯誤")
            raise TypeError("add_line 的 的 line 參數型別錯誤")

        self.boundaries.append(line)

        linear = Linear(line.get_start_point(), line.get_end_point())
        self.linear_boundaries.append(linear)

    def get_id(self):
        """取得防煙區劃編號。

        Returns:
            str: 防煙區劃編號

        """
        return self.id

    def get_name(self):
        """取得防煙區劃名稱。

        Returns:
            str: 防煙區劃名稱

        """
        return self.name
