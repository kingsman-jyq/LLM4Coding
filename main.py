import os
from PIL import Image, ImageDraw, ImageFont, ExifTags
import argparse

def get_exif_date(img):
    """Extracts the original creation date from image EXIF data."""
    try:
        exif_data = img._getexif()
        if not exif_data:
            return None

        # Find the tag for DateTimeOriginal
        for tag, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag, tag)
            if tag_name == 'DateTimeOriginal':
                # Format: YYYY:MM:DD HH:MM:SS -> YYYY-MM-DD
                return value.split(' ')[0].replace(':', '-')
        return None
    except (AttributeError, KeyError, IndexError):
        return None

def add_watermark(image_path, output_dir):
    """Adds a date watermark to an image and saves it."""
    try:
        with Image.open(image_path) as img:
            # Get date from EXIF
            watermark_text = get_exif_date(img)
            if not watermark_text:
                print(f"Skipping {os.path.basename(image_path)}: No EXIF date found.")
                return

            # Prepare to draw
            draw = ImageDraw.Draw(img)
            
            # Use a default font bundled with Pillow
            try:
                font = ImageFont.truetype("arial.ttf", size=50)
            except IOError:
                font = ImageFont.load_default()
                print("Arial font not found, using default font.")

            # Default settings (white, bottom-right)
            text_color = (255, 255, 255, 220) # White with some transparency
            margin = 10
            text_width, text_height = draw.textsize(watermark_text, font)
            position = (img.width - text_width - margin, img.height - text_height - margin)

            # Draw the watermark
            draw.text(position, watermark_text, font=font, fill=text_color)

            # Save the watermarked image
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, filename)
            img.save(output_path)
            print(f"Saved watermarked image to: {output_path}")

    except Exception as e:
        print(f"Could not process {os.path.basename(image_path)}: {e}")


def main():
    """Main function to process a directory of images."""
    parser = argparse.ArgumentParser(description="Add date watermarks to images.")
    parser.add_argument("image_dir", help="Path to the directory containing images.")
    args = parser.parse_args()

    input_dir = args.image_dir
    if not os.path.isdir(input_dir):
        print(f"Error: Directory not found at {input_dir}")
        return

    # Create the output directory
    parent_dir = os.path.dirname(os.path.abspath(input_dir))
    dir_name = os.path.basename(os.path.abspath(input_dir))
    output_dir = os.path.join(parent_dir, f"{dir_name}_watermark")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Process each file in the directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            image_path = os.path.join(input_dir, filename)
            add_watermark(image_path, output_dir)

if __name__ == "__main__":
    main()