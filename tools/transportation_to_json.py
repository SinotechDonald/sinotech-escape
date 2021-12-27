import os
import json


f1 = open(os.path.join("source", "json", "transportations_20210316.json"), "r")
f2 = open(os.path.join("source", "json", "transportations_20210327.json"), "w")

buf = f1.read()

buf = buf.replace("(", "[").replace(")", "]")

buf = " ".join([("\"" + str(x[:-1]) + "\":") if (":" in x and "\"" not in x) else str(x) for x in buf.split()])
buf = " ".join([("\"" + str(x[:-1]) + "\",") if ("," in x and not x.replace("[", "").replace("]", "").replace(",", "").replace("-", "").replace(".", "", 1).isdigit()) else str(x) for x in buf.split()])

for x in buf.split("} "):
    print("{ " + x + "} " + (" }" if "}" not in x else ""))
    _ = json.loads("{ " + x + "} " + (" }" if "}" not in x else ""))

json.dump([json.loads("{ " + x + "} " + (" }" if "}" not in x else "")) for x in buf.split("} ")], f2, ensure_ascii=False, indent=4)
