import os
import sys
import inspect


currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
os.chdir(os.path.join(os.getcwd(), ".."))


def test_pytest_alive():
    return True


def test_alive():

    from building import Building

    os.makedirs(".log", exist_ok=True)
    os.makedirs(".cache", exist_ok=True)

    extended_gbxml_path = os.path.join(
        "xml",
        "LG10_Extended_gbXML_20210913.xml"
    )

    LG10 = Building(
        density=(0.2 ** 0.5),
        use_cache=True,
        cache_dir=".cache",
        output_dir=".outputs"
    )
    LG10.load_infos(
        contours_path=extended_gbxml_path
    )

    LG10.to_grid_graph()
    LG10.connect_floors()
    LG10.instances_analysis()
    LG10.calculate_reverse_table()
    # LG10.dump_sol_table()
