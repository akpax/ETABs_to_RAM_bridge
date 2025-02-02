"""
This is the main module of the application. It contains the tkinter GUI.


"""

from tkinter import (
    Tk,
    Button,
    filedialog,
    font,
    StringVar,
    Listbox,
    Canvas,
    Toplevel,
    Frame,
    Text,
    Scrollbar,
)
from tkinter import ttk
import json
from pathlib import Path
from PIL import ImageTk, Image
from datetime import datetime
from utils.ETABS_utils import *
from utils.RAM_utils import *
from utils.misc_utils import *


small_italic_font = "Arial 7 italic"
arrow_image_path = resource_path(R"images\arrow_medium.png")
# arrow_image_path = "images\arrow_medium.png"
blue_button_color_code = "#1F51FF"
white_color_code = "#FFFFFF"
red_button_color_code = "#D04848"


ETABS_analysis_types_dict = {
    "Linear Static": 1,
    "Nonlinear Static": 2,
    "Modal": 3,
    "Response Spectrum": 4,
    "Linear History": 5,
    "Nonlinear History": 6,
    "Linear Dynamic": 7,
    "Nonlinear Dynamic": 8,
    "Moving Load": 9,
    "Buckling": 10,
    "Steady State": 11,
    "Power Spectral Density": 12,
    "Linear Static Multi Step": 13,
    "Hyper Static": 14,
}


class ETABS_to_RAM_APP:
    def __init__(self, root):
        # initialize attritibutes
        self.ETABS_load_cases = []
        self.ETABS_levels = []
        self.ETABS_model_path = None
        self.ETABS_results = None
        self.ETABSObject = None
        self.SapModel = None

        self.RAM_model_path = None
        self.RAM_load_layers = []
        self.concept = None
        self.root = root

        self.root.title("ETABS to RAM Concept Column Load Transfer")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.notebook = ttk.Notebook(self.root)
        f1 = ttk.Frame(self.notebook)
        f2 = ttk.Frame(self.notebook)
        self.notebook.add(f1, text="Model Paths Config")
        self.notebook.add(f2, text="Load Transfer Hub", state="disabled")
        # self.notebook.tab("Load Transfer Hub", state="normal")
        self.notebook.pack(expand=True, fill="both", padx=10, pady=(10, 0))

        # Create a Frame for the logging area
        logging_frame = ttk.Frame(self.root)
        logging_frame.pack(fill="both", expand=False, padx=10, pady=(0, 10))

        # Create the Text widget and Scrollbar within the logging frame
        self.log = Text(
            logging_frame,
            state="disabled",
            width=80,
            height=6,
            wrap="none",
            borderwidth=2,
            relief="sunken",
        )
        self.log.grid(row=0, column=0, sticky="ew", padx=(0, 0), pady=(10, 0))

        scrollbar = ttk.Scrollbar(
            logging_frame, orient="vertical", command=self.log.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns", pady=(10, 10))
        self.log["yscrollcommand"] = scrollbar.set

        # add credits
        ttk.Label(
            logging_frame,
            text="Developed by Austin Paxton. Contact via LinkedIn: https://www.linkedin.com/in/austin-paxton-98b496165/",
            font=small_italic_font,
        ).grid(row=1, column=0)

        # Configure the logging frame's column to expand, filling the space
        logging_frame.grid_columnconfigure(0, weight=1)

        #######################   f1 Widgets   #######################
        # label and selection for input file
        ttk.Label(
            f1, text="Select ETABS Model file:", font=font.nametofont("TkHeadingFont")
        ).grid(row=0, column=0, pady=20)
        Button(f1, text="Browse", command=self.select_ETABS_model_path).grid(
            row=0, column=2
        )
        self.ETABS_model_path_label = ttk.Label(f1, text="")
        self.ETABS_model_path_label.grid(row=0, column=1)

        ttk.Label(
            f1, text="Select RAM Model file:", font=font.nametofont("TkHeadingFont")
        ).grid(row=1, column=0)
        Button(
            f1,
            text="Browse",
            command=self.select_RAM_model_path,
        ).grid(row=1, column=2)
        self.RAM_model_path_label = ttk.Label(f1, text="")
        self.RAM_model_path_label.grid(row=1, column=1)

        self.pull_data_button = Button(
            f1,
            text="Access ETABS and RAM Concept Data",
            command=self.pull_model_data,
            state="disabled",
            bg=blue_button_color_code,
            fg=white_color_code,
        )
        self.pull_data_button.grid(row=2, column=0, columnspan=3, pady=(20, 5))

        ttk.Label(
            f1,
            font=small_italic_font,
            text="Note: Data Extraction may take a while if model unlocked. Program may appear unresponsive while analysis runs.",
        ).grid(row=3, column=0, columnspan=3, sticky="ew", padx=(10, 0))

        #######################   f2 Widgets   #######################
        # __________________ETABS_frame___________________
        self.ETABS_frame = ttk.Frame(f2, relief="raised")
        self.ETABS_frame.grid(row=0, column=0)
        ttk.Label(
            self.ETABS_frame,
            text="ETABS User Inputs:",
            font=font.nametofont("TkHeadingFont"),
        ).grid(row=0, column=0, pady=20)

        ttk.Label(
            self.ETABS_frame,
            text="Select Level:",
            font=font.nametofont("TkDefaultFont"),
        ).grid(row=1, column=0, padx=(10, 0), sticky="w")
        self.levelvar = StringVar(self.ETABS_frame, value=self.ETABS_levels)
        self.combo_box_levels = ttk.Combobox(
            self.ETABS_frame, textvariable=self.levelvar
        )
        self.combo_box_levels.grid(
            row=1, column=1, padx=(0, 10)
        )  # grid after to avoid chaining and assigning .grid() return of None
        self.combo_box_levels["state"] = "readonly"  # make read only

        # add analysis combo box
        ttk.Label(
            self.ETABS_frame,
            text="Select Analysis Type:",
            font=font.nametofont("TkDefaultFont"),
        ).grid(row=2, column=0, padx=(10, 0), pady=5, sticky="w")

        # self.ETABS_analysis_types = list(ETABS_analysis_types_dict.keys())
        self.analysis_type = StringVar(
            self.ETABS_frame, list(ETABS_analysis_types_dict.keys())[0]
        )
        self.analysis_combo_box = ttk.Combobox(
            self.ETABS_frame, textvariable=self.analysis_type, state="readonly"
        )
        self.analysis_combo_box.grid(row=2, column=1, padx=(0, 10), pady=5)
        self.analysis_combo_box["values"] = list(ETABS_analysis_types_dict.keys())
        self.analysis_combo_box.bind(
            "<<ComboboxSelected>>", self.analysis_combo_box_handler
        )
        # self.analysis_combo_box.current(1)  # set to linear static by default

        ttk.Label(
            self.ETABS_frame,
            text="Select Load Cases:",
            font=font.nametofont("TkDefaultFont"),
        ).grid(row=3, column=0, padx=(10, 0), sticky="w")
        self.load_case_var = StringVar(self.ETABS_frame, value=self.ETABS_load_cases)
        self.l_box = Listbox(
            self.ETABS_frame,
            listvariable=self.load_case_var,
            selectmode="extended",
            height=10,
            exportselection=0,
        )
        self.l_box.grid(row=4, column=1, padx=(0, 10))

        ttk.Label(
            self.ETABS_frame,
            text="Note: Multiple Load Cases can be selected",
            font=small_italic_font,
        ).grid(row=5, column=1, pady=(0, 10), padx=(0, 10))

        # __________________arrow image___________________
        img_loc = (35, 35)
        canvas = Canvas(f2, width=120, height=100)
        canvas.grid(row=0, column=1, padx=(40, 0))
        im = Image.open(arrow_image_path)
        im.convert("RGBA")
        self.photoimage = ImageTk.PhotoImage(im)
        canvas.create_image(*img_loc, image=self.photoimage)

        # __________________RAM_frame___________________
        self.RAM_frame = ttk.Frame(f2, relief="raised")
        self.RAM_frame.grid(row=0, column=2)
        ttk.Label(
            self.RAM_frame,
            text="RAM Concept Inputs:",
            font=font.nametofont("TkHeadingFont"),
        ).grid(row=0, column=0, pady=20)

        ttk.Label(
            self.RAM_frame,
            text="Select RAM Loading Layer:",
            font=font.nametofont("TkDefaultFont"),
        ).grid(row=1, column=0, pady=20, sticky="w")
        self.load_layers_var = StringVar(self.RAM_frame, value=self.RAM_load_layers)
        self.combo_box_load_layer = ttk.Combobox(
            self.RAM_frame,
            textvariable=self.load_layers_var,
        )
        self.combo_box_load_layer.grid(
            row=1, column=1, padx=(0, 10)
        )  # grid after to avoid chaining and assigning .grid() return of None
        self.combo_box_load_layer["state"] = "readonly"  # make read only

        ttk.Label(
            self.RAM_frame,
            text="Add Custom Loading Layer:",
            font=font.nametofont("TkDefaultFont"),
        ).grid(row=2, column=0, sticky="w")

        ttk.Separator(self.RAM_frame, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew"
        )

        self.transfer_loads_button = Button(
            self.RAM_frame,
            text="Transfer Loads",
            command=self.transfer_loads,
            bg=blue_button_color_code,
            fg=white_color_code,
            state="disabled",
        )
        self.transfer_loads_button.grid(
            row=5,
            column=0,
            columnspan=2,
            rowspan=2,
            padx=20,
            pady=(10, 5),
            sticky="nsew",
        )

        Button(
            self.RAM_frame,
            text="Calibrate",
            command=self.launch_calibrate_window,
            bg=red_button_color_code,
            fg=white_color_code,
        ).grid(row=8, column=0, columnspan=2, padx=(20, 20), pady=(5, 10), sticky="ew")

        ### styling ####
        # Colorize alternating lines of the listbox

    def select_ETABS_model_path(self):
        ETABS_model_path = filedialog.askopenfilename(
            filetypes=[("EDB files", "*.EDB")]
        )
        if ETABS_model_path:
            self.ETABS_model_path = ETABS_model_path
            ETABS_model_name = Path(self.ETABS_model_path).name
            self.ETABS_model_path_label.config(
                text=f'"{ETABS_model_name}"', font=small_italic_font
            )
        self.check_enable_data_button(self.pull_data_button)

    def select_RAM_model_path(self):
        RAM_model_path = filedialog.askopenfilename(filetypes=[("cpt files", "*.cpt")])
        if RAM_model_path:
            self.RAM_model_path = RAM_model_path
            RAM_model_name = Path(self.RAM_model_path).name
            self.RAM_model_path_label.config(
                text=f'"{RAM_model_name}"', font=small_italic_font
            )
        self.check_enable_data_button(self.pull_data_button)

    def analysis_combo_box_handler(self, event):
        """
        Handles selection event vfro combo box and updates the available load cases lsitbox
        """
        selection = self.analysis_combo_box.get()
        self.writeToLog(f"User changed Analysis type to: {selection}")
        self.ETABS_load_cases = find_load_cases_by_type(
            self.SapModel, load_case_type=ETABS_analysis_types_dict[selection]
        )
        self.refresh_list_box(self.l_box, self.load_case_var, self.ETABS_load_cases)
        self.writeToLog(f"Updated Load Case options")

    def pull_model_data(self):
        self.pull_data_button["state"] = "disabled"
        ###### ETABS data extraction/object creation ######

        self.SapModel, self.ETABSObject = initalize_SapModel()
        self.writeToLog(f"Attempting to open ETABS model at: {self.ETABS_model_path}")
        open_ETABS_file(self.SapModel, self.ETABS_model_path)
        self.writeToLog(f"Successfully opened ETABS file")
        self.ETABS_load_cases = find_load_cases_by_type(self.SapModel)
        self.load_case_var.set(self.ETABS_load_cases)

        # stylze list box entries
        self.refresh_list_box(self.l_box, self.load_case_var, self.ETABS_load_cases)
        self.cols_df = find_columns(get_all_frame_elements(self.SapModel))
        self.writeToLog("Accessed ETABS frame elements successfully")
        # populate combo box w levels
        self.ETABS_levels = find_levels(self.cols_df)
        self.combo_box_levels["values"] = self.ETABS_levels

        lb_in_F = 1
        set_units(self.SapModel, unit_enum=lb_in_F)
        self.writeToLog("Set ETABS units to [lb, in]")
        self.writeToLog("Begining ETABS Analysis. This may take a while.")
        self.writeToLog("Program may appear unresponsive")

        self.ETABS_results = run_ETABS_analysis(self.SapModel, self.cols_df)
        self.writeToLog(f"ETABS analysis complete")

        self.ETABS_setup = get_ETABS_results_setup(self.ETABS_results)

        ###### RAM data extraction/object creation ######
        self.writeToLog(f"Begin RAM Initialization and object creation")
        self.concept, self.model, self.cad_manager = start_concept_and_open_model(
            self.RAM_model_path
        )
        self.writeToLog(f"Initialization Successfull")
        set_units_to_US(self.model)
        self.writeToLog("Set RAM units to [lb, in]")
        self.RAM_load_layers = get_all_loading_layers(self.cad_manager)
        self.writeToLog(
            f"Detected the following RAM loading layers: {self.RAM_load_layers}"
        )
        self.combo_box_load_layer["values"] = self.RAM_load_layers

        self.notebook.tab(1, state="normal")

    def launch_calibrate_window(self):
        self.calibrate_win = Toplevel()
        self.calibrate_win.title("Calibrate Coordinates")
        self.coord_entry_dict = {
            "ETABS point 1:": [],
            "RAM point 1:": [],
            "ETABS point 2:": [],
            "RAM point 2:": [],
        }
        cols = 2
        start_row = 1
        start_col = 0
        for i, row in enumerate(self.coord_entry_dict.keys()):
            ttk.Label(self.calibrate_win, text=row).grid(
                row=start_row + i, column=start_col, padx=(10, 0), sticky="w"
            )
            for col in range(cols):
                if col == 1:
                    padx = (0, 10)
                else:
                    padx = 5
                entry = ttk.Entry(self.calibrate_win, width=8)
                entry.grid(row=start_row + i, column=1 + col, padx=padx, pady=5)
                self.coord_entry_dict[row].append(entry)

        top_labels = ["x [in]", "y [in]"]
        for i, label in enumerate(top_labels):
            ttk.Label(self.calibrate_win, text=label).grid(row=0, column=i + 1)

        # pad last column
        last_col = self.calibrate_win.grid_slaves(column=3)

        Button(
            self.calibrate_win,
            text="Calibrate",
            command=self.calibrate_ETABS_to_RAM,
            bg=blue_button_color_code,
            fg=white_color_code,
        ).grid(row=5, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")

    def calibrate_ETABS_to_RAM(self):

        ETABS_pt1 = [
            float(entry.get()) for entry in self.coord_entry_dict["ETABS point 1:"]
        ]
        ETABS_pt2 = [
            float(entry.get()) for entry in self.coord_entry_dict["ETABS point 2:"]
        ]
        RAM_pt1 = [
            float(entry.get()) for entry in self.coord_entry_dict["RAM point 1:"]
        ]
        RAM_pt2 = [
            float(entry.get()) for entry in self.coord_entry_dict["RAM point 2:"]
        ]
        rotation_matrix, delta_translation = calibrate(
            ETABS_pt1, ETABS_pt2, RAM_pt1, RAM_pt2
        )

        self.cols_df[["RAM_X", "RAM_Y"]] = self.cols_df.apply(
            lambda row: pd.Series(
                convert_point_to_new_coord_system(
                    row["Point1X"],
                    row["Point1Y"],
                    rotation_matrix,
                    delta_translation,
                )
            ),
            axis=1,
        )
        self.writeToLog(f"Rotation calibration matrix: {rotation_matrix}")
        self.writeToLog(
            f"Delta translation values; x: {round(delta_translation[0],2)}in, y: {round(delta_translation[1],2)}in"
        )
        self.calibrate_win.destroy()
        self.transfer_loads_button["state"] = "normal"

    def transfer_loads(self):
        # get user inputs
        user_level_selection = self.combo_box_levels.get()
        self.writeToLog(f"User Level Selection: {user_level_selection}")
        user_ETABS_lc_selection = self.get_selected_load_cases()
        self.writeToLog(f"User ETABS Load Case Selection: {user_ETABS_lc_selection}")
        user_RAM_layer_selection = self.load_layers_var.get()
        self.writeToLog(f"RAM load layer: {user_RAM_layer_selection}")

        df_keys = []
        # add axial loads to cols df and save keys in df_keys
        for i, lc in enumerate(user_ETABS_lc_selection):
            change_ETABS_output_case(self.ETABS_setup, lc)
            P_max = find_max_axial(
                self.ETABS_results,
                self.cols_df[self.cols_df["StoryName"] == user_level_selection][
                    "MyNames"
                ].to_list(),
            )
            self.writeToLog(
                f"ETABS LOAD CASE: {lc} Queried ETABS for max axial force lb"
            )
            # add key to df_keys and then map the loads to this key in df
            df_keys.append(f"P_max_{lc}")
            self.cols_df[df_keys[i]] = self.cols_df["MyNames"].map(P_max)

        # handle case where user selects multiple keys
        # add summed loads to df under combined key
        if len(df_keys) > 1:
            user_ETABS_lc_selection.insert(0, "P_max")
            combined_key = "_".join(user_ETABS_lc_selection)
            self.cols_df[combined_key] = self.cols_df[df_keys].sum(axis=1)
            df_keys.append(
                combined_key
            )  # add to df_keys since last key is outputed to RAM
            self.writeToLog(
                f"Summed load for following keys: {df_keys[:-1]} and added to internal df as {combined_key}"
            )

        # filter columns_df for specific story and add to RAM layer
        add_axial_loads_to_loading_layer(
            self.cad_manager,
            user_RAM_layer_selection,
            self.cols_df[self.cols_df["StoryName"] == user_level_selection][
                "RAM_X"
            ].to_list(),
            self.cols_df[self.cols_df["StoryName"] == user_level_selection][
                "RAM_Y"
            ].to_list(),
            self.cols_df[self.cols_df["StoryName"] == user_level_selection][
                df_keys[-1]
            ].to_list(),
        )
        self.writeToLog(
            f"ETABS LOAD CASE: {df_keys[-1]} Successfully added loads to RAM loading layer"
        )

        self.model.save_file(self.RAM_model_path)
        self.writeToLog("Successfully saved updated RAM Model")

    def check_enable_data_button(self, button):
        if self.ETABS_model_path is not None and self.RAM_model_path is not None:
            button["state"] = "normal"

    def refresh_list_box(self, list_box, s_var, new_contents):
        s_var.set(new_contents)
        for i in range(0, len(new_contents), 2):
            list_box.itemconfigure(i, background="#f0f0ff")

    def get_selected_load_cases(self):
        selected_indices = self.l_box.curselection()
        selected_load_cases = [self.l_box.get(i) for i in selected_indices]
        return selected_load_cases

    def writeToLog(self, msg, verbose=True):
        msg = timestamp(msg)
        if verbose:
            print(msg)
        self.log["state"] = "normal"
        if self.log.index("end-1c") != "1.0":
            self.log.insert("end", "\n")
        self.log.insert("end", msg)
        self.log["state"] = "disabled"
        self.log.see("end")  # Auto-scroll to the bottom

    def on_close(self):
        if self.ETABSObject or self.SapModel:
            exit_ETABS(self.ETABSObject)
            clean_up_ETABS(self.ETABSObject, self.SapModel)
        if self.concept:
            self.concept.shut_down()
        self.root.destroy()


def timestamp(msg: str) -> str:
    """
    Appends current date to the prefix string
    """
    date = datetime.now()
    time_stamp = date.strftime("%Y-%m-%d %H:%M:%S")
    return f"{time_stamp}   {msg}"


if __name__ == "__main__":
    root = Tk()
    ETABS_to_RAM_APP(root)
    root.mainloop()
