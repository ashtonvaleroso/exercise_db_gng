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
        self.exercise_names = list(self.df['name'])
        self.current_index = 0
        self.fields = {}
        self.selected_exercise = tk.StringVar()
        self.build_ui()
        self.load_exercise()
        self.bind_shortcuts()

    def build_ui(self):
        self.geometry("1920x1080")

        # Layout frames
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill="y", padx=20, pady=20)

        right_frame = tk.Frame(self)
        right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Image panels on the left
        self.image_panel_0 = tk.Label(left_frame)
        self.image_panel_0.pack(side="left", padx=10)

        self.image_panel_1 = tk.Label(left_frame)
        self.image_panel_1.pack(side="left", padx=10)

        # Top bar on the right for dropdown and index
        top_bar = tk.Frame(right_frame)
        top_bar.pack(fill="x", pady=(0, 10))

        self.dropdown = ttk.Combobox(top_bar, textvariable=self.selected_exercise, values=self.exercise_names, state="readonly", width=50)
        self.dropdown.pack(side="left", padx=(0, 10))
        self.dropdown.bind("<<ComboboxSelected>>", self.on_exercise_selected)

        self.index_label = tk.Label(top_bar, text="", font=("Arial", 12))
        self.index_label.pack(side="left")

        # Name entry on top of right side
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(right_frame, textvariable=self.name_var, font=("Arial", 18))
        name_entry.pack(pady=(0, 10), fill="x")
        self.fields['name'] = name_entry

        # All fields stacked vertically
        params = ['force', 'level', 'mechanic', 'equipment', 'primaryMuscles',
                  'secondaryMuscles', 'instructions', 'category', 'volume_multiplier', 'alt_name']
        for param in params:
            field_frame = tk.Frame(right_frame)
            field_frame.pack(fill="x", pady=4)

            label = tk.Label(field_frame, text=param, width=20, anchor="e")
            label.pack(side="left")

            entry = tk.Entry(field_frame, width=50)
            entry.pack(side="left", fill="x", expand=True)
            self.fields[param] = entry

        # Muscle diagram image
        self.diagram_panel = tk.Label(right_frame)
        self.diagram_panel.pack(pady=10)

        # Submit button
        self.submit_btn = tk.Button(right_frame, text="Submit Changes (Ctrl+S)", command=self.submit_changes)
        self.submit_btn.pack(pady=10)

        # Navigation buttons
        nav_frame = tk.Frame(right_frame)
        nav_frame.pack(pady=10)

        tk.Button(nav_frame, text="Previous (Shift+Left)", command=self.prev_exercise).pack(side="left", padx=5)
        tk.Button(nav_frame, text="Next (Shift+Right)", command=self.next_exercise).pack(side="left", padx=5)

    def on_exercise_selected(self, event=None):
        selected_name = self.selected_exercise.get()
        try:
            index = self.exercise_names.index(selected_name)
            self.current_index = index
            self.load_exercise()
        except ValueError:
            messagebox.showerror("Error", f"Exercise '{selected_name}' not found.")

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

        # Update dropdown and index label
        self.selected_exercise.set(row['name'])
        self.index_label.config(text=f"{self.current_index + 1} / {len(self.df)}")

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
        self.exercise_names = list(self.df['name'])
        self.dropdown['values'] = self.exercise_names
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
