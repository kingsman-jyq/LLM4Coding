
import os
from PIL import Image, ImageDraw, ImageFont, ExifTags
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
        "top-right": (img_width - text_width - margin, margin),
        "bottom-left": (margin, img_height - text_height - margin),
        "bottom-right": (img_width - text_width - margin, img_height - text_height - margin),
        "center": ((img_width - text_width) / 2, (img_height - text_height) / 2)
    }
    return positions.get(position, positions["bottom-right"])


def add_watermark(image_path, output_dir, font_size, color, position, opacity):
    """Adds a date watermark to an image and saves it."""
    try:
        with Image.open(image_path).convert("RGBA") as img:
            watermark_text = get_exif_date(img)
            if not watermark_text:
                print(f"Skipping {os.path.basename(image_path)}: No EXIF date found.")
                return

            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", size=font_size)
            except IOError:
                font = ImageFont.load_default()
                print("Arial font not found, using default font.")

            text_color = parse_color(color, opacity)
            text_size = draw.textsize(watermark_text, font)
            text_position = get_position(img.size, text_size, position, margin=10)

            draw.text(text_position, watermark_text, font=font, fill=text_color)
            
            # Convert back to RGB before saving to avoid issues with JPEG
            img_rgb = img.convert("RGB")
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, filename)
            img_rgb.save(output_path)
            print(f"Saved watermarked image to: {output_path}")

    except Exception as e:
        print(f"Could not process {os.path.basename(image_path)}: {e}")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("水印应用")
        self.geometry("1024x768")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 左侧控制面板 ---
        self.left_frame = customtkinter.CTkFrame(self, width=300)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")

        # --- 右侧文件列表 ---
        self.right_frame = customtkinter.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)

        # --- 文件选择按钮 ---
        self.select_files_button = customtkinter.CTkButton(self.left_frame, text="选择图片", command=self.select_files)
        self.select_files_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.select_folder_button = customtkinter.CTkButton(self.left_frame, text="选择文件夹", command=self.select_folder)
        self.select_folder_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # --- 输出路径选择 ---
        self.output_dir_button = customtkinter.CTkButton(self.left_frame, text="选择输出文件夹", command=self.select_output_dir)
        self.output_dir_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.output_dir_label = customtkinter.CTkLabel(self.left_frame, text="未选择输出文件夹", wraplength=280)
        self.output_dir_label.grid(row=3, column=0, padx=10, pady=0, sticky="ew")

        # --- 输出格式选择 ---
        self.output_format_label = customtkinter.CTkLabel(self.left_frame, text="输出格式:")
        self.output_format_label.grid(row=4, column=0, padx=10, pady=(20, 0), sticky="w")
        self.output_format_var = customtkinter.StringVar(value="JPEG")
        self.jpeg_radio = customtkinter.CTkRadioButton(self.left_frame, text="JPEG", variable=self.output_format_var, value="JPEG")
        self.jpeg_radio.grid(row=5, column=0, padx=20, pady=10, sticky="w")
        self.png_radio = customtkinter.CTkRadioButton(self.left_frame, text="PNG", variable=self.output_format_var, value="PNG")
        self.png_radio.grid(row=6, column=0, padx=20, pady=0, sticky="w")

        # --- 文件列表 ---
        self.image_list_frame = customtkinter.CTkScrollableFrame(self.right_frame, label_text="已选图片")
        self.image_list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")

        self.image_paths = []
        self.output_dir = ""
        self.thumbnail_images = [] # 必须保留对PhotoImage的引用

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

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="选择文件夹", initialdir="/")
        if not folder_path:
            return
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(folder_path, filename)
                if full_path not in self.image_paths:
                    self.image_paths.append(full_path)
        self.update_image_list()

    def update_image_list(self):
        # 清空旧的缩略图
        for widget in self.image_list_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()

        # 创建新的缩略图列表
        for i, path in enumerate(self.image_paths):
            try:
                img = Image.open(path)
                img.thumbnail((100, 100))
                ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                self.thumbnail_images.append(ctk_img) # 保持引用

                item_frame = customtkinter.CTkFrame(self.image_list_frame)
                item_frame.pack(fill="x", padx=5, pady=5)

                thumb_label = customtkinter.CTkLabel(item_frame, image=ctk_img, text="")
                thumb_label.pack(side="left", padx=5, pady=5)

                filename_label = customtkinter.CTkLabel(item_frame, text=os.path.basename(path), wraplength=450)
                filename_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)

            except Exception as e:
                print(f"无法创建缩略图 {path}: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
