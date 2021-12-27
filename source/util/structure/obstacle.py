import copy


class Obstacle:
    """障礙物。

    Attributes:
        __id (str): 障礙物編號
        __name (str): 障礙物名稱
        __category (str): 障礙物種類
        __contour (source.util.structure.contour.Contour): 障礙物輪廓
    
    Args: 
        ID (str): 物件編號
        name (str): 物件名稱
        category (str): 物件類別
        contour (source.util.structure.contour.Contour): 物件輪廓
    
    Raises:
        TypeError: 如果任何input的型別錯誤
    
    """

    def __init__(self, ID, name, category, contour):
        """ Obstacle 建構子。

        Args: 
            ID (str): 物件編號
            name (str): 物件名稱
            category (str): 物件類別
            contour (source.util.structure.contour.Contour): 物件輪廓
        
        Raises:
            TypeError: 如果任何input的型別錯誤
        
        """
        if type(ID).__name__ != 'str':
            pass
            # raise TypeError("Obstacle 的 ID 參數型別錯誤")
        elif type(name).__name__ != 'str':
            raise TypeError("Obstacle 的 name 參數型別錯誤")
        elif type(category).__name__ != 'str':
            raise TypeError("Obstacle 的 category 參數型別錯誤")
        elif type(contour).__name__ != 'Contour':
            raise TypeError("Obstacle 的 contour 參數型別錯誤")

        self.__id = ID
        self.__name = name
        self.__category = category
        self.__contour = contour

    def get_ID(self):
        """取得障礙物編號。

        Returns:
            str: 障礙物編號
        
        """
        return self.__id

    def get_name(self):
        """取得障礙物名稱。

        Returns:
            str: 障礙物名稱
        
        """
        return self.__name

    def get_category(self):
        """取得障礙物類別。

        Returns:
            str障礙物類別
        
        """
        return self.__category

    def get_contour(self):
        """取得障礙物輪廓。

        Returns:
            source.util.structure.contour.Contour: 障礙物輪廓
        
        """
        return copy.deepcopy(self.__contour)
