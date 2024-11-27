import customtkinter as ctk
import tkinter as tk
from PIL import ImageGrab, ImageTk, Image
import keyboard
import win32gui
from threading import Thread
import time

class MOGZoomer:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("MOG-ZOOMER")
        self.app.geometry("400x600")
        self.app.configure(fg_color="#1E1E2E")

        # Zoom state
        self.zooming = False
        self.zoom_level = 2.0
        self.zoom_size = 600
        self.follow_cursor = True
        self.quality = "high"
        self.drag_data = {"x": 0, "y": 0}
        self.last_frame_time = 0
        self.frame_interval = 1/60

        # Create zoom window
        self.zoom_window = tk.Toplevel()
        self.zoom_window.overrideredirect(True)
        self.zoom_window.attributes('-topmost', True)
        self.zoom_window.configure(bg='#181825')
        self.zoom_window.withdraw()

        # Create title bar for dragging
        self.title_bar = tk.Frame(self.zoom_window, bg='#313244', height=25)
        self.title_bar.pack(fill='x', side='top')
        
        # Add title text
        title_label = tk.Label(self.title_bar, text="MOG-ZOOMER (Drag here)", bg='#313244', fg='white')
        title_label.pack(side='left', padx=5)
        
        # Bind dragging events
        for widget in (self.title_bar, title_label):
            widget.bind('<Button-1>', self.start_drag)
            widget.bind('<B1-Motion>', self.on_drag)

        # Create canvas
        self.canvas = tk.Canvas(
            self.zoom_window,
            width=self.zoom_size,
            height=self.zoom_size,
            bg='#181825',
            highlightthickness=1,
            highlightbackground="#313244"
        )
        self.canvas.pack(expand=True, fill='both')

        self.create_controls()

        # Start update thread
        self.running = True
        self.update_thread = Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()

        # Bind keyboard shortcut
        keyboard.on_press_key("c", lambda _: self.toggle_zoom())

    def create_controls(self):
        # Main frame
        frame = ctk.CTkFrame(self.app, fg_color="#181825")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title Label
        title_label = ctk.CTkLabel(
            frame,
            text="MOG-ZOOMER",
            text_color="#9D7CD8",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=20)

        # Zoom Level
        ctk.CTkLabel(frame, text="Zoom Level:", text_color="white", font=("Arial", 14)).pack(pady=5)
        self.zoom_slider = ctk.CTkSlider(
            frame,
            from_=1.0,
            to=8.0,
            command=self.update_zoom_level,
            button_color="#9D7CD8",
            progress_color="#9D7CD8"
        )
        self.zoom_slider.set(2.0)
        self.zoom_slider.pack(padx=20, pady=5, fill="x")

        self.zoom_label = ctk.CTkLabel(frame, text="2.0x", text_color="white")
        self.zoom_label.pack(pady=2)

        # Window Size
        ctk.CTkLabel(frame, text="Window Size:", text_color="white", font=("Arial", 14)).pack(pady=5)
        self.size_slider = ctk.CTkSlider(
            frame,
            from_=200,
            to=1000,
            command=self.update_window_size,
            button_color="#9D7CD8",
            progress_color="#9D7CD8"
        )
        self.size_slider.set(self.zoom_size)
        self.size_slider.pack(padx=20, pady=5, fill="x")

        self.size_label = ctk.CTkLabel(frame, text=f"{self.zoom_size}x{self.zoom_size}", text_color="white")
        self.size_label.pack(pady=2)

        # Lock Position Checkbox
        self.follow_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame,
            text="Lock to Cursor (Uncheck to drag)",
            variable=self.follow_var,
            text_color="white",
            fg_color="#9D7CD8",
            hover_color="#B4A0E5"
        ).pack(pady=10)

        # Crosshair Checkbox
        self.crosshair_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame,
            text="Show Crosshair",
            variable=self.crosshair_var,
            text_color="white",
            fg_color="#9D7CD8",
            hover_color="#B4A0E5"
        ).pack(pady=10)

        # Status Label
        self.status_label = ctk.CTkLabel(
            frame,
            text="Press 'C' to toggle zoom",
            text_color="#00FF00",
            font=("Arial", 14, "bold")
        )
        self.status_label.pack(pady=20)

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
            self.status_label.configure(text="Zoom: Active", text_color="#00FF00")
        else:
            self.zoom_window.withdraw()
            self.status_label.configure(text="Zoom: Inactive", text_color="#FF0000")

    def update_loop(self):
        while self.running:
            current_time = time.time()
            
            if current_time - self.last_frame_time >= self.frame_interval and self.zooming:
                try:
                    x, y = win32gui.GetCursorPos()
                    capture_size = int(self.zoom_size / self.zoom_level)
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

                    self.photo = ImageTk.PhotoImage(zoomed)
                    
                    self.canvas.delete("all")
                    self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
                    
                    if self.crosshair_var.get():
                        center = self.zoom_size // 2
                        self.canvas.create_line(center, 0, center, self.zoom_size, fill="red", width=2)
                        self.canvas.create_line(0, center, self.zoom_size, center, fill="red", width=2)

                    if self.follow_var.get():
                        self.zoom_window.geometry(f"{self.zoom_size}x{self.zoom_size + 25}+{x+20}+{y-self.zoom_size//2}")

                    self.last_frame_time = current_time
                    self.zoom_window.update_idletasks()

                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(0.1)

            time.sleep(0.001)

    def run(self):
        try:
            self.app.mainloop()
        finally:
            self.running = False

if __name__ == "__main__":
    app = MOGZoomer()
    app.run()