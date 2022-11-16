from fileinput import filename
import os
from posixpath import join
import shutil
import logging
import time
import datetime
import pandas as pd

from tkinter import Tk, messagebox, filedialog, Label, Button, simpledialog
from tkinter.constants import NONE
from util.structure.transportation import Transportation
from datetime import datetime

from building import Building
from gui.stage_two import get_prevent_zone_id


class TkApp:

    def __init__(self, base_path, log_dir, cache_dir) -> None:
            
        self.start_Output_cache = '' # 預設起始Output cache路徑

        self.base_path = base_path  # repo/app path
        self.log_dir = log_dir  # ~/.sinopath/.log
        # cache_dir  # ~/.sinopath/.cache

        # if os.path.exists(os.path.join(self.base_path, ".cache")) and \
        #         not len([f for f in os.listdir(self.cache_dir) if ".pickle" in f]):
        #     # 如果 APP 有 cache 而系統沒有，就 copy 過去系統
        #     self.__reset_cache()

        # if messagebox.askquestion("確認", "是否強制重置快取？") == "yes":
        #     self.__reset_cache()

        self.meta_file_path = None
        self.xml_path = None
        # self.input_cache_dir = None
        self.output_cache_dir = None
        self.output_dir = None

        self.root = Tk()
        self.root.title("SinoPath_1.3.0")
        # self.root.geometry("720x480")

        # 置中
        # Gets the requested values of the height and widht. 720x480
        windowWidth = 720
        windowHeight = 480        
        # Gets both half the screen width/height and window width/height
        positionRight = int(self.root.winfo_screenwidth()/2 - windowWidth/2)
        positionDown = int(self.root.winfo_screenheight()/3 - windowHeight/2)        
        # Positions the window in the center of the page.
        size = '720x480+%s+%s' % (positionRight, positionDown)
        self.root.geometry(size)

        self.xml_label = Label(self.root, text=self.xml_path)
        self.xml_label.config(font=("Courier", 8))
        # self.xml_label['text'] = "D:/逃生路徑/_LG10/gbXML/LG10_Extended_gbXML_20211102.xml"
        # self.xml_path = "D:/逃生路徑/_LG10/gbXML/LG10_Extended_gbXML_20211102.xml"
        # self.xml_label['text'] = "D:/逃生路徑/_G22/gbXML/G22_Extended_gbXML_20220524.xml"
        # self.xml_path = "D:/逃生路徑/_G22/gbXML/G22_Extended_gbXML_20220524.xml"
        self.xml_label.pack()

        buttonCommit1 = Button(
            self.root,
            height=1,
            width=20,
            text="gbXML檔案",
            command=lambda: self.__handleChangeFile(
                self.xml_label,
                "Please select a extended gbXML file",
                "xml",
                "LG10_Extended_gbXML_20211104.xml"
            )
        )
        buttonCommit1.pack()

        # input_cache_label = Label(self.root, text=self.input_cache_dir)
        # input_cache_label.config(font=("Courier", 8))
        # input_cache_label['text'] = "D:/逃生路徑/_LG10/Input cache"
        # self.input_cache_dir = "D:/逃生路徑/_LG10/Input cache"
        # input_cache_label.pack()

        # buttonCommit2 = Button(
        #     self.root,
        #     height=1,
        #     width=20,
        #     text="Input cache directory",
        #     command=lambda: self.__handleChangeDir(
        #         input_cache_label,
        #         "Select a input cache directory",
        #         1
        #     )
        # )
        # buttonCommit2.pack()

        output_cache_label = Label(self.root, text=self.output_cache_dir)
        # output_cache_label = Label(self.root, text=self.input_cache_dir) # <-- 台大原本這樣寫
        output_cache_label.config(font=("Courier", 8))
        # output_cache_label['text'] = "D:/逃生路徑/_LG10/Output cache"
        # self.output_cache_dir = "D:/逃生路徑/_LG10/Output cache"
        # output_cache_label['text'] = "D:/逃生路徑/_G22/Output cache"
        # self.output_cache_dir = "D:/逃生路徑/_G22/Output cache"
        output_cache_label.pack()

        buttonCommit2 = Button(
            self.root,
            height=1,
            width=20,
            text="cache輸出路徑",
            command=lambda: self.__handleChangeDir(
                output_cache_label,
                "Select a Output cache directory",
                2
            )
        )
        buttonCommit2.pack()

        output_label = Label(self.root, text=self.output_dir)
        output_label.config(font=("Courier", 8))
        # output_label['text'] = "D:/逃生路徑/_LG10/Output directory"
        # self.output_dir = "D:/逃生路徑/_LG10/Output directory"
        # output_label['text'] = "D:/逃生路徑/_G22/Output directory"
        # self.output_dir = "D:/逃生路徑/_G22/Output directory"
        output_label.pack()

        buttonCommit2 = Button(
            self.root,
            height=1,
            width=20,
            text="結果輸出路徑",
            command=lambda: self.__handleChangeDir(
                output_label,
                "Please select a output directory",
                0
            )
        )
        buttonCommit2.pack()

        _ = Label(self.root, text="")
        _.config(font=("Courier", 12))
        _.pack()

        buttonCommit2 = Button(
            self.root,
            height=1,
            width=20,
            text="分析運算",
            command=lambda: self.__handleRun()
        )
        buttonCommit2.pack()


        _ = Label(self.root, text="")
        _.config(font=("Courier", 12))
        _.pack()
        buttonCommit2 = Button(
            self.root,
            height=1,
            width=14,
            text="路徑輸出",
            command=lambda: self.__handlePlot(0)
        )
        
        buttonCommit2.pack()


        self.plotBtn = None

        self.root.mainloop()

    def __reset_cache(self, output_dir: str, suffix: str = ".pickle") -> None:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
    # 台大原本這樣寫
    # def __reset_cache(self, input_dir: str, output_dir: str, suffix: str = ".pickle") -> None:
    #     if input_dir == output_dir:
    #         return
    #     if not os.path.exists(output_dir):
    #         os.makedirs(output_dir, exist_ok=True)
    #     for path in os.listdir(input_dir):
    #         if suffix in path:
    #             shutil.copy(
    #                 os.path.join(input_dir, path),
    #                 os.path.join(output_dir, path)
    #             )

    # 檢核Output cache所有子資料夾中, 是否都有完整的cache, 將Output cache的.pickle檔複製過去
    def __copy_cache(self, suffix: str = ".pickle"):

        for dir in os.walk(self.output_cache_dir): # 搜尋底下所有子資料夾
            os.chdir(dir[0])
            directory = os.getcwd()
            if not os.path.samefile(self.output_cache_dir, directory):
                for fileName in os.listdir(self.output_cache_dir):
                    if suffix in fileName:
                        if not os.path.exists(os.path.join(directory, fileName)):                            
                            shutil.copy(
                                os.path.join(self.output_cache_dir, fileName),
                                os.path.join(directory, fileName)
                            )

    def __handleChangeFile(self, target_label: Label, title_: str, type: str, default_path: str) -> None:
        target_label["text"] = os.path.join(
            type,
            filedialog.askopenfilename(
                title=title_,
                initialdir=os.path.join(self.base_path, type),
                initialfile=os.path.join(self.base_path, type, default_path),
                filetypes=[(type.upper(), "*.{}".format(type),)]
            )
        )
        if type == "json":
            self.meta_file_path = target_label["text"]
        elif type == "xml":
            self.xml_path = target_label["text"]

    def __handleChangeDir(self, target_label: Label, title_: str, type: int) -> None:
        """
        type: 0 -> output_dir, 1 -> input_cache_dir, 2 -> output_cache_dir
        """
        target_label["text"] = filedialog.askdirectory(title=title_)
        if type == 0:
            self.output_dir = target_label["text"]
        elif type == 1:
            self.input_cache_dir = target_label["text"]
        elif type == 2:
            self.output_cache_dir = target_label["text"]

    def __default_set(self, output_cache_dir):
        self.building = Building(
                density=(0.2 ** 0.5),
                use_cache=True,
                cache_dir=output_cache_dir,
                output_dir=self.output_dir
            )
        self.building.load_infos(
            contours_path=self.xml_path,
            msgBox='no'
        )
        
        self.building.to_grid_graph()
        self.building.connect_floors()
        self.building.instances_analysis()
        self.building.calculate_reverse_table()

        while not self.__check_output_dir_existence_and_premission(self.output_dir):
            self.output_dir = filedialog.askdirectory(
                title="輸出資料夾不存在或權限錯誤，請重新選擇"
            )
            self.building.update_output_dir(self.output_dir)

    def __handleRun(self): # 分析運算

        if (not self.xml_path or ".xml" not in self.xml_path) \
                or not self.output_dir:
            messagebox.showwarning("Warning", "Please choose some files.")
            return

        self.__reset_cache(self.output_cache_dir)
        # self.__reset_cache(self.input_cache_dir, self.output_cache_dir)

        # 修改內容, 把樓梯都更換為電扶梯
        msgBox = messagebox.askquestion("SinoPath", "是否將樓梯加入失效情境運算?")

        self.start_Output_cache = self.output_cache_dir # 起始母資料夾

        self.building = Building(
            density=(0.2 ** 0.5),
            use_cache=True,
            cache_dir=self.output_cache_dir,
            output_dir=self.output_dir
        )
        self.building.load_infos(
            contours_path=self.xml_path,
            msgBox=msgBox
        )

        self.building.to_grid_graph()
        while messagebox.askquestion("SinoPath", "Open Editor?") == "yes":
            self.root.update()
            self.building.edit_graph_gui()
        
        start_time = time.perf_counter()

        # 建立Excel儲存運算結果
        nowTime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') #取得當前時間
        writerPath = os.path.join(self.output_dir, 'results_' + nowTime + '.xlsx')
        writer = pd.ExcelWriter(writerPath, engine="xlsxwriter")
        writer.save()
        writer.close()

        # 檢核Output cache所有子資料夾中, 是否都有完整的cache, 將Output cache的.pickle檔複製過去
        self.__copy_cache()

        # 搜尋Output cache資料夾中, 所有子資料夾
        for dir in os.walk(self.output_cache_dir): # 搜尋底下所有子資料夾
            os.chdir(dir[0])
            self.output_cache_dir = os.getcwd()

            # 路徑資料夾名設定為Sheet Name
            sheetName = os.path.basename(self.output_cache_dir)

            self.building = Building(
                density=(0.2 ** 0.5),
                use_cache=True,
                cache_dir=self.output_cache_dir,
                output_dir=self.output_dir
            )
            self.building.load_infos(
                contours_path=self.xml_path,
                msgBox=msgBox
            )

            self.building.connect_floors()
            self.building.instances_analysis()
            self.building.calculate_reverse_table()

            while not self.__check_output_dir_existence_and_premission(self.output_dir):
                self.output_dir = filedialog.askdirectory(
                    title="輸出資料夾不存在或權限錯誤，請重新選擇"
                )
                self.building.update_output_dir(self.output_dir)

            # 匯出Excel檔
            # self.building.dump_sol_table()
            self.building.export_to_excel(writerPath, sheetName)

        # 分析完成後, 預設回母資料夾的cache
        self.output_cache_dir = self.start_Output_cache
        self.__default_set(self.output_cache_dir)

        end_time = time.perf_counter()
        spendTime = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
        logging.info("執行結束！共花費 " + spendTime + " 秒。")
        messagebox.showinfo("完成", "成功分析逃生路徑！共花費 " + spendTime + " 秒。")

        # if not self.plotBtn:
        #     _ = Label(self.root, text="")
        #     _.config(font=("Courier", 12))
        #     _.pack()
        #     _ = Label(self.root, text="路徑輸出")
        #     _.config(font=("Courier", 12))
        #     _.pack()
        #     self.plotBtn = Button(
        #         self.root,
        #         height=1,
        #         width=14,
        #         text="路徑輸出",
        #         command=lambda: self.__handlePlot(0)
        #     )
        #     self.plotBtn.pack()
            # _ = Label(self.root, text="第二階段")
            # _.config(font=("Courier", 12))
            # _.pack()
            # stageTwoBtn = Button(
            #     self.root,
            #     height=1,
            #     width=14,
            #     text="運行第二階段",
            #     command=lambda: self.__handleStageTwo()
            # )
            # stageTwoBtn.pack()

    def __check_output_dir_existence_and_premission(self, output_dir: str) -> bool:
        if not os.path.exists(output_dir):
            logging.info("Not exists: {}".format(
                output_dir
            ))
            return False
        try:
            open(os.path.join(output_dir, ".sinopath_test_write_permission"), "w")
            os.remove(os.path.join(
                output_dir,
                ".sinopath_test_write_permission"
            ))
            logging.info("Exists: {}".format(
                output_dir
            ))
            return True
        except Exception as e:
            logging.info("{} encounters {}, did not pass checking".format(
                output_dir, repr(e)
            ))
            return False

    def __handlePlot(self, type: int): # 路徑輸出
        
        # 選擇要運行情境的cache資料夾
        root = Tk()
        root.withdraw()
        # 如果未更換過Output cache dir, 則不重新讀取cache, 可直接輸出svg圖
        if self.output_cache_dir is not self.start_Output_cache:
            self.start_Output_cache = self.output_cache_dir
        # self.output_cache_dir = filedialog.askdirectory(parent=root) 選擇要運算的Output cache資料夾
        
            self.__default_set(self.output_cache_dir)
            # self.building = Building(
            #     density=(0.2 ** 0.5),
            #     use_cache=True,
            #     cache_dir=self.output_cache_dir,
            #     output_dir=self.output_dir
            # )
            # self.building.load_infos(
            #     contours_path=self.xml_path,
            #     msgBox='no'
            # )
            
            # self.building.to_grid_graph()
            # self.building.connect_floors()
            # self.building.instances_analysis()
            # self.building.calculate_reverse_table()

            # while not self.__check_output_dir_existence_and_premission(self.output_dir):
            #     self.output_dir = filedialog.askdirectory(
            #         title="輸出資料夾不存在或權限錯誤，請重新選擇"
            #     )
            #     self.building.update_output_dir(self.output_dir)
        if type == 0:
            # # key: preventzone name, value: preventzone id
            # prevent_zone_dict = {self.building.get_preventzone_name_by_id(
            #     id_): id_ for id_ in self.building.get_all_preventzone_ids()}
            # # key: transportation name, value: transportation id
            # transportation_dict = {self.building.get_transportation_name_by_id(
            #     id_.split("_")[0]): id_ for id_ in self.building.get_all_may_fail_transportation_ids()}

            # prevent_zone_ids = list(prevent_zone_dict.keys())
            # transportation_ids = list(transportation_dict.keys())

            # seletect_prevent_zone = prevent_zone_dict[get_prevent_zone_id(
            #     "Select prevent zone", prevent_zone_ids)]
            # seletect_transportation = transportation_dict[get_prevent_zone_id(
            #     "Select transportation", transportation_ids)]
            # print(seletect_prevent_zone, seletect_transportation)
            # instance_str = "{}_{}".format(
            #     seletect_prevent_zone, seletect_transportation)

            # floor_idx_dict = dict({
            #     floor.get_name(): i
            #     for i, floor in enumerate(self.building.get_floors())
            # })
            # selected_floor_idx = floor_idx_dict[
            #     get_prevent_zone_id(
            #         "選擇起始點會在哪一層",
            #         list(floor_idx_dict.keys())
            #     )
            # ]

            # start_point = self.building.get_floor_with_idx(
            #     selected_floor_idx
            # ).select_point()
            # self.root.update()

            # if self.building.which_preventzone(start_point) == seletect_prevent_zone:
            #     instance_str = "in" + instance_str

            instance_str = simpledialog.askstring(
                title="",
                prompt="Input instance_str:"
            )
            start_point = simpledialog.askstring(
                title="",
                prompt="Input start point:"
            )

            failed_endpoints = self.building.plot_sol(
                "2",
                start_point,
                # "",
                instance_str
            )
            if len(failed_endpoints):
                messagebox.showwarning(
                    "計算錯誤", "不存在到終點{}的路徑".format(failed_endpoints)
                )
                self.root.update()

    def __handleStageTwo(self):
        prevent_zone_dict = {
            self.building.get_preventzone_name_by_id(id_): id_
            for id_ in self.building.get_all_preventzone_ids()
        }
        prevent_zone_ids = list(prevent_zone_dict.keys())
        prevent_zone_id = prevent_zone_dict[
            get_prevent_zone_id(
                "Select prevent zone",
                prevent_zone_ids
            )
        ]
        logging.info("Selected prevent zone: {}".format(prevent_zone_id))

        floor_idx_dict = dict({
            floor.get_name(): i
            for i, floor in enumerate(self.building.get_floors())
        })
        selected_floor_idx = floor_idx_dict[
            get_prevent_zone_id(
                "選擇起始點在哪一層",
                list(floor_idx_dict.keys())
            )
        ]
        start_point_id = self.building.get_floors()[
            selected_floor_idx
        ].select_point()
        logging.debug("Selected: {}".format(start_point_id))

        while not self.__check_output_dir_existence_and_premission(self.output_dir):
            self.output_dir = filedialog.askdirectory(
                title="輸出資料夾不存在或權限錯誤，請重新選擇"
            )
            self.building.update_output_dir(self.output_dir)

        self.building.real_time_escape(
            prevent_zone_id,
            start_point_id
        )
