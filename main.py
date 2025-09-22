
import os
from PIL import Image, ImageDraw, ImageFont, ExifTags
import argparse

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

def main():
    """Main function to process a directory of images."""
    parser = argparse.ArgumentParser(description="Add date watermarks to images based on EXIF data.")
    parser.add_argument("image_dir", help="Path to the directory containing images.")
    parser.add_argument("-s", "--font-size", type=int, default=50, help="Font size for the watermark text. Default: 50.")
    parser.add_argument("-c", "--color", default="white", help="Color of the watermark. Can be a name (e.g., 'white', 'red') or an RGB string 'R,G,B'. Default: 'white'.")
    parser.add_argument("-p", "--position", default="bottom-right", choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"], help="Position of the watermark. Default: 'bottom-right'.")
    parser.add_argument("-o", "--opacity", type=int, default=70, help="Opacity of the watermark text (0-100). Default: 70.")

    args = parser.parse_args()

    input_dir = args.image_dir
    if not os.path.isdir(input_dir):
        print(f"Error: Directory not found at {input_dir}")
        return

    # Create the output directory as a subdirectory of the input directory
    output_dir = os.path.join(input_dir, f"{os.path.basename(os.path.abspath(input_dir))}_watermark")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            image_path = os.path.join(input_dir, filename)
            add_watermark(image_path, output_dir, args.font_size, args.color, args.position, args.opacity)

if __name__ == "__main__":
    main()
