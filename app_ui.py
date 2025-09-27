import os
import json
from PIL import Image, ImageTk
import customtkinter
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from image_processor import generate_watermarked_image, add_watermark, get_position

class App(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("水印应用")
        self.geometry("1280x720")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, minsize=350)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = customtkinter.CTkScrollableFrame(self, label_text="控制面板", width=300, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nswe")

        self.center_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.center_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)

        self.right_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.right_frame.grid(row=0, column=2, sticky="nswe")
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

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

        self.naming_rule_label = customtkinter.CTkLabel(self.left_frame, text="命名规则:")
        self.naming_rule_label.grid(row=13, column=0, padx=10, pady=(20, 0), sticky="w")
        self.naming_rule_var = customtkinter.StringVar(value="原文件名")
        self.naming_rule_options = customtkinter.CTkSegmentedButton(self.left_frame, values=["原文件名", "加前缀", "加后缀"], variable=self.naming_rule_var, command=self.toggle_prefix_suffix_entry)
        self.naming_rule_options.grid(row=14, column=0, padx=10, pady=5, sticky="ew")
        self.prefix_suffix_var = customtkinter.StringVar(value="watermarked_")
        self.prefix_suffix_entry = customtkinter.CTkEntry(self.left_frame, textvariable=self.prefix_suffix_var)

        self.process_button = customtkinter.CTkButton(self.left_frame, text="开始处理", command=self.process_images)
        self.process_button.grid(row=16, column=0, padx=10, pady=(20, 5), sticky="ew")
        self.progressbar = customtkinter.CTkProgressBar(self.left_frame)
        self.progressbar.grid(row=17, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progressbar.set(0)

        self.preview_label = customtkinter.CTkLabel(self.center_frame, text="请从右侧列表选择一张图片以预览效果", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nswe")
        self.preview_label.bind("<ButtonPress-1>", self.on_drag_start)
        self.preview_label.bind("<B1-Motion>", self.on_drag_motion)

        self.image_list_frame = customtkinter.CTkScrollableFrame(self.right_frame, label_text="已选图片")
        self.image_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nswe")

        self.image_paths = []
        self.output_dir = ""
        self.thumbnail_images = []
        self.selected_image_path = None
        self.preview_image_object = None
        self.original_pil_image = None
        self.watermark_text_size = (0, 0)
        self.drag_start_pos = None
        self.drag_start_watermark_pos = None

        self.load_settings()
        self.toggle_prefix_suffix_entry()

    def on_drag_start(self, event):
        if self.preview_image_object:
            self.drag_start_pos = (event.x, event.y)
            current_pos_str = self.position_var.get()
            preview_size = self.preview_image_object.cget("size")
            watermark_pos = get_position(preview_size, self.watermark_text_size, current_pos_str, margin=10)
            self.drag_start_watermark_pos = watermark_pos

    def on_drag_motion(self, event):
        if self.drag_start_pos and self.preview_image_object:
            dx = event.x - self.drag_start_pos[0]
            dy = event.y - self.drag_start_pos[1]
            new_x = self.drag_start_watermark_pos[0] + dx
            new_y = self.drag_start_watermark_pos[1] + dy
            self.position_var.set(f"{new_x},{new_y}")
            self.update_preview()

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
        was_selected = (self.selected_image_path == path_to_remove)
        self.image_paths.remove(path_to_remove)
        self.update_image_list()

        if was_selected:
            if self.image_paths:
                self.select_image_for_preview(self.image_paths[0])
            else:
                self.clear_preview()

    def clear_preview(self):
        self.selected_image_path = None
        self.preview_image_object = None
        self.original_pil_image = None
        self.preview_label.configure(image=None, text="请从右侧列表选择一张图片以预览效果")

    def update_image_list(self):
        for widget in self.image_list_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()

        for i, path in enumerate(self.image_paths):
            try:
                item_frame = customtkinter.CTkFrame(self.image_list_frame)
                item_frame.pack(fill="x", padx=5, pady=5)
                item_frame.grid_columnconfigure(1, weight=1)

                img = Image.open(path)
                img.thumbnail((60, 60))
                ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                self.thumbnail_images.append(ctk_img)
                
                thumb_label = customtkinter.CTkLabel(item_frame, image=ctk_img, text="")
                thumb_label.grid(row=0, column=0, padx=5, pady=5)
                thumb_label.bind("<Button-1>", lambda e, p=path: self.select_image_for_preview(p))

                filename_label = customtkinter.CTkLabel(item_frame, text=os.path.basename(path), anchor="w")
                filename_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
                filename_label.bind("<Button-1>", lambda e, p=path: self.select_image_for_preview(p))

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
        self.original_pil_image = None # Reset to force reload
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

            if self.original_pil_image is None:
                self.original_pil_image = Image.open(self.selected_image_path).convert("RGBA")

            final_position_str = position
            if ',' in position:
                if self.preview_image_object:
                    preview_size = self.preview_image_object.cget("size")
                    original_size = self.original_pil_image.size
                    try:
                        preview_x, preview_y = map(float, position.split(','))
                        scale_x = original_size[0] / preview_size[0]
                        scale_y = original_size[1] / preview_size[1]
                        original_x = int(preview_x * scale_x)
                        original_y = int(preview_y * scale_y)
                        final_position_str = f"{original_x},{original_y}"
                    except (ValueError, ZeroDivisionError):
                        final_position_str = "bottom-right"
                else:
                    final_position_str = "bottom-right"

            watermarked_pil_image, text_size = generate_watermarked_image(
                self.original_pil_image, watermark_text, font_size, color, final_position_str, opacity
            )

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

            original_text_w, original_text_h = text_size
            if self.original_pil_image.width > 0 and self.original_pil_image.height > 0:
                scale_w = new_width / self.original_pil_image.width
                scale_h = new_height / self.original_pil_image.height
                self.watermark_text_size = (int(original_text_w * scale_w), int(original_text_h * scale_h))

        except Exception as e:
            print(f"无法更新预览: {e}")

    def handle_drop(self, event):
        filepaths = self.tk.splitlist(event.data)
        added_paths = []
        for path in filepaths:
            if path.lower().endswith((".png", ".jpg", ".jpeg")) and path not in self.image_paths:
                self.image_paths.append(path)
                added_paths.append(path)
        
        if added_paths:
            self.update_image_list()
            if not self.selected_image_path:
                self.select_image_for_preview(added_paths[0])

    def toggle_prefix_suffix_entry(self, value=None):
        if self.naming_rule_var.get() in ["加前缀", "加后缀"]:
            self.prefix_suffix_entry.grid(row=15, column=0, padx=10, pady=5, sticky="ew")
        else:
            self.prefix_suffix_entry.grid_forget()

    def process_images(self):
        if not self.output_dir:
            messagebox.showerror("错误", "请先选择一个输出文件夹。" )
            return
        if not self.image_paths:
            messagebox.showerror("错误", "列表中没有需要处理的图片。" )
            return

        watermark_text = self.watermark_text_var.get()
        opacity = self.opacity_var.get()
        position = self.position_var.get()
        font_size = 50
        color = "white"
        output_format = self.output_format_var.get()
        naming_rule = self.naming_rule_var.get()
        prefix_suffix = self.prefix_suffix_var.get()

        total_images = len(self.image_paths)
        self.progressbar.set(0)

        for i, image_path in enumerate(self.image_paths):
            final_position_str = position
            if ',' in position:
                try:
                    preview_x, preview_y = map(float, position.split(','))
                    with Image.open(self.selected_image_path) as preview_img, Image.open(image_path) as target_img:
                        preview_size = preview_img.size
                        target_size = target_img.size
                    scale_x = target_size[0] / preview_size[0]
                    scale_y = target_size[1] / preview_size[1]
                    original_x = int(preview_x * scale_x)
                    original_y = int(preview_y * scale_y)
                    final_position_str = f"{original_x},{original_y}"
                except Exception as e:
                    print(f"Could not scale position for {os.path.basename(image_path)}: {e}")
                    final_position_str = "bottom-right"

            base, ext = os.path.splitext(os.path.basename(image_path))
            
            if naming_rule == "加前缀":
                new_name = f"{prefix_suffix}{base}{ext}"
            elif naming_rule == "加后缀":
                new_name = f"{base}{prefix_suffix}{ext}"
            else:
                new_name = f"{base}{ext}"

            if output_format.upper() == 'PNG':
                new_name = f"{os.path.splitext(new_name)[0]}.png"
            else:
                new_name = f"{os.path.splitext(new_name)[0]}.jpg"

            output_path = os.path.join(self.output_dir, new_name)

            add_watermark(
                image_path, output_path, watermark_text, font_size, color,
                final_position_str, opacity, output_format
            )
            
            progress = (i + 1) / total_images
            self.progressbar.set(progress)
            self.update_idletasks()

        self.progressbar.set(1)
        messagebox.showinfo("处理完成", f"成功为 {total_images} 张图片添加了水印！")
        self.progressbar.set(0)

    def on_closing(self):
        self.save_settings()
        self.destroy()

    def save_settings(self):
        settings = {
            "output_dir": self.output_dir,
            "output_format": self.output_format_var.get(),
            "watermark_text": self.watermark_text_var.get(),
            "opacity": self.opacity_var.get(),
            "position": self.position_var.get(),
            "naming_rule": self.naming_rule_var.get(),
            "prefix_suffix": self.prefix_suffix_var.get(),
        }
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    
                    self.output_dir = settings.get("output_dir", "")
                    self.output_format_var.set(settings.get("output_format", "JPEG"))
                    self.watermark_text_var.set(settings.get("watermark_text", "Hello World"))
                    self.opacity_var.set(settings.get("opacity", 70))
                    self.position_var.set(settings.get("position", "bottom-right"))
                    self.naming_rule_var.set(settings.get("naming_rule", "原文件名"))
                    self.prefix_suffix_var.set(settings.get("prefix_suffix", "watermarked_"))

                    if self.output_dir:
                        self.output_dir_label.configure(text=f"输出到:\n{self.output_dir}")
                    self.opacity_label.configure(text=f"透明度: {int(self.opacity_var.get())}%")
        except Exception as e:
            print(f"Error loading settings: {e}")
