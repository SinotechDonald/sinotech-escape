import numpy as np
from bs4 import BeautifulSoup


with open("LG10.xml", "rb") as f:
    buf = f.read()
    print(len(buf))
    soup = BeautifulSoup(buf, 'xml')

# print(soup.find("CartesianPoint"))
# print([float(x.text) for x in soup.find("CartesianPoint").find_all("Coordinate")])

with open("Name.txt", "w") as f:
    for name in soup.find_all("Name"):
        f.write("{}\n".format(str(name.text)))

with open("CADObjectId.txt", "w") as f:
    for id in soup.find_all("CADObjectId"):
        f.write("{}\n".format(str(id.text)))

with open("tags.txt", "w") as f:
    for tag in np.unique([t.name for t in soup.find_all()]):
        f.write("{}\n".format(str(tag)))
