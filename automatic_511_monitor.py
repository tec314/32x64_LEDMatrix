import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageDraw, ImageTk
import requests
import io
import threading

PIXEL_SIZE = 15
WIDTH = 64
HEIGHT = 32

CAM_ORIGINAL_WIDTH = 640
CAM_ORIGINAL_HEIGHT = 480
CAM_DISPLAY_WIDTH = 320
CAM_DISPLAY_HEIGHT = 240

SCALE_X = CAM_ORIGINAL_WIDTH / CAM_DISPLAY_WIDTH
SCALE_Y = CAM_ORIGINAL_HEIGHT / CAM_DISPLAY_HEIGHT

# Simple 5x7 pixel font dictionary (only uppercase letters and digits)
# Each list is 7 rows of 5 bits (1=pixel on, 0=off)
PIXEL_FONT = {
    'A': [
        "010",
        "101",
        "111",
        "101",
        "101",
    ],
    'B': [
        "110",
        "101",
        "110",
        "101",
        "110",
    ],
    'C': [
        "011",
        "100",
        "100",
        "100",
        "011",
    ],
    'D': [
        "110",
        "101",
        "101",
        "101",
        "110",
    ],
    'E': [
        "111",
        "100",
        "110",
        "100",
        "111",
    ],
    'F': [
        "111",
        "100",
        "110",
        "100",
        "100",
    ],
    'G': [
        "0111",
        "1000",
        "1011",
        "1001",
        "0111",
    ],
    'H': [
        "101",
        "101",
        "111",
        "101",
        "101",
    ],
    'I': [
        "111",
        "010",
        "010",
        "010",
        "111",
    ],
    'J': [
        "001",
        "001",
        "001",
        "101",
        "010",
    ],
    'K': [
        "101",
        "110",
        "100",
        "110",
        "101",
    ],
    'L': [
        "100",
        "100",
        "100",
        "100",
        "111",
    ],
    'M': [  # wider, 5x5
        "10001",
        "11011",
        "10101",
        "10001",
        "10001",
    ],
    'N': [  # wider, 5x5
        "10001",
        "11001",
        "10101",
        "10011",
        "10001",
    ],
    'O': [
        "010",
        "101",
        "101",
        "101",
        "010",
    ],
    'P': [
        "110",
        "101",
        "110",
        "100",
        "100",
    ],
    'Q': [
        "010",
        "101",
        "101",
        "011",
        "001",
    ],
    'R': [
        "110",
        "101",
        "110",
        "101",
        "101",
    ],
    'S': [
        "011",
        "100",
        "010",
        "001",
        "110",
    ],
    'T': [
        "111",
        "010",
        "010",
        "010",
        "010",
    ],
    'U': [
        "101",
        "101",
        "101",
        "101",
        "111",
    ],
    'V': [
        "101",
        "101",
        "101",
        "101",
        "010",
    ],
    'W': [
        "10001",
        "10001",
        "10101",
        "11011",
        "10001",
    ],
    'X': [
        "101",
        "101",
        "010",
        "101",
        "101",
    ],
    'Y': [
        "101",
        "101",
        "010",
        "010",
        "010",
    ],
    'Z': [
        "111",
        "001",
        "010",
        "100",
        "111",
    ],
    ' ': [
        "00",
        "00",
        "00",
        "00",
        "00",
    ],
    '!': [
        "1",
        "1",
        "1",
        "0",
        "1",
    ],
    '?': [
        "111",
        "001",
        "011",
        "000",
        "010",
    ],
    '%': [
        "11001",
        "11010",
        "00100",
        "01011",
        "10011",
    ],
    ':': [
        "0",
        "1",
        "0",
        "1",
        "0",
    ],
    '.': [
        "0",
        "0",
        "0",
        "0",
        "1",
    ],
    '0': [
        "010",
        "101",
        "101",
        "101",
        "010",
    ],
    '1': [
        "010",
        "110",
        "010",
        "010",
        "111",
    ],
    '2': [
        "110",
        "001",
        "010",
        "100",
        "111",
    ],
    '3': [
        "110",
        "001",
        "010",
        "001",
        "110",
    ],
    '4': [
        "101",
        "101",
        "111",
        "001",
        "001",
    ],
    '5': [
        "111",
        "100",
        "110",
        "001",
        "110",
    ],
    '6': [
        "011",
        "100",
        "110",
        "101",
        "010",
    ],
    '7': [
        "111",
        "001",
        "010",
        "010",
        "010",
    ],
    '8': [
        "010",
        "101",
        "010",
        "101",
        "010",
    ],
    '9': [
        "010",
        "101",
        "011",
        "001",
        "110",
    ],
}

class TrainMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Train Detection Monitor")

        self.canvas = tk.Canvas(root, width=WIDTH * PIXEL_SIZE, height=HEIGHT * PIXEL_SIZE, bg="black")
        self.canvas.pack()

        self.image = Image.new("RGB", (WIDTH, HEIGHT), "black")
        self.draw = ImageDraw.Draw(self.image)

        self.previous_snapshot = None
        self.monitor_url = "https://www.511pa.com/map/Cctv/5981?t=1752200849"

        self.monitor_pixel = None
        self.reference_color = None
        self.temp_mouse_pos = None

        self.pixel_info = {}  # New dictionary to store pixel metadata

        self.cam_window = tk.Toplevel(self.root)
        self.cam_window.title("Live Camera Feed")

        self.cam_label = tk.Label(self.cam_window)
        self.cam_label.pack()

        self.info_label = tk.Label(self.cam_window, text="Click on the image to select the pixel to monitor")
        self.info_label.pack(pady=5)

        self.status_label = tk.Label(self.cam_window, text="No pixel selected")
        self.status_label.pack(pady=5)

        self.cam_label.bind("<Button-1>", self.set_monitor_pixel)
        self.cam_label.bind("<Motion>", self.track_mouse)

        self.reset_display()
        self.draw_display("PERFORM", 1, 1, (0, 0, 255))
        self.draw_display("PC SETUP", 1, 8, (0, 0, 255))
        self.load_initial_image()
        self.refresh_live_view()

    def reset_display(self):
        self.draw.rectangle([0, 0, WIDTH, HEIGHT], fill="black")

    def draw_display(self, text, xpos, ypos, color=(0,255,0)):
        text = text.upper()

        pixel_scale = 1
        char_width = 5 * pixel_scale

        start_x = xpos
        start_y = ypos

        for char in text:
            bitmap = PIXEL_FONT.get(char, PIXEL_FONT[' '])
            for row_i, row in enumerate(bitmap):
                for col_i, pixel in enumerate(row):
                    if pixel == '1':
                        for dx in range(pixel_scale):
                            for dy in range(pixel_scale):
                                x = start_x + col_i*pixel_scale + dx
                                y = start_y + row_i*pixel_scale + dy
                                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                                    self.image.putpixel((x, y), color)
            start_x += col_i + 2

        self.redraw_canvas()
        self.send_to_led()

    def redraw_canvas(self):
        self.canvas.delete("all")
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = self.image.getpixel((x, y))
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                x1 = x * PIXEL_SIZE
                y1 = y * PIXEL_SIZE
                x2 = x1 + PIXEL_SIZE
                y2 = y1 + PIXEL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=hex_color, outline="lightgray")

    def send_to_led(self):
        pixel_data = []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = self.image.getpixel((x, y))
                pixel_data.append(bytes([r, g, b]))

        flat_data = b"".join(pixel_data)

        try:
            requests.post("http://10.0.0.145/upload", data=flat_data, timeout=2)
        except:
            pass

    def update_cam_window(self, img):
        draw = ImageDraw.Draw(img)

        if self.temp_mouse_pos:
            mx, my = self.temp_mouse_pos
            circle_radius = 5
            left_up = (mx - circle_radius, my - circle_radius)
            right_down = (mx + circle_radius, my + circle_radius)
            draw.ellipse([left_up, right_down], outline="orange", width=2)

        if self.monitor_pixel:
            mx, my = self.monitor_pixel
            circle_radius = 5
            left_up = (mx - circle_radius, my - circle_radius)
            right_down = (mx + circle_radius, my + circle_radius)
            draw.ellipse([left_up, right_down], outline="red", width=2)

        img_resized = img.resize((CAM_DISPLAY_WIDTH, CAM_DISPLAY_HEIGHT), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_resized)
        self.cam_label.configure(image=img_tk)
        self.cam_label.image = img_tk

    def set_monitor_pixel(self, event):
        x = int(event.x)
        y = int(event.y)
        self.monitor_pixel = (x, y)
        self.status_label.config(text=f"Monitoring pixel at ({x}, {y})")

        info = self.get_pixel_info()
        self.pixel_info[self.monitor_pixel] = info

        if self.previous_snapshot:
            self.reference_color = self.previous_snapshot.getpixel(self.monitor_pixel)

        self.reset_display()
        self.draw_display("Monitoring", 1, 1)
        self.monitor_camera()

    def get_pixel_info(self):
        railroad = simpledialog.askstring("Input", "Enter Railroad Name:", parent=self.root)
        camera_name = simpledialog.askstring("Input", "Enter 511PA Camera Name:", parent=self.root)
        milepost = simpledialog.askstring("Input", "Enter Milepost Number:", parent=self.root)
        direction = simpledialog.askstring("Input", "Enter Likely Direction of Travel:", parent=self.root)

        return {
            "railroad": railroad,
            "camera_name": camera_name,
            "milepost": milepost,
            "direction": direction
        }

    def track_mouse(self, event):
        x = int(event.x)
        y = int(event.y)
        self.temp_mouse_pos = (x, y)

    def load_initial_image(self):
        def task():
            try:
                response = requests.get(self.monitor_url, timeout=5)
                cam_image = Image.open(io.BytesIO(response.content)).convert("RGB")
                self.previous_snapshot = cam_image.copy()
                self.update_cam_window(cam_image)
            except Exception as e:
                print("Initial load error:", e)

        threading.Thread(target=task, daemon=True).start()

    def monitor_camera(self):
        def task():
            try:
                response = requests.get(self.monitor_url, timeout=5)
                cam_image = Image.open(io.BytesIO(response.content)).convert("RGB")

                if self.monitor_pixel and self.reference_color:
                    current_color = cam_image.getpixel(self.monitor_pixel)
                    diff = sum(abs(c - r) for c, r in zip(current_color, self.reference_color))

                    if diff > 60:
                        self.reset_display()
                        self.draw_display("TRAIN!", 1, 1, (255, 0, 0))
                    else:
                        self.reset_display()
                        self.draw_display("Monitoring", 1, 1, (0, 255, 0))

                self.previous_snapshot = cam_image.copy()

            except Exception as e:
                print("Monitor error:", e)

        threading.Thread(target=task, daemon=True).start()
        self.root.after(10000, self.monitor_camera)

    def refresh_live_view(self):
        if self.previous_snapshot:
            self.update_cam_window(self.previous_snapshot.copy())
        self.root.after(100, self.refresh_live_view)

if __name__ == "__main__":
    root = tk.Tk()
    app = TrainMonitor(root)
    root.mainloop()