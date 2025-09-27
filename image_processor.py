import os
from PIL import Image, ImageDraw, ImageFont, ExifTags

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
    """Parses a color string (name, hex, or RGB) into an RGBA tuple."""
    color_str = color_str.lower().strip()
    if color_str.startswith('#'):
        try:
            hex_color = color_str.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            print(f"Warning: Invalid hex color '{color_str}'. Defaulting to white.")
            r, g, b = 255, 255, 255
    elif color_str in COLOR_MAP:
        r, g, b = COLOR_MAP[color_str]
    else:
        try:
            r, g, b = map(int, color_str.split(','))
        except ValueError:
            print(f"Warning: Invalid color format '{color_str}'. Defaulting to white.")
            r, g, b = 255, 255, 255
    return (r, g, b, int(255 * ((100 - opacity) / 100)))

def get_position(img_size, text_size, position, margin):
    """Calculates the (x, y) coordinates for the watermark text."""
    if ',' in position:
        try:
            x, y = map(int, map(float, position.split(',')))
            return (x, y)
        except ValueError:
            position = "bottom-right"

    img_width, img_height = img_size
    text_width, text_height = text_size

    positions = {
        "top-left": (margin, margin),
        "top-center": (int((img_width - text_width) / 2), margin),
        "top-right": (int(img_width - text_width - margin), margin),
        "center-left": (margin, int((img_height - text_height) / 2)),
        "center": (int((img_width - text_width) / 2), int((img_height - text_height) / 2)),
        "center-right": (int(img_width - text_width - margin), int((img_height - text_height) / 2)),
        "bottom-left": (margin, int(img_height - text_height - margin)),
        "bottom-center": (int((img_width - text_width) / 2), int(img_height - text_height - margin)),
        "bottom-right": (int(img_width - text_width - margin), int(img_height - text_height - margin)),
    }
    return positions.get(position, positions["bottom-right"])

def generate_watermarked_image(img, watermark_text, font_size, color, position, opacity, font_name="arial.ttf", is_bold=False, is_italic=False, shadow_enabled=False, shadow_color="black", shadow_offset=(2, 2)):
    """Applies a watermark to a PIL Image object and returns a new watermarked image object."""
    base_img = img.copy().convert("RGBA")
    txt_layer = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    try:
        base_font_name = font_name.split('.')[0]
        style = ""
        if is_bold:
            style += "b"
        if is_italic:
            style += "i"

        # This is a simplified mapping. A more robust solution would be more complex.
        style_map = {
            "arial": {"b": "arialbd.ttf", "i": "ariali.ttf", "bi": "arialbi.ttf"},
            "times": {"b": "timesbd.ttf", "i": "timesi.ttf", "bi": "timesbi.ttf"},
            "cour": {"b": "courbd.ttf", "i": "couri.ttf", "bi": "courbi.ttf"},
        }

        final_font_name = style_map.get(base_font_name, {}).get(style, font_name)

        font = ImageFont.truetype(final_font_name, size=font_size)
    except IOError:
        print(f"Warning: Font '{final_font_name}' not found. Falling back to '{font_name}' or default.")
        try:
            font = ImageFont.truetype(font_name, size=font_size)
        except IOError:
            print(f"Warning: Font '{font_name}' not found. Defaulting to built-in font.")
            font = ImageFont.load_default()

    text_color_with_opacity = parse_color(color, opacity)

    try:
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_size = (text_width, text_height)
    except AttributeError:
        text_size = draw.textsize(watermark_text, font)

    text_position = get_position(base_img.size, text_size, position, margin=10)

    if shadow_enabled:
        shadow_color_with_opacity = parse_color(shadow_color, opacity)
        shadow_pos = (text_position[0] + shadow_offset[0], text_position[1] + shadow_offset[1])
        draw.text(shadow_pos, watermark_text, font=font, fill=shadow_color_with_opacity)

    draw.text(text_position, watermark_text, font=font, fill=text_color_with_opacity)

    watermarked_img = Image.alpha_composite(base_img, txt_layer)
    return watermarked_img, text_size

def generate_image_watermarked_image(img, image_wm_path, scale, opacity, position):
    """Applies an image watermark to a PIL Image object."""
    base_img = img.copy().convert("RGBA")
    
    try:
        watermark = Image.open(image_wm_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Warning: Watermark image not found at {image_wm_path}")
        return base_img, (0, 0)

    # Scale watermark
    scale_factor = scale / 100
    wm_width = int(base_img.width * scale_factor)
    aspect_ratio = watermark.height / watermark.width
    wm_height = int(wm_width * aspect_ratio)
    watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)

    # Apply opacity
    if opacity < 100:
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: p * ((100 - opacity) / 100))
        watermark.putalpha(alpha)

    # Position watermark
    wm_size = watermark.size
    paste_position = get_position(base_img.size, wm_size, position, margin=10)

    # Create a transparent layer and paste the watermark onto it
    txt_layer = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    txt_layer.paste(watermark, paste_position, watermark)

    watermarked_img = Image.alpha_composite(base_img, txt_layer)
    return watermarked_img, wm_size

def add_watermark(image_path, output_path, watermark_type, position, output_format, jpeg_quality=95, resize_enabled=False, output_width=None, output_height=None, text="", font_size=50, font_color="white", opacity=70, font_name="arial.ttf", is_bold=False, is_italic=False, shadow_enabled=False, shadow_color="black", image_path_wm=None, image_scale=50, image_opacity=70, **kwargs):
    """Adds a watermark to an image and saves it to the specified output path."""
    try:
        with Image.open(image_path) as img:
            # Resize before watermarking
            if resize_enabled:
                try:
                    w = int(output_width) if output_width else None
                    h = int(output_height) if output_height else None
                    if w and h:
                        img = img.resize((w, h), Image.Resampling.LANCZOS)
                    elif w:
                        aspect_ratio = img.height / img.width
                        new_height = int(w * aspect_ratio)
                        img = img.resize((w, new_height), Image.Resampling.LANCZOS)
                    elif h:
                        aspect_ratio = img.width / img.height
                        new_width = int(h * aspect_ratio)
                        img = img.resize((new_width, h), Image.Resampling.LANCZOS)
                except (ValueError, TypeError) as e:
                    print(f"Invalid resize dimensions for {os.path.basename(image_path)}: {e}. Skipping resize.")

            img = img.convert("RGBA")

            if watermark_type == "文本":
                watermarked_img, _ = generate_watermarked_image(
                    img, text, font_size, font_color, position, opacity, font_name, 
                    is_bold, is_italic, shadow_enabled, shadow_color
                )
            else: # Image watermark
                watermarked_img, _ = generate_image_watermarked_image(
                    img, image_path_wm, image_scale, image_opacity, position
                )

            save_format = output_format.upper()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if save_format == 'JPEG':
                watermarked_img = watermarked_img.convert("RGB")
                watermarked_img.save(output_path, format=save_format, quality=jpeg_quality)
            else:
                watermarked_img.save(output_path, format=save_format)

            print(f"Saved watermarked image to: {output_path}")

    except Exception as e:
        print(f"Could not process {os.path.basename(image_path)}: {e}")
