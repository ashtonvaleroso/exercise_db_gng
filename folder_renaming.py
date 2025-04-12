from PIL import Image, ImageTk
import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

EXCEL_FILE = "dist/exercises.xlsx"
IMAGE_FOLDER = "exercises"
MUSCLE_DIAGRAM_FOLDER = "muscle_diagram"

def format_folder_name(name):
    name = name.replace("'", "").replace("(", "").replace(")", "").replace("/", "_")
    name = ''.join(c for c in name if c.isalnum() or c in [' ', '_']).replace(" ", "_")
    return name

def parse_muscle_list(text):
    return [m.strip() for m in text.replace('"','').replace('[','').replace(']','').split(',') if m.strip()]

def generate_muscle_diagram(primary_muscles, secondary_muscles):
    base_path = os.path.join(MUSCLE_DIAGRAM_FOLDER, "base.png")
    if not os.path.exists(base_path):
        return None
    base = Image.open(base_path).convert("RGBA")

    def load_overlay(muscle, alpha=255):
        filename = muscle.lower().replace(" ", "_") + ".png"
        path = os.path.join(MUSCLE_DIAGRAM_FOLDER, filename)
        if os.path.exists(path):
            overlay = Image.open(path).convert("RGBA")
            if alpha < 255:
                overlay.putalpha(alpha)
            base.alpha_composite(overlay)

    for muscle in primary_muscles:
        load_overlay(muscle, alpha=255)
    for muscle in secondary_muscles:
        load_overlay(muscle, alpha=128)

    return ImageTk.PhotoImage(base.resize((300, 300)))

class ExerciseEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Exercise Editor")
        self.df = pd.read_excel(EXCEL_FILE)
        self.current_index = 0
        self.fields = {}
        self.build_ui()
        self.load_exercise()
        self.bind_shortcuts()

    def build_ui(self):
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(self, textvariable=self.name_var, font=("Arial", 14))
        name_entry.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        self.fields['name'] = name_entry

        self.image_panel_0 = tk.Label(self)
        self.image_panel_0.grid(row=1, column=0, padx=10, pady=10)
        self.image_panel_1 = tk.Label(self)
        self.image_panel_1.grid(row=1, column=1, padx=10, pady=10)
        self.diagram_panel = tk.Label(self)
        self.diagram_panel.grid(row=2, column=0, columnspan=2)

        params = ['force', 'level', 'mechanic', 'equipment', 'primaryMuscles',
                  'secondaryMuscles', 'instructions', 'category', 'laterality', 'alt_name']
        for i, param in enumerate(params):
            label = tk.Label(self, text=param)
            label.grid(row=i+3, column=0, sticky="e", padx=5)
            entry = tk.Entry(self, width=50)
            entry.grid(row=i+3, column=1, padx=5, pady=2, sticky="w")
            self.fields[param] = entry

        self.submit_btn = tk.Button(self, text="Submit Changes (Ctrl+S)", command=self.submit_changes)
        self.submit_btn.grid(row=14, column=0, columnspan=2, pady=10)

        nav_frame = tk.Frame(self)
        nav_frame.grid(row=15, column=0, columnspan=2, pady=10)
        tk.Button(nav_frame, text="Previous (Shift+Left)", command=self.prev_exercise).pack(side="left", padx=5)
        tk.Button(nav_frame, text="Next (Shift+Right)", command=self.next_exercise).pack(side="left", padx=5)

    def load_exercise(self):
        row = self.df.iloc[self.current_index]
        for key, widget in self.fields.items():
            widget.delete(0, tk.END)
            widget.insert(0, str(row.get(key, "")))

        folder = format_folder_name(row['name'])
        folder_path = os.path.join(IMAGE_FOLDER, folder)
        img0 = self.load_image(os.path.join(folder_path, "0.jpg"))
        img1 = self.load_image(os.path.join(folder_path, "1.jpg"))
        self.image_panel_0.config(image=img0)
        self.image_panel_0.image = img0
        self.image_panel_1.config(image=img1)
        self.image_panel_1.image = img1

        muscles1 = parse_muscle_list(row.get('primaryMuscles', ''))
        muscles2 = parse_muscle_list(row.get('secondaryMuscles', ''))
        diagram = generate_muscle_diagram(muscles1, muscles2)
        if diagram:
            self.diagram_panel.config(image=diagram)
            self.diagram_panel.image = diagram
        else:
            self.diagram_panel.config(image='')

    def load_image(self, path):
        if os.path.exists(path):
            img = Image.open(path)
            img = img.resize((300, 300))
            return ImageTk.PhotoImage(img)
        return None

    def submit_changes(self, auto=False):
        index = self.current_index
        old_excel_name = str(self.df.at[index, "name"])
        old_folder = os.path.join(IMAGE_FOLDER, format_folder_name(old_excel_name))

        for key, entry in self.fields.items():
            self.df.at[index, key] = entry.get()

        new_excel_name = str(self.df.at[index, "name"])
        new_folder = os.path.join(IMAGE_FOLDER, format_folder_name(new_excel_name))

        if new_folder != old_folder and os.path.exists(old_folder):
            try:
                os.rename(old_folder, new_folder)
            except Exception as e:
                messagebox.showerror("Rename Error", f"Could not rename folder:\n{e}")
                return

        self.df.to_excel(EXCEL_FILE, index=False)
        if not auto:
            messagebox.showinfo("Saved", "Changes submitted successfully.")
        self.load_exercise()

    def prev_exercise(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_exercise()

    def next_exercise(self):
        if self.current_index < len(self.df) - 1:
            self.current_index += 1
            self.load_exercise()

    def bind_shortcuts(self):
        self.bind('<Control-s>', lambda e: self.submit_changes())
        self.bind('<Shift-Right>', lambda e: self.next_exercise())
        self.bind('<Shift-Left>', lambda e: self.prev_exercise())

        field_keys = list(self.fields.values())
        def focus_next(event):
            widget = self.focus_get()
            if widget in field_keys:
                i = field_keys.index(widget)
                next_index = (i + 1) % len(field_keys)
                field_keys[next_index].focus_set()
            return "break"

        def focus_prev(event):
            widget = self.focus_get()
            if widget in field_keys:
                i = field_keys.index(widget)
                prev_index = (i - 1) % len(field_keys)
                field_keys[prev_index].focus_set()
            return "break"

        self.bind('<Down>', focus_next)
        self.bind('<Up>', focus_prev)

if __name__ == "__main__":
    app = ExerciseEditor()
    app.mainloop()
