import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab, ImageTk, Image
import keyboard
import win32gui
from threading import Thread, Lock
import time

class MOGZoomer:
    def __init__(self):
        self.app = tk.Tk()
        self.app.title("MOG-ZOOMER v1.1")
        self.app.geometry("420x700")
        self.app.configure(bg="#FFFFFF")
        self.app.resizable(True, True)

        self.zooming = False
        self.zoom_level = 2.0
        self.zoom_size = 400
        self.follow_cursor = True
        self.drag_data = {"x": 0, "y": 0}
        self.last_frame_time = 0
        self.frame_interval = 1/30
        self.current_keybind = "c"
        self.photo = None
        self.current_image = None
        self.image_lock = Lock()

        self.zoom_window = tk.Toplevel()
        self.zoom_window.overrideredirect(True)
        self.zoom_window.attributes('-topmost', True)
        self.zoom_window.configure(bg='#F5F5F5')
        self.zoom_window.withdraw()

        self.title_bar = tk.Frame(self.zoom_window, bg='#E0E0E0', height=25)
        self.title_bar.pack(fill='x', side='top')
        
        title_label = tk.Label(self.title_bar, text="MOG-ZOOMER (Drag here)", bg='#E0E0E0', fg='#000000')
        title_label.pack(side='left', padx=5)
        
        for widget in (self.title_bar, title_label):
            widget.bind('<Button-1>', self.start_drag)
            widget.bind('<B1-Motion>', self.on_drag)

        self.canvas = tk.Canvas(
            self.zoom_window,
            width=self.zoom_size,
            height=self.zoom_size,
            bg='#F5F5F5',
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill='both')
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw")
        self.crosshair_lines = []

        self.create_scrollable_controls()

        self.running = True
        self.update_thread = Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()

        self.set_keybind(self.current_keybind)

    def create_scrollable_controls(self):
        main_frame = tk.Frame(self.app, bg="#FFFFFF")
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        title_label = tk.Label(
            scrollable_frame,
            text="MOG-ZOOMER v1.1",
            fg="#4B6EAF",
            bg="#FFFFFF",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=20)

        creds_label = tk.Label(
            scrollable_frame,
            text="Credits: MOG-Developing\nGitHub: https://github.com/MOG-Developing/MOG-ZOOMER",
            fg="#666666",
            bg="#FFFFFF",
            font=("Arial", 10)
        )
        creds_label.pack(pady=10)

        zoom_frame = tk.LabelFrame(scrollable_frame, text="Zoom Settings", bg="#FFFFFF", fg="#333333", font=("Arial", 11, "bold"), padx=10, pady=10)
        zoom_frame.pack(fill="x", pady=10, ipadx=5, ipady=5)

        tk.Label(zoom_frame, text="Zoom Level:", bg="#FFFFFF", anchor="w").pack(fill="x", pady=(0,5))
        self.zoom_slider = tk.Scale(
            zoom_frame,
            from_=1.0,
            to=8.0,
            resolution=0.1,
            orient="horizontal",
            command=self.update_zoom_level,
            bg="#FFFFFF",
            length=350,
            highlightthickness=0
        )
        self.zoom_slider.set(2.0)
        self.zoom_slider.pack(fill="x", pady=5)

        self.zoom_label = tk.Label(zoom_frame, text="2.0x", bg="#FFFFFF")
        self.zoom_label.pack(anchor="w")

        tk.Label(zoom_frame, text="Window Size:", bg="#FFFFFF", anchor="w").pack(fill="x", pady=(10,5))
        self.size_slider = tk.Scale(
            zoom_frame,
            from_=200,
            to=800,
            orient="horizontal",
            command=self.update_window_size,
            bg="#FFFFFF",
            length=350,
            highlightthickness=0
        )
        self.size_slider.set(self.zoom_size)
        self.size_slider.pack(fill="x", pady=5)

        self.size_label = tk.Label(zoom_frame, text=f"{self.zoom_size}x{self.zoom_size}", bg="#FFFFFF")
        self.size_label.pack(anchor="w")

        settings_frame = tk.LabelFrame(scrollable_frame, text="Settings", bg="#FFFFFF", fg="#333333", font=("Arial", 11, "bold"), padx=10, pady=10)
        settings_frame.pack(fill="x", pady=10, ipadx=5, ipady=5)

        self.follow_var = tk.BooleanVar(value=True)
        follow_cb = tk.Checkbutton(
            settings_frame,
            text="Lock to Cursor (Uncheck to drag manually)",
            variable=self.follow_var,
            bg="#FFFFFF",
            anchor="w",
            highlightthickness=0
        )
        follow_cb.pack(fill="x", pady=5)

        self.crosshair_var = tk.BooleanVar(value=True)
        crosshair_cb = tk.Checkbutton(
            settings_frame,
            text="Show Crosshair",
            variable=self.crosshair_var,
            bg="#FFFFFF",
            anchor="w",
            highlightthickness=0
        )
        crosshair_cb.pack(fill="x", pady=5)

        keybind_frame = tk.Frame(settings_frame, bg="#FFFFFF")
        keybind_frame.pack(fill="x", pady=10)
        
        tk.Label(keybind_frame, text="Activation Keybind:", bg="#FFFFFF", anchor="w").pack(fill="x")
        
        keybind_input_frame = tk.Frame(keybind_frame, bg="#FFFFFF")
        keybind_input_frame.pack(fill="x", pady=5)
        
        tk.Label(keybind_input_frame, text="Key:", bg="#FFFFFF").pack(side="left")
        self.keybind_entry = tk.Entry(keybind_input_frame, width=5, justify="center", highlightthickness=1)
        self.keybind_entry.insert(0, self.current_keybind)
        self.keybind_entry.pack(side="left", padx=5)
        
        self.keybind_status = tk.Label(keybind_input_frame, text="✓ Active", fg="green", bg="#FFFFFF")
        self.keybind_status.pack(side="left", padx=10)
        
        self.keybind_entry.bind('<KeyRelease>', self.validate_keybind)

        self.status_label = tk.Label(
            scrollable_frame,
            text="Press 'C' to toggle zoom",
            fg="#2E8B57",
            bg="#FFFFFF",
            font=("Arial", 12, "bold")
        )
        self.status_label.pack(pady=20)

    def validate_keybind(self, event):
        new_key = self.keybind_entry.get().strip().lower()
        if len(new_key) == 1 and new_key.isprintable():
            old_key = self.current_keybind
            self.current_keybind = new_key
            try:
                self.set_keybind(new_key)
                self.keybind_status.config(text="✓ Active", fg="green")
                self.status_label.config(text=f"Press '{new_key.upper()}' to toggle zoom", fg="#2E8B57")
            except:
                self.current_keybind = old_key
                self.keybind_entry.delete(0, tk.END)
                self.keybind_entry.insert(0, old_key)
                self.keybind_status.config(text="✗ Failed", fg="red")
        elif new_key == "":
            self.keybind_entry.delete(0, tk.END)
            self.keybind_entry.insert(0, self.current_keybind)

    def set_keybind(self, key):
        keyboard.unhook_all()
        keyboard.on_press_key(key, lambda _: self.toggle_zoom())

    def start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag(self, event):
        if not self.follow_var.get():
            x = self.zoom_window.winfo_x() + (event.x - self.drag_data["x"])
            y = self.zoom_window.winfo_y() + (event.y - self.drag_data["y"])
            self.zoom_window.geometry(f"+{x}+{y}")

    def update_zoom_level(self, value):
        self.zoom_level = float(value)
        self.zoom_label.configure(text=f"{self.zoom_level:.1f}x")

    def update_window_size(self, value):
        self.zoom_size = int(value)
        self.size_label.configure(text=f"{self.zoom_size}x{self.zoom_size}")
        self.canvas.configure(width=self.zoom_size, height=self.zoom_size)
        self.zoom_window.geometry(f"{self.zoom_size}x{self.zoom_size + 25}")

    def toggle_zoom(self):
        self.zooming = not self.zooming
        if self.zooming:
            self.zoom_window.deiconify()
            self.status_label.configure(text=f"Zoom: Active (Press '{self.current_keybind.upper()}' to close)", fg="#2E8B57")
        else:
            self.zoom_window.withdraw()
            self.status_label.configure(text=f"Zoom: Inactive (Press '{self.current_keybind.upper()}' to open)", fg="#DC143C")

    def update_crosshair(self):
        for line in self.crosshair_lines:
            self.canvas.delete(line)
        self.crosshair_lines = []
        
        if self.crosshair_var.get() and self.zooming:
            center = self.zoom_size // 2
            self.crosshair_lines.append(
                self.canvas.create_line(center, 0, center, self.zoom_size, fill="red", width=1)
            )
            self.crosshair_lines.append(
                self.canvas.create_line(0, center, self.zoom_size, center, fill="red", width=1)
            )

    def update_loop(self):
        while self.running:
            current_time = time.time()
            if current_time - self.last_frame_time >= self.frame_interval and self.zooming:
                try:
                    x, y = win32gui.GetCursorPos()
                    capture_size = max(10, int(self.zoom_size / self.zoom_level))
                    x1 = x - capture_size // 2
                    y1 = y - capture_size // 2
                    x2 = x1 + capture_size
                    y2 = y1 + capture_size

                    screenshot = ImageGrab.grab(
                        bbox=(x1, y1, x2, y2),
                        include_layered_windows=True,
                        all_screens=True
                    )

                    zoomed = screenshot.resize(
                        (self.zoom_size, self.zoom_size),
                        Image.Resampling.LANCZOS
                    )

                    with self.image_lock:
                        self.current_image = ImageTk.PhotoImage(zoomed)
                        self.canvas.itemconfig(self.canvas_image_id, image=self.current_image)
                    
                    self.update_crosshair()

                    if self.follow_var.get():
                        self.zoom_window.geometry(f"+{x+20}+{y-self.zoom_size//2}")

                    self.last_frame_time = current_time

                except Exception as e:
                    time.sleep(0.01)

            time.sleep(0.001)

    def run(self):
        try:
            self.app.mainloop()
        finally:
            self.running = False

if __name__ == "__main__":
    app = MOGZoomer()
    app.run()