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

def generate_watermarked_image(img, watermark_text, font_size, color, position, opacity):
    """Applies a watermark to a PIL Image object and returns a new watermarked image object."""
    base_img = img.copy().convert("RGBA")
    txt_layer = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    try:
        font = ImageFont.truetype("arial.ttf", size=font_size)
    except IOError:
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
    draw.text(text_position, watermark_text, font=font, fill=text_color_with_opacity)

    watermarked_img = Image.alpha_composite(base_img, txt_layer)
    return watermarked_img, text_size

def add_watermark(image_path, output_path, watermark_text, font_size, color, position, opacity, output_format):
    """Adds a watermark to an image and saves it to the specified output path."""
    try:
        with Image.open(image_path).convert("RGBA") as img:
            watermarked_img, _ = generate_watermarked_image(img, watermark_text, font_size, color, position, opacity)
            
            save_format = output_format.upper()
            if save_format == 'JPEG':
                watermarked_img = watermarked_img.convert("RGB")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            watermarked_img.save(output_path, format=save_format)
            print(f"Saved watermarked image to: {output_path}")

    except Exception as e:
        print(f"Could not process {os.path.basename(image_path)}: {e}")
