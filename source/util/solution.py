class Solution:
    """
    Attributes:
        shortest_paths ({({str}, {float})}): key: 終點, value: (parent id dict, distance dict)
        failed_transportation_id (str): 失效傳送點id
        failed_block_id (str): 失效防煙區劃id
    
    """

    def __init__(self, failed_transportation_id, failed_block_id):
        self.failed_transportation_id = failed_transportation_id
        self.failed_block_id = failed_block_id
        self.shortest_paths = dict()
    pass
