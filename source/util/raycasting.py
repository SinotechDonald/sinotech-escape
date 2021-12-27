def isPointinPolygon(point, rangelist):  # [[0,0],[1,1],[0,1],[0,0]] [1,0.8]
    lnglist = []
    latlist = []
    for i in range(len(rangelist)-1):
        lnglist.append(rangelist[i][0])
        latlist.append(rangelist[i][1])

    count = 0
    point1 = rangelist[0]
    for i in range(1, len(rangelist)):
        point2 = rangelist[i]
        if (point[0] == point1[0] and point[1] == point1[1]) or (point[0] == point2[0] and point[1] == point2[1]):
            return False
        if (point1[1] < point[1] and point2[1] >= point[1]) or (point1[1] >= point[1] and point2[1] < point[1]):
            point12lng = point2[0] - (point2[1] - point[1]) * \
                (point2[0] - point1[0])/(point2[1] - point1[1])
            if (point12lng == point[0]):
                return False
            if (point12lng < point[0]):
                count += 1
        point1 = point2
    if count % 2 == 0:
        return False
    else:
        return True
