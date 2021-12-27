import copy


class Contour:
    """輪廓。

    Attributes:
        __lines ([source.util.structure.line.Line]): 所有線段集合
    
    """

    def __init__(self, lines):
        """Contour 建構子。

        Args:
            lines ([source.util.structure.line.Line]): 所有線段集合
        
        Raises:
            TypeError: 如果線段的格式不符預期
        
        """
        if type(lines).__name__ != 'list':
            raise TypeError("lines 的型別錯誤")
        for line in lines:
            if type(line).__name__ != 'Line':
                raise TypeError("lines 列表中值的型別錯誤")
        self.__lines = lines

    def get_lines(self):
        """取得輪廓線段陣列。

        Returns:
            [source.util.structure.line.Line]: 輪廓線段陣列
        
        """
        return copy.deepcopy(self.__lines)
