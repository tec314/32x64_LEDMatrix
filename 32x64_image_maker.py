import tkinter as tk
from tkinter import colorchooser, filedialog
from PIL import Image, ImageDraw, ImageTk
import requests

PIXEL_SIZE = 15
WIDTH = 64
HEIGHT = 32

class PixelEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("64x32 Pixel Editor")

        self.canvas = tk.Canvas(root, width=WIDTH * PIXEL_SIZE, height=HEIGHT * PIXEL_SIZE, bg="black")
        self.canvas.pack()

        self.image = Image.new("RGB", (WIDTH, HEIGHT), "black")
        self.draw = ImageDraw.Draw(self.image)

        self.undo_stack = []
        self.redo_stack = []

        self.current_color = "#FFFFFF"
        self.eraser_mode = False
        self.drawing = False

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-1>", self.start_paint)
        self.canvas.bind("<ButtonRelease-1>", self.end_paint)

        self.temp_image = None
        self.temp_photo = None
        self.temp_image_id = None
        self.temp_pos = [0, 0]
        self.temp_scale = 1.0

        self.build_buttons()
        self.draw_grid()

    def build_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Choose Color", bg="#E0E0E0", command=self.choose_color).pack(side="left", padx=5)
        self.eraser_button = tk.Button(button_frame, text="Use Eraser", bg="#FFCCCC", command=self.toggle_eraser)
        self.eraser_button.pack(side="left", padx=5)
        tk.Button(button_frame, text="Undo", bg="#CCE5FF", command=self.undo).pack(side="left", padx=5)
        tk.Button(button_frame, text="Redo", bg="#CCFFCC", command=self.redo).pack(side="left", padx=5)
        tk.Button(button_frame, text="Load Image", bg="#D9EAD3", command=self.load_image).pack(side="left", padx=5)

        self.apply_button = tk.Button(button_frame, text="Apply Image", bg="#B4A7D6", command=self.apply_image, state="disabled")
        self.apply_button.pack(side="left", padx=5)

        tk.Button(button_frame, text="Zoom +", command=self.zoom_in).pack(side="left", padx=2)
        tk.Button(button_frame, text="Zoom -", command=self.zoom_out).pack(side="left", padx=2)

        self.name_entry = tk.Entry(button_frame, width=20)
        self.name_entry.insert(0, "MyImage")
        self.name_entry.pack(side="left", padx=5)

        self.done_button = tk.Button(button_frame, text="Done", bg="#FFD699", command=self.save_pixels)
        self.done_button.pack(side="left", padx=5)

        self.brightness_scale = tk.Scale(button_frame, from_=0, to=255, orient="horizontal", label="Brightness")
        self.brightness_scale.set(170)  # Default matches ESP32 value
        self.brightness_scale.pack(side="left", padx=5)


    def draw_grid(self):
        for x in range(WIDTH):
            for y in range(HEIGHT):
                x1 = x * PIXEL_SIZE
                y1 = y * PIXEL_SIZE
                x2 = x1 + PIXEL_SIZE
                y2 = y1 + PIXEL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="lightgray", fill="black")

    def choose_color(self):
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code and color_code[1]:
            self.current_color = color_code[1]
            self.eraser_mode = False
            self.eraser_button.config(text="Use Eraser", bg="#FFCCCC")

    def toggle_eraser(self):
        self.eraser_mode = not self.eraser_mode
        if self.eraser_mode:
            self.eraser_button.config(text="Eraser ON", bg="#FF9999")
        else:
            self.eraser_button.config(text="Use Eraser", bg="#FFCCCC")

    def start_paint(self, event):
        if self.temp_image: return
        self.push_undo()
        self.drawing = True
        self.paint(event)

    def end_paint(self, event):
        self.drawing = False

    def paint(self, event):
        if self.temp_image: return
        x = event.x // PIXEL_SIZE
        y = event.y // PIXEL_SIZE
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            color = "#000000" if self.eraser_mode else self.current_color
            self.draw.rectangle([x, y, x, y], fill=color)
            x1 = x * PIXEL_SIZE
            y1 = y * PIXEL_SIZE
            x2 = x1 + PIXEL_SIZE
            y2 = y1 + PIXEL_SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="lightgray")

    def push_undo(self):
        self.undo_stack.append(self.image.copy())
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.image.copy())
            self.image = self.undo_stack.pop()
            self.draw = ImageDraw.Draw(self.image)
            self.redraw_canvas()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.image.copy())
            self.image = self.redo_stack.pop()
            self.draw = ImageDraw.Draw(self.image)
            self.redraw_canvas()

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
        if self.temp_image:
            self.render_temp_image()

    def save_pixels(self):
        name = self.name_entry.get().strip()
        if not name.isidentifier():
            name = "MyImage"

        # Send brightness first
        brightness = self.brightness_scale.get()
        print("Brightness slider: " + str(brightness))
        try:
            response = requests.post("http://172.16.33.33/set_brightness", data=str(brightness), headers={"Content-Type": "text/plain"})
            print("Brightness set:", response.status_code, response.text)
        except Exception as e:
            print("Failed to set brightness:", e)

        # Then send image
        pixel_data = []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = self.image.getpixel((x, y))
                pixel_data.append(bytes([r, g, b]))
        
        flat_data = b"".join(pixel_data)

        try:
            response = requests.post("http://172.16.33.33/upload", data=flat_data)
            print("Upload status:", response.status_code, response.text)
        except Exception as e:
            print("Failed to upload image:", e)

        #self.root.quit()



    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if not file_path:
            return

        self.temp_image = Image.open(file_path).convert("RGBA")
        bg = Image.new("RGBA", self.temp_image.size, (0, 0, 0, 255))  # Black background for transparency
        combined = Image.alpha_composite(bg, self.temp_image)
        self.temp_image = combined.convert("RGB")

        self.temp_scale = 1.0
        self.temp_pos = [0, 0]
        self.render_temp_image()

        self.canvas.bind("<B1-Motion>", self.drag_image)
        self.canvas.bind("<Button-1>", self.start_drag)
        self.apply_button.config(state="normal")
        self.done_button.config(state="disabled")

    def render_temp_image(self):
        if self.temp_image:
            w, h = self.temp_image.size
            scaled = self.temp_image.resize((int(w * self.temp_scale), int(h * self.temp_scale)), Image.Resampling.LANCZOS)
            self.temp_photo = ImageTk.PhotoImage(scaled)
            if self.temp_image_id:
                self.canvas.delete(self.temp_image_id)
            self.temp_image_id = self.canvas.create_image(self.temp_pos[0], self.temp_pos[1], anchor="nw", image=self.temp_photo)

    def start_drag(self, event):
        self.drag_offset = (event.x - self.temp_pos[0], event.y - self.temp_pos[1])

    def drag_image(self, event):
        if self.temp_image:
            self.temp_pos = [event.x - self.drag_offset[0], event.y - self.drag_offset[1]]
            self.render_temp_image()

    def zoom_in(self):
        if self.temp_image:
            self.temp_scale *= 1.1
            self.render_temp_image()

    def zoom_out(self):
        if self.temp_image:
            self.temp_scale *= 0.9
            self.render_temp_image()

    def apply_image(self):
        if self.temp_image:
            scaled = self.temp_image.resize(
                (int(self.temp_image.width * self.temp_scale), int(self.temp_image.height * self.temp_scale)),
                Image.Resampling.LANCZOS
            )

            self.push_undo()
            for y in range(scaled.height):
                for x in range(scaled.width):
                    px, py = self.temp_pos[0] + x, self.temp_pos[1] + y
                    gx, gy = px // PIXEL_SIZE, py // PIXEL_SIZE
                    if 0 <= gx < WIDTH and 0 <= gy < HEIGHT:
                        r, g, b = scaled.getpixel((x, y))
                        self.image.putpixel((gx, gy), (r, g, b))

            self.draw = ImageDraw.Draw(self.image)
            self.temp_image = None
            self.temp_photo = None
            if self.temp_image_id:
                self.canvas.delete(self.temp_image_id)
                self.temp_image_id = None
            self.redraw_canvas()
            self.apply_button.config(state="disabled")

            # UNBIND image drag handlers
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<Button-1>")

            # REBIND drawing handlers
            self.canvas.bind("<B1-Motion>", self.paint)
            self.canvas.bind("<Button-1>", self.start_paint)
            self.canvas.bind("<ButtonRelease-1>", self.end_paint)

            # Enable Done button after image is applied
            self.done_button.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = PixelEditor(root)
    root.mainloop()
