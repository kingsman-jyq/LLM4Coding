import os
from PIL import Image, ImageDraw, ImageFont, ExifTags, ImageTk
import customtkinter
from tkinter import filedialog

# A mapping of color names to RGBA values
COLOR_MAP = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
}

def get_exif_date(img):
    """Extracts the original creation date from image EXIF data."""
    try:
        exif_data = img._getexif()
        if not exif_data:
            return None
        for tag, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag, tag)
            if tag_name == 'DateTimeOriginal':
                return value.split(' ')[0].replace(':', '-')
        return None
    except (AttributeError, KeyError, IndexError):
        return None

def parse_color(color_str, opacity):
    """Parses a color string (name or RGB) into an RGBA tuple."""
    color_str = color_str.lower()
    if color_str in COLOR_MAP:
        r, g, b = COLOR_MAP[color_str]
    else:
        try:
            r, g, b = map(int, color_str.split(','))
        except ValueError:
            print(f"Warning: Invalid color '{color_str}'. Defaulting to white.")
            r, g, b = 255, 255, 255
    return (r, g, b, int(255 * (opacity / 100)))

def get_position(img_size, text_size, position, margin):
    """Calculates the (x, y) coordinates for the watermark text."""
    img_width, img_height = img_size
    text_width, text_height = text_size

    positions = {
        "top-left": (margin, margin),
        "top-center": ((img_width - text_width) / 2, margin),
        "top-right": (img_width - text_width - margin, margin),
        "center-left": (margin, (img_height - text_height) / 2),
        "center": ((img_width - text_width) / 2, (img_height - text_height) / 2),
        "center-right": (img_width - text_width - margin, (img_height - text_height) / 2),
        "bottom-left": (margin, img_height - text_height - margin),
        "bottom-center": ((img_width - text_width) / 2, img_height - text_height - margin),
        "bottom-right": (img_width - text_width - margin, img_height - text_height - margin),
    }
    return positions.get(position, positions["bottom-right"])

def generate_watermarked_image(img, watermark_text, font_size, color, position, opacity):
    """Applies a watermark to a PIL Image object and returns a new watermarked image object."""
    base_img = img.copy().convert("RGBA")
    txt_layer = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    try:
        font = ImageFont.truetype("arial.ttf", size=font_size)
    except IOError:
        font = ImageFont.load_default()

    text_color_opaque = parse_color(color, 100)

    try:
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_size = (text_width, text_height)
    except AttributeError:
        text_size = draw.textsize(watermark_text, font)

    text_position = get_position(base_img.size, text_size, position, margin=10)
    draw.text(text_position, watermark_text, font=font, fill=text_color_opaque)

    if opacity < 100:
        alpha = txt_layer.split()[3]
        alpha = alpha.point(lambda p: p * (1.0 - (opacity / 100.0)))
        txt_layer.putalpha(alpha)

    watermarked_img = Image.alpha_composite(base_img, txt_layer)
    return watermarked_img

def add_watermark(image_path, output_dir, watermark_text, font_size, color, position, opacity, output_format):
    """Adds a watermark to an image and saves it."""
    try:
        with Image.open(image_path).convert("RGBA") as img:
            watermarked_img = generate_watermarked_image(img, watermark_text, font_size, color, position, opacity)
            
            save_format = output_format.upper()
            if save_format == 'JPEG':
                watermarked_img = watermarked_img.convert("RGB")
            
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, filename)
            if save_format == 'PNG':
                output_path = os.path.splitext(output_path)[0] + '.png'

            watermarked_img.save(output_path, format=save_format)
            print(f"Saved watermarked image to: {output_path}")

    except Exception as e:
        print(f"Could not process {os.path.basename(image_path)}: {e}")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("水印应用")
        self.geometry("1280x720")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, minsize=350) # Give right frame a minimum width
        self.grid_rowconfigure(0, weight=1)

        # --- 左侧控制面板 ---
        self.left_frame = customtkinter.CTkFrame(self, width=300, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nswe")
        self.left_frame.grid_rowconfigure(10, weight=1)

        # --- 中间预览面板 ---
        self.center_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.center_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)

        # --- 右侧文件列表 ---
        self.right_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.right_frame.grid(row=0, column=2, sticky="nswe")
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # --- 左侧面板控件 (unchanged) ---
        self.select_files_button = customtkinter.CTkButton(self.left_frame, text="选择图片", command=self.select_files)
        self.select_files_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.select_folder_button = customtkinter.CTkButton(self.left_frame, text="选择文件夹", command=self.select_folder)
        self.select_folder_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.output_dir_button = customtkinter.CTkButton(self.left_frame, text="选择输出文件夹", command=self.select_output_dir)
        self.output_dir_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.output_dir_label = customtkinter.CTkLabel(self.left_frame, text="未选择输出文件夹", wraplength=280)
        self.output_dir_label.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        self.output_format_label = customtkinter.CTkLabel(self.left_frame, text="输出格式:")
        self.output_format_label.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="w")
        self.output_format_var = customtkinter.StringVar(value="JPEG")
        self.jpeg_radio = customtkinter.CTkRadioButton(self.left_frame, text="JPEG", variable=self.output_format_var, value="JPEG")
        self.jpeg_radio.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        self.png_radio = customtkinter.CTkRadioButton(self.left_frame, text="PNG", variable=self.output_format_var, value="PNG")
        self.png_radio.grid(row=6, column=0, padx=20, pady=0, sticky="w")
        self.watermark_text_label = customtkinter.CTkLabel(self.left_frame, text="水印文本:")
        self.watermark_text_label.grid(row=7, column=0, padx=10, pady=(20, 0), sticky="w")
        self.watermark_text_var = customtkinter.StringVar(value="Hello World")
        self.watermark_text_var.trace_add("write", self._on_text_change)
        self.watermark_text_entry = customtkinter.CTkEntry(self.left_frame, textvariable=self.watermark_text_var)
        self.watermark_text_entry.grid(row=8, column=0, padx=10, pady=5, sticky="ew")
        self.opacity_label = customtkinter.CTkLabel(self.left_frame, text="透明度: 70%")
        self.opacity_label.grid(row=9, column=0, padx=10, pady=(10, 0), sticky="w")
        self.opacity_var = customtkinter.DoubleVar(value=70)
        self.opacity_slider = customtkinter.CTkSlider(self.left_frame, from_=0, to=100, variable=self.opacity_var, command=self._on_slider_move)
        self.opacity_slider.grid(row=10, column=0, padx=10, pady=5, sticky="ew")
        self.position_label = customtkinter.CTkLabel(self.left_frame, text="位置:")
        self.position_label.grid(row=11, column=0, padx=10, pady=(10, 0), sticky="w")
        self.position_var = customtkinter.StringVar(value="bottom-right")
        position_frame = customtkinter.CTkFrame(self.left_frame)
        position_frame.grid(row=12, column=0, padx=10, pady=5, sticky="ew")
        positions = {
            "top-left": "↖", "top-center": "↑", "top-right": "↗",
            "center-left": "←", "center": "C", "center-right": "→",
            "bottom-left": "↙", "bottom-center": "↓", "bottom-right": "↘"
        }
        for i, (pos_name, pos_char) in enumerate(positions.items()):
            row, col = divmod(i, 3)
            button = customtkinter.CTkButton(position_frame, text=pos_char, width=40, height=40,
                                             command=lambda p=pos_name: self.set_position(p))
            button.grid(row=row, column=col, padx=3, pady=3)

        # --- 中间面板控件 ---
        self.preview_label = customtkinter.CTkLabel(self.center_frame, text="请从右侧列表选择一张图片以预览效果", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nswe")

        # --- 右侧面板控件 ---
        self.image_list_frame = customtkinter.CTkScrollableFrame(self.right_frame, label_text="已选图片")
        self.image_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")

        # --- 状态变量 ---
        self.image_paths = []
        self.output_dir = ""
        self.thumbnail_images = []
        self.selected_image_path = None
        self.preview_image_object = None

    def _on_text_change(self, *args):
        self.update_preview()

    def _on_slider_move(self, value):
        self.opacity_label.configure(text=f"透明度: {int(value)}%")
        self.update_preview()

    def set_position(self, position):
        self.position_var.set(position)
        self.update_preview()

    def select_output_dir(self):
        folder_path = filedialog.askdirectory(title="选择输出文件夹", initialdir="/")
        if folder_path:
            self.output_dir = folder_path
            self.output_dir_label.configure(text=f"输出到:\n{self.output_dir}")

    def select_files(self):
        filetypes = (("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
        filepaths = filedialog.askopenfilenames(title="选择图片", initialdir="/", filetypes=filetypes)
        for path in filepaths:
            if path not in self.image_paths:
                self.image_paths.append(path)
        self.update_image_list()
        if filepaths and not self.selected_image_path:
            self.select_image_for_preview(filepaths[0])

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="选择文件夹", initialdir="/")
        if not folder_path:
            return
        added_paths = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                full_path = os.path.join(folder_path, filename)
                if full_path not in self.image_paths:
                    self.image_paths.append(full_path)
                    added_paths.append(full_path)
        self.update_image_list()
        if added_paths and not self.selected_image_path:
            self.select_image_for_preview(added_paths[0])

    def remove_image(self, path_to_remove):
        self.image_paths.remove(path_to_remove)

        # If the deleted image was the one being previewed, clear the preview.
        if self.selected_image_path == path_to_remove:
            self.clear_preview()

        # Update the visual list of images.
        self.update_image_list()

        # Asynchronously schedule the preview of the next item.
        # This gives the UI time to update before we try to draw a new preview.
        if self.image_paths and not self.selected_image_path:
            self.after(50, lambda: self.select_image_for_preview(self.image_paths[0]))

    def clear_preview(self):
        self.selected_image_path = None
        self.preview_image_object = None
        self.preview_label.configure(image=None, text="请从右侧列表选择一张图片以预览效果")

    def update_image_list(self):
        for widget in self.image_list_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()

        for i, path in enumerate(self.image_paths):
            try:
                # Create a frame for each item
                item_frame = customtkinter.CTkFrame(self.image_list_frame)
                item_frame.pack(fill="x", padx=5, pady=5)
                item_frame.grid_columnconfigure(1, weight=1)

                # Thumbnail
                img = Image.open(path)
                img.thumbnail((60, 60))
                ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                self.thumbnail_images.append(ctk_img)
                
                thumb_label = customtkinter.CTkLabel(item_frame, image=ctk_img, text="")
                thumb_label.grid(row=0, column=0, padx=5, pady=5)
                thumb_label.bind("<Button-1>", lambda e, p=path: self.select_image_for_preview(p))

                # Filename
                filename_label = customtkinter.CTkLabel(item_frame, text=os.path.basename(path), anchor="w")
                filename_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
                filename_label.bind("<Button-1>", lambda e, p=path: self.select_image_for_preview(p))

                # Delete Button
                delete_button = customtkinter.CTkButton(
                    item_frame, text="X", width=30, height=30, 
                    fg_color="transparent", text_color=("gray10", "gray90"),
                    command=lambda p=path: self.remove_image(p)
                )
                delete_button.grid(row=0, column=2, padx=5, pady=5)

            except Exception as e:
                print(f"无法创建缩略图 {path}: {e}")

    def select_image_for_preview(self, path):
        self.selected_image_path = path
        self.update_preview()

    def update_preview(self):
        if not self.selected_image_path:
            self.clear_preview()
            return

        try:
            watermark_text = self.watermark_text_var.get()
            opacity = self.opacity_var.get()
            position = self.position_var.get()
            font_size = 50
            color = "white"

            pil_image = Image.open(self.selected_image_path).convert("RGBA")
            watermarked_pil_image = generate_watermarked_image(pil_image, watermark_text, font_size, color, position, opacity)

            panel_width = self.center_frame.winfo_width()
            panel_height = self.center_frame.winfo_height()
            
            if panel_width < 2 or panel_height < 2:
                self.after(100, self.update_preview)
                return

            img_aspect_ratio = watermarked_pil_image.width / watermarked_pil_image.height
            panel_aspect_ratio = panel_width / panel_height

            if img_aspect_ratio > panel_aspect_ratio:
                new_width = panel_width - 10
                new_height = int(new_width / img_aspect_ratio)
            else:
                new_height = panel_height - 10
                new_width = int(new_height * img_aspect_ratio)

            resized_img = watermarked_pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            ctk_image = customtkinter.CTkImage(light_image=resized_img, dark_image=resized_img, size=(new_width, new_height))
            self.preview_image_object = ctk_image
            self.preview_label.configure(image=ctk_image, text="")

        except Exception as e:
            print(f"无法更新预览: {e}")
            self.preview_label.configure(text=f"无法加载图片:\n{os.path.basename(self.selected_image_path)}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
