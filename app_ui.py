import os
import json
from PIL import Image, ImageTk
import customtkinter
from tkinter import filedialog, messagebox, colorchooser
from tkinterdnd2 import DND_FILES, TkinterDnD
from image_processor import generate_watermarked_image, add_watermark, get_position, generate_image_watermarked_image

class App(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("水印应用")
        self.geometry("1280x720")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Configure main window grid ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1) # Make preview area scalable

        # --- Create Frames ---
        self.left_frame = customtkinter.CTkScrollableFrame(self, label_text="文件与输出", width=350, corner_radius=0)
        self.left_frame.grid(row=0, column=0, rowspan=2, sticky="nswe")

        self.right_frame = customtkinter.CTkScrollableFrame(self, label_text="已选图片", corner_radius=0)
        self.right_frame.grid(row=0, column=2, rowspan=2, sticky="nswe")
        self.right_frame.grid_columnconfigure(0, weight=1)

        top_controls_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        top_controls_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(10, 0))
        top_controls_frame.grid_columnconfigure(1, weight=1)

        self.preview_label = customtkinter.CTkLabel(self, text="请从右侧列表选择一张图片以预览效果", anchor="center")
        self.preview_label.grid(row=1, column=1, sticky="nswe", padx=10, pady=10)
        
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)
        self.preview_label.bind("<Configure>", self.on_preview_resize)
        self.preview_label.bind("<ButtonPress-1>", self.on_drag_start)
        self.preview_label.bind("<B1-Motion>", self.on_drag_motion)

        # --- Variables ---
        self.output_format_var = customtkinter.StringVar(value="JPEG")
        self.watermark_text_var = customtkinter.StringVar(value="Hello World")
        self.font_name_var = customtkinter.StringVar(value="arial")
        self.font_size_var = customtkinter.StringVar(value="50")
        self.font_color_var = customtkinter.StringVar(value="white")
        self.is_bold_var = customtkinter.BooleanVar(value=False)
        self.is_italic_var = customtkinter.BooleanVar(value=False)
        self.opacity_var = customtkinter.DoubleVar(value=70)
        self.position_var = customtkinter.StringVar(value="bottom-right")
        self.naming_rule_var = customtkinter.StringVar(value="原文件名")
        self.prefix_suffix_var = customtkinter.StringVar(value="watermarked_")
        self.shadow_enabled_var = customtkinter.BooleanVar(value=False)
        self.shadow_color_var = customtkinter.StringVar(value="black")
        self.jpeg_quality_var = customtkinter.IntVar(value=95)
        self.resize_enabled_var = customtkinter.BooleanVar(value=False)
        self.output_width_var = customtkinter.StringVar()
        self.output_height_var = customtkinter.StringVar()

        # --- Watermark Variables ---
        self.watermark_type_var = customtkinter.StringVar(value="文本")
        self.image_watermark_path_var = customtkinter.StringVar()
        self.image_watermark_scale_var = customtkinter.DoubleVar(value=50)
        self.image_watermark_opacity_var = customtkinter.DoubleVar(value=70)
        self.rotation_var = customtkinter.DoubleVar(value=0)

        # --- Template Variables ---
        self.template_var = customtkinter.StringVar(value="")
        self.templates = []

        # --- Left Frame Widgets ---
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
        self.jpeg_radio = customtkinter.CTkRadioButton(self.left_frame, text="JPEG", variable=self.output_format_var, value="JPEG", command=self._toggle_jpeg_quality_slider)
        self.jpeg_radio.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        self.png_radio = customtkinter.CTkRadioButton(self.left_frame, text="PNG", variable=self.output_format_var, value="PNG", command=self._toggle_jpeg_quality_slider)
        self.png_radio.grid(row=6, column=0, padx=20, pady=0, sticky="w")

        self.jpeg_quality_label = customtkinter.CTkLabel(self.left_frame, text="JPEG 质量: 95%")
        self.jpeg_quality_label.grid(row=7, column=0, padx=10, pady=(10, 0), sticky="w")
        self.jpeg_quality_slider = customtkinter.CTkSlider(self.left_frame, from_=1, to=100, variable=self.jpeg_quality_var, command=self._on_jpeg_quality_change)
        self.jpeg_quality_slider.grid(row=8, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.naming_rule_label = customtkinter.CTkLabel(self.left_frame, text="命名规则:")
        self.naming_rule_label.grid(row=9, column=0, padx=10, pady=(20, 0), sticky="w")
        self.naming_rule_options = customtkinter.CTkSegmentedButton(self.left_frame, values=["原文件名", "加前缀", "加后缀"], variable=self.naming_rule_var, command=self.toggle_prefix_suffix_entry)
        self.naming_rule_options.grid(row=10, column=0, padx=10, pady=5, sticky="ew")
        self.prefix_suffix_entry = customtkinter.CTkEntry(self.left_frame, textvariable=self.prefix_suffix_var)

        # --- Resize Controls ---
        self.resize_checkbox = customtkinter.CTkCheckBox(self.left_frame, text="调整输出尺寸", variable=self.resize_enabled_var, command=self._toggle_resize_entries)
        self.resize_checkbox.grid(row=11, column=0, padx=10, pady=(20, 5), sticky="w")

        self.resize_frame = customtkinter.CTkFrame(self.left_frame, fg_color="transparent")
        self.resize_frame.grid(row=12, column=0, padx=5, pady=0, sticky="ew")
        self.resize_frame.grid_columnconfigure(1, weight=1)

        self.width_label = customtkinter.CTkLabel(self.resize_frame, text="宽:")
        self.width_label.grid(row=0, column=0, padx=(5, 2), pady=2)
        self.width_entry = customtkinter.CTkEntry(self.resize_frame, textvariable=self.output_width_var)
        self.width_entry.grid(row=0, column=1, padx=(0, 5), pady=2, sticky="ew")

        self.height_label = customtkinter.CTkLabel(self.resize_frame, text="高:")
        self.height_label.grid(row=1, column=0, padx=(5, 2), pady=2)
        self.height_entry = customtkinter.CTkEntry(self.resize_frame, textvariable=self.output_height_var)
        self.height_entry.grid(row=1, column=1, padx=(0, 5), pady=2, sticky="ew")

        self.process_button = customtkinter.CTkButton(self.left_frame, text="开始处理", command=self.process_images)
        self.process_button.grid(row=13, column=0, padx=10, pady=(20, 5), sticky="ew")

        # --- Template Controls ---
        template_frame = customtkinter.CTkFrame(self.left_frame)
        template_frame.grid(row=14, column=0, padx=10, pady=(20, 0), sticky="ew")
        template_frame.grid_columnconfigure(0, weight=1)

        self.template_label = customtkinter.CTkLabel(template_frame, text="水印模板:")
        self.template_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="w")
        self.template_menu = customtkinter.CTkOptionMenu(template_frame, variable=self.template_var, command=self.load_template)
        self.template_menu.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.save_template_button = customtkinter.CTkButton(template_frame, text="保存模板", command=self.save_template)
        self.save_template_button.grid(row=2, column=0, padx=(10, 5), pady=5, sticky="ew")
        self.delete_template_button = customtkinter.CTkButton(template_frame, text="删除模板", command=self.delete_template)
        self.delete_template_button.grid(row=2, column=1, padx=(5, 10), pady=5, sticky="ew")

        self.progressbar = customtkinter.CTkProgressBar(self.left_frame)
        self.progressbar.grid(row=15, column=0, padx=10, pady=(20, 10), sticky="ew")
        self.progressbar.set(0)

        # --- Top Controls Widgets ---
        self.watermark_type_switcher = customtkinter.CTkSegmentedButton(top_controls_frame, values=["文本", "图片"], variable=self.watermark_type_var, command=self._switch_watermark_type)
        self.watermark_type_switcher.grid(row=0, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")

        # --- Text Watermark Frame ---
        self.text_watermark_frame = customtkinter.CTkFrame(top_controls_frame, fg_color="transparent")
        self.text_watermark_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.text_watermark_frame.grid_columnconfigure(1, weight=1)

        # --- Image Watermark Frame ---
        self.image_watermark_frame = customtkinter.CTkFrame(top_controls_frame, fg_color="transparent")
        self.image_watermark_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.image_watermark_frame.grid_columnconfigure(1, weight=1)

        # --- Text Watermark Controls ---
        # Row 0: Text
        self.watermark_text_label = customtkinter.CTkLabel(self.text_watermark_frame, text="水印文本:")
        self.watermark_text_label.grid(row=0, column=0, padx=(10, 5), pady=5)
        self.watermark_text_entry = customtkinter.CTkEntry(self.text_watermark_frame, textvariable=self.watermark_text_var)
        self.watermark_text_entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")
        self.watermark_text_var.trace_add("write", self._on_text_change)

        # Row 1: Font
        font_frame = customtkinter.CTkFrame(self.text_watermark_frame, fg_color="transparent")
        font_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        font_frame.grid_columnconfigure(1, weight=1)
        self.font_name_label = customtkinter.CTkLabel(font_frame, text="字体:")
        self.font_name_label.grid(row=0, column=0, padx=(0, 5))
        self.font_name_menu = customtkinter.CTkOptionMenu(font_frame, variable=self.font_name_var, values=["arial", "times", "cour"], command=lambda _: self.update_preview())
        self.font_name_menu.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        self.font_size_label = customtkinter.CTkLabel(font_frame, text="字号:")
        self.font_size_label.grid(row=0, column=2, padx=(10, 5))
        self.font_size_entry = customtkinter.CTkEntry(font_frame, textvariable=self.font_size_var, width=50)
        self.font_size_entry.grid(row=0, column=3, padx=(0, 10))
        self.font_size_var.trace_add("write", self._on_text_change)
        self.font_color_button = customtkinter.CTkButton(font_frame, text="颜色", width=50, command=self.select_font_color)
        self.font_color_button.grid(row=0, column=4, padx=(10, 5))
        self.font_color_label = customtkinter.CTkLabel(font_frame, text=self.font_color_var.get(), width=60)
        self.font_color_label.grid(row=0, column=5, padx=(0, 10))
        self.bold_checkbox = customtkinter.CTkCheckBox(font_frame, text="粗体", variable=self.is_bold_var, command=self.update_preview)
        self.bold_checkbox.grid(row=0, column=6, padx=10)
        self.italic_checkbox = customtkinter.CTkCheckBox(font_frame, text="斜体", variable=self.is_italic_var, command=self.update_preview)
        self.italic_checkbox.grid(row=0, column=7, padx=10)

        # Row 2: Effects
        effects_frame = customtkinter.CTkFrame(self.text_watermark_frame, fg_color="transparent")
        effects_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        effects_frame.grid_columnconfigure(1, weight=1)
        self.opacity_label = customtkinter.CTkLabel(effects_frame, text="透明度: 70%")
        self.opacity_label.grid(row=0, column=0, padx=(0, 5))
        self.opacity_slider = customtkinter.CTkSlider(effects_frame, from_=0, to=100, variable=self.opacity_var, command=self._on_slider_move)
        self.opacity_slider.grid(row=0, column=1, sticky="ew")
        self.shadow_checkbox = customtkinter.CTkCheckBox(effects_frame, text="阴影", variable=self.shadow_enabled_var, command=self.update_preview)
        self.shadow_checkbox.grid(row=0, column=2, padx=(10, 5))
        self.shadow_color_button = customtkinter.CTkButton(effects_frame, text="阴影颜色", width=80, command=self.select_shadow_color)
        self.shadow_color_button.grid(row=0, column=3, padx=(0, 5))
        self.shadow_color_label = customtkinter.CTkLabel(effects_frame, text=self.shadow_color_var.get(), width=60)
        self.shadow_color_label.grid(row=0, column=4, padx=(0, 10))

        # --- Position and Rotation Controls (Shared) ---
        position_rotation_frame = customtkinter.CTkFrame(top_controls_frame)
        position_rotation_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        position_rotation_frame.grid_columnconfigure(3, weight=1)

        position_label = customtkinter.CTkLabel(position_rotation_frame, text="位置:")
        position_label.grid(row=0, column=0, padx=(10, 5), pady=5)

        position_frame = customtkinter.CTkFrame(position_rotation_frame)
        position_frame.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="w")

        rotation_label = customtkinter.CTkLabel(position_rotation_frame, text="旋转:")
        rotation_label.grid(row=0, column=2, padx=(20, 5), pady=5)
        self.rotation_slider = customtkinter.CTkSlider(position_rotation_frame, from_=0, to=360, variable=self.rotation_var, command=self._on_rotation_change)
        self.rotation_slider.grid(row=0, column=3, padx=(0, 10), pady=5, sticky="ew")

        self.rotation_value_label = customtkinter.CTkLabel(position_rotation_frame, text="0°", width=40)
        self.rotation_value_label.grid(row=0, column=4, padx=(5, 10), pady=5)

        # --- Image Watermark Controls ---
        self.select_image_wm_button = customtkinter.CTkButton(self.image_watermark_frame, text="选择水印图片", command=self.select_image_watermark)
        self.select_image_wm_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.image_wm_path_label = customtkinter.CTkLabel(self.image_watermark_frame, text="未选择图片", wraplength=280)
        self.image_wm_path_label.grid(row=1, column=0, columnspan=2, padx=10, pady=0, sticky="ew")

        self.image_wm_scale_label = customtkinter.CTkLabel(self.image_watermark_frame, text="缩放: 50%")
        self.image_wm_scale_label.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        self.image_wm_scale_slider = customtkinter.CTkSlider(self.image_watermark_frame, from_=1, to=200, variable=self.image_watermark_scale_var, command=self._on_image_scale_change)
        self.image_wm_scale_slider.grid(row=2, column=1, padx=10, pady=(10, 0), sticky="ew")

        self.image_wm_opacity_label = customtkinter.CTkLabel(self.image_watermark_frame, text="透明度: 70%")
        self.image_wm_opacity_label.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")
        self.image_wm_opacity_slider = customtkinter.CTkSlider(self.image_watermark_frame, from_=0, to=100, variable=self.image_watermark_opacity_var, command=self._on_image_opacity_change)
        self.image_wm_opacity_slider.grid(row=3, column=1, padx=10, pady=(10, 0), sticky="ew")
        positions = {
            "top-left": "↖", "top-center": "↑", "top-right": "↗",
            "center-left": "←", "center": "C", "center-right": "→",
            "bottom-left": "↙", "bottom-center": "↓", "bottom-right": "↘"
        }
        for i, (pos_name, pos_char) in enumerate(positions.items()):
            row, col = divmod(i, 3)
            button = customtkinter.CTkButton(position_frame, text=pos_char, width=30, height=30, command=lambda p=pos_name: self.set_position(p))
            button.grid(row=row, column=col, padx=2, pady=2)

        # --- Instance Variables ---
        self.image_paths = []
        self.output_dir = ""
        self.thumbnail_images = []
        self.selected_image_path = None
        self.preview_image_object = None
        self.original_pil_image = None
        self.watermark_original_size = (0, 0)
        self.preview_watermark_size = (0, 0)
        self.drag_start_pos = None
        self.drag_start_watermark_pos = None

        self.load_settings()
        self.toggle_prefix_suffix_entry()
        self._toggle_jpeg_quality_slider()
        self._toggle_resize_entries()
        self._switch_watermark_type(self.watermark_type_var.get())
        self.update_template_menu()

    def _on_jpeg_quality_change(self, value):
        self.jpeg_quality_label.configure(text=f"JPEG 质量: {int(value)}%")

    def _toggle_jpeg_quality_slider(self):
        if self.output_format_var.get() == "JPEG":
            self.jpeg_quality_label.grid(row=7, column=0, padx=10, pady=(10, 0), sticky="w")
            self.jpeg_quality_slider.grid(row=8, column=0, padx=10, pady=(0, 10), sticky="ew")
        else:
            self.jpeg_quality_label.grid_forget()
            self.jpeg_quality_slider.grid_forget()

    def _toggle_resize_entries(self):
        if self.resize_enabled_var.get():
            self.resize_frame.grid(row=12, column=0, padx=5, pady=0, sticky="ew")
        else:
            self.resize_frame.grid_forget()

    def select_image_watermark(self):
        filepath = filedialog.askopenfilename(title="选择水印图片", filetypes=(("PNG files", "*.png"), ("All files", "*.*")))
        if filepath:
            self.image_watermark_path_var.set(filepath)
            self.image_wm_path_label.configure(text=os.path.basename(filepath))
            self.update_preview()

    def _on_image_scale_change(self, value):
        self.image_wm_scale_label.configure(text=f"缩放: {int(value)}%")
        self.update_preview()

    def _on_image_opacity_change(self, value):
        self.image_wm_opacity_label.configure(text=f"透明度: {int(value)}%")
        self.update_preview()

    def _on_rotation_change(self, value):
        self.rotation_value_label.configure(text=f"{int(value)}°")
        self.update_preview()

    def _switch_watermark_type(self, value):
        if value == "文本":
            self.image_watermark_frame.grid_forget()
            self.text_watermark_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        else:
            self.text_watermark_frame.grid_forget()
            self.image_watermark_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.update_preview()

    def on_preview_resize(self, event):
        self.update_preview()

    def select_shadow_color(self):
        color_code = colorchooser.askcolor(title="Choose shadow color")
        if color_code and color_code[1]:
            self.shadow_color_var.set(color_code[1])
            self.shadow_color_label.configure(text=color_code[1])
            self.update_preview()

    def select_font_color(self):
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code and color_code[1]:
            self.font_color_var.set(color_code[1])
            self.font_color_label.configure(text=color_code[1])
            self.update_preview()

    def on_drag_start(self, event):
        if self.preview_image_object:
            self.drag_start_pos = (event.x, event.y)
            current_pos_str = self.position_var.get()
            preview_size = self.preview_image_object.cget("size")
            watermark_pos = get_position(preview_size, self.preview_watermark_size, current_pos_str, margin=10)
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
        filetypes = (("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("All files", "*.*"))
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
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
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
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()

        for i, path in enumerate(self.image_paths):
            try:
                item_frame = customtkinter.CTkFrame(self.right_frame)
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

    def update_preview_panel(self, watermarked_pil_image):
        panel_width = self.preview_label.winfo_width()
        panel_height = self.preview_label.winfo_height()
        
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

        # Update watermark size for drag-and-drop based on preview scaling
        if self.watermark_original_size[0] > 0 and self.original_pil_image.width > 0:
            scale_w = new_width / self.original_pil_image.width
            self.preview_watermark_size = (int(self.watermark_original_size[0] * scale_w), int(self.watermark_original_size[1] * scale_w))
        else:
            self.preview_watermark_size = (0, 0)

    def update_preview(self):
        if not self.selected_image_path:
            self.clear_preview()
            return

        try:
            if self.original_pil_image is None:
                self.original_pil_image = Image.open(self.selected_image_path).convert("RGBA")

            watermark_type = self.watermark_type_var.get()
            position = self.position_var.get()
            rotation = self.rotation_var.get()

            if watermark_type == "文本":
                watermark_text = self.watermark_text_var.get()
                opacity = self.opacity_var.get()
                font_name = self.font_name_var.get()
                try:
                    font_size = int(self.font_size_var.get())
                except (ValueError, TypeError):
                    font_size = 50 # Default size if input is invalid
                color = self.font_color_var.get()
                is_bold = self.is_bold_var.get()
                is_italic = self.is_italic_var.get()
                shadow_enabled = self.shadow_enabled_var.get()
                shadow_color = self.shadow_color_var.get()

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
                    self.original_pil_image, watermark_text, font_size, color, final_position_str, opacity, font_name,
                    is_bold=is_bold, is_italic=is_italic, shadow_enabled=shadow_enabled, shadow_color=shadow_color, rotation=rotation
                )
                self.watermark_original_size = text_size
            else: # Image watermark
                image_wm_path = self.image_watermark_path_var.get()
                if not image_wm_path or not os.path.exists(image_wm_path):
                    self.update_preview_panel(self.original_pil_image)
                    return
                
                scale = self.image_watermark_scale_var.get()
                opacity = self.image_watermark_opacity_var.get()

                watermarked_pil_image, wm_size = generate_image_watermarked_image(
                    self.original_pil_image, image_wm_path, scale, opacity, position, rotation
                )
                self.watermark_original_size = wm_size # Reuse for drag-and-drop

            self.update_preview_panel(watermarked_pil_image)

        except Exception as e:
            print(f"无法更新预览: {e}")

    def handle_drop(self, event):
        filepaths = self.tk.splitlist(event.data)
        added_paths = []
        for path in filepaths:
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")) and path not in self.image_paths:
                self.image_paths.append(path)
                added_paths.append(path)
        
        if added_paths:
            self.update_image_list()
            if not self.selected_image_path:
                self.select_image_for_preview(added_paths[0])

    def toggle_prefix_suffix_entry(self, value=None):
        if self.naming_rule_var.get() in ["加前缀", "加后缀"]:
            self.prefix_suffix_entry.grid(row=18, column=0, padx=10, pady=5, sticky="ew")
        else:
            self.prefix_suffix_entry.grid_forget()

    def process_images(self):
        if not self.output_dir:
            messagebox.showerror("错误", "请先选择一个输出文件夹。" )
            return
        if not self.image_paths:
            messagebox.showerror("错误", "列表中没有需要处理的图片。" )
            return

        watermark_type = self.watermark_type_var.get()
        position = self.position_var.get()
        output_format = self.output_format_var.get()
        naming_rule = self.naming_rule_var.get()
        prefix_suffix = self.prefix_suffix_var.get()
        jpeg_quality = self.jpeg_quality_var.get()
        resize_enabled = self.resize_enabled_var.get()
        output_width = self.output_width_var.get()
        output_height = self.output_height_var.get()
        rotation = self.rotation_var.get()

        # Text watermark specific
        watermark_text = self.watermark_text_var.get()
        opacity = self.opacity_var.get()
        try:
            font_size = int(self.font_size_var.get())
        except (ValueError, TypeError):
            font_size = 50 # Default size if input is invalid
        font_name = self.font_name_var.get()
        color = self.font_color_var.get()
        is_bold = self.is_bold_var.get()
        is_italic = self.is_italic_var.get()
        shadow_enabled = self.shadow_enabled_var.get()
        shadow_color = self.shadow_color_var.get()

        # Image watermark specific
        image_wm_path = self.image_watermark_path_var.get()
        image_wm_scale = self.image_watermark_scale_var.get()
        image_wm_opacity = self.image_watermark_opacity_var.get()

        if watermark_type == "图片" and (not image_wm_path or not os.path.exists(image_wm_path)):
            messagebox.showerror("错误", "请先选择一个有效的水印图片。" )
            return

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
                image_path, output_path, 
                watermark_type=watermark_type,
                position=final_position_str, 
                output_format=output_format, 
                jpeg_quality=jpeg_quality,
                resize_enabled=resize_enabled, 
                output_width=output_width, 
                output_height=output_height,
                # Text-specific
                text=watermark_text, 
                font_size=font_size, 
                font_color=color, 
                opacity=opacity, 
                font_name=font_name,
                is_bold=is_bold, 
                is_italic=is_italic, 
                shadow_enabled=shadow_enabled, 
                shadow_color=shadow_color,
                # Image-specific
                image_path_wm=image_wm_path,
                image_scale=image_wm_scale,
                image_opacity=image_wm_opacity,
                rotation=rotation
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

    def update_template_menu(self):
        self.templates = []
        if not os.path.exists("templates"):
            os.makedirs("templates")
        for f in os.listdir("templates"):
            if f.endswith(".json"):
                self.templates.append(os.path.splitext(f)[0])
        if not self.templates:
            self.templates.append("无可用模板")
        self.template_menu.configure(values=self.templates)
        self.template_var.set(self.templates[0])

    def save_template(self):
        dialog = customtkinter.CTkInputDialog(text="输入模板名称:", title="保存模板")
        template_name = dialog.get_input()
        if template_name:
            settings = self.get_current_settings()
            if not os.path.exists("templates"):
                os.makedirs("templates")
            with open(f"templates/{template_name}.json", "w") as f:
                json.dump(settings, f, indent=4)
            self.update_template_menu()
            self.template_var.set(template_name)

    def load_template(self, template_name):
        if template_name == "无可用模板":
            return
        try:
            with open(f"templates/{template_name}.json", "r") as f:
                settings = json.load(f)
                self.load_settings(settings)
        except FileNotFoundError:
            messagebox.showerror("错误", f"模板 '{template_name}' 未找到.")
            self.update_template_menu()

    def delete_template(self):
        template_name = self.template_var.get()
        if template_name == "无可用模板":
            return
        if messagebox.askyesno("确认删除", f"确定要删除模板 '{template_name}'吗?"):
            try:
                os.remove(f"templates/{template_name}.json")
                self.update_template_menu()
            except FileNotFoundError:
                messagebox.showerror("错误", f"模板 '{template_name}' 未找到.")
                self.update_template_menu()

    def get_current_settings(self):
        return {
            "output_dir": self.output_dir,
            "output_format": self.output_format_var.get(),
            "watermark_text": self.watermark_text_var.get(),
            "opacity": self.opacity_var.get(),
            "position": self.position_var.get(),
            "naming_rule": self.naming_rule_var.get(),
            "prefix_suffix": self.prefix_suffix_var.get(),
            "font_name": self.font_name_var.get(),
            "font_size": self.font_size_var.get(),
            "font_color": self.font_color_var.get(),
            "is_bold": self.is_bold_var.get(),
            "is_italic": self.is_italic_var.get(),
            "shadow_enabled": self.shadow_enabled_var.get(),
            "shadow_color": self.shadow_color_var.get(),
            "jpeg_quality": self.jpeg_quality_var.get(),
            "resize_enabled": self.resize_enabled_var.get(),
            "output_width": self.output_width_var.get(),
            "output_height": self.output_height_var.get(),
            "watermark_type": self.watermark_type_var.get(),
            "image_watermark_path": self.image_watermark_path_var.get(),
            "image_watermark_scale": self.image_watermark_scale_var.get(),
            "image_watermark_opacity": self.image_watermark_opacity_var.get(),
            "rotation": self.rotation_var.get(),
        }

    def save_settings(self):
        settings = self.get_current_settings()
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self, settings_dict=None):
        try:
            if settings_dict:
                settings = settings_dict
            elif os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
            else:
                return

            self.output_dir = settings.get("output_dir", "")
            self.output_format_var.set(settings.get("output_format", "JPEG"))
            self.watermark_text_var.set(settings.get("watermark_text", "Hello World"))
            self.opacity_var.set(settings.get("opacity", 70))
            self.position_var.set(settings.get("position", "bottom-right"))
            self.naming_rule_var.set(settings.get("naming_rule", "原文件名"))
            self.prefix_suffix_var.set(settings.get("prefix_suffix", "watermarked_"))
            self.font_name_var.set(settings.get("font_name", "arial.ttf"))
            self.font_size_var.set(settings.get("font_size", "50"))
            self.font_color_var.set(settings.get("font_color", "white"))
            self.is_bold_var.set(settings.get("is_bold", False))
            self.is_italic_var.set(settings.get("is_italic", False))
            self.shadow_enabled_var.set(settings.get("shadow_enabled", False))
            self.shadow_color_var.set(settings.get("shadow_color", "black"))
            self.jpeg_quality_var.set(settings.get("jpeg_quality", 95))
            self.resize_enabled_var.set(settings.get("resize_enabled", False))
            self.output_width_var.set(settings.get("output_width", ""))
            self.output_height_var.set(settings.get("output_height", ""))
            self.watermark_type_var.set(settings.get("watermark_type", "文本"))
            self.image_watermark_path_var.set(settings.get("image_watermark_path", ""))
            self.image_watermark_scale_var.set(settings.get("image_watermark_scale", 50))
            self.image_watermark_opacity_var.set(settings.get("image_watermark_opacity", 70))
            self.rotation_var.set(settings.get("rotation", 0))

            if self.output_dir:
                self.output_dir_label.configure(text=f"输出到:\n{self.output_dir}")
            self.opacity_label.configure(text=f"透明度: {int(self.opacity_var.get())}%")
            self.font_color_label.configure(text=self.font_color_var.get())
            self.shadow_color_label.configure(text=self.shadow_color_var.get())
            self._on_jpeg_quality_change(self.jpeg_quality_var.get())
            self._toggle_jpeg_quality_slider()
            self._toggle_resize_entries()
            self._switch_watermark_type(self.watermark_type_var.get())
            self.image_wm_path_label.configure(text=os.path.basename(self.image_watermark_path_var.get()) or "未选择图片")
            self._on_image_scale_change(self.image_watermark_scale_var.get())
            self._on_image_opacity_change(self.image_watermark_opacity_var.get())
            self._on_rotation_change(self.rotation_var.get())
        except Exception as e:
            print(f"Error loading settings: {e}")
