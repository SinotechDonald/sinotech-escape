

class Vertex:
    """點。

    Attributes:
        __x (float): x座標
        __y (float): y座標
        __z (float): z座標
        __id (str): 編號，例如點(1,2,3)的__id為1_2_3
    
    Args:
        x (float): x座標
        y (float): y座標
        z (float): z座標
    
    Raises:
        TypeError: 如果x,y,z輸入型別錯誤
        
    """

    def __init__(self, x, y, z, id_):
        """Vertex 建構子
        Args:
            x (float): x座標
            y (float): y座標
            z (float): z座標
        
        Raises:
            TypeError: 如果x,y,z輸入型別錯誤
        
        """
        if type(x).__name__ != 'float' or type(y).__name__ != 'float' or type(z).__name__ != 'float':
            raise TypeError("Vertex 的座標參數型別錯誤")
        if type(id_).__name__ != 'str':
            raise TypeError("Vertex 的 id 型別錯誤")

        self.__x = x
        self.__y = y
        self.__z = z
        self.__id = id_

    def get_coordinate(self):
        """取得點座標。

        Returns:
            (float, float, float): 點座標tuple
        
        """
        return (self.__x, self.__y, self.__z)

    def get_id(self):
        """取得點編號。
    
        Returns:
            str: 點ID
        
        """
        return self.__id
