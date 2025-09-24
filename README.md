# Image Date Watermarker

A Python script to automatically add date watermarks to a batch of images. The script extracts the original creation date from the image's EXIF metadata and applies it as a customizable watermark.

## Features

- **Automatic Date Extraction**: Reads the 'DateTimeOriginal' tag from EXIF data.
- **Batch Processing**: Process an entire directory of images at once.
- **Customizable Watermark**:
    - Font Size
    - Color (by name or RGB value)
    - Position (top-left, top-right, bottom-left, bottom-right, center)
    - Opacity
- **Safe Output**: Creates a new sub-directory for watermarked images, leaving original files untouched.
- **Cross-Platform**: Uses default fonts if specific ones like Arial are not found.

## Prerequisites

- Python 3.x

## Installation

1.  **Clone the repository or download the files.**

2.  **Navigate to the project directory:**
    ```bash
    cd path\to\llm-assist
    ```

3.  **It is recommended to use a Python virtual environment:**
    ```bash
    # Create a virtual environment
    python -m venv venv

    # Activate it
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

4.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from your terminal, pointing it to the directory containing your images.

### Basic Usage

```bash
python main.py "C:\path\to\your\image_folder"
```

This will process all images in the specified folder using the default settings and save them to a new folder named `image_folder_watermark`.

### Advanced Options

You can customize the watermark using the following command-line arguments:

- `-s`, `--font-size`: Set the font size. (Default: 50)
- `-c`, `--color`: Set the text color. Can be a name (e.g., `red`, `black`) or an RGB value (e.g., "0,0,255"). (Default: "white")
- `-p`, `--position`: Set the watermark position. (Choices: `top-left`, `top-right`, `bottom-left`, `bottom-right`, `center`). (Default: "bottom-right")
- `-o`, `--opacity`: Set the text opacity from 0 (transparent) to 100 (opaque). (Default: 70)

### Examples

**Red watermark in the top-left corner:**
```bash
python main.py "C:\Photos\Vacation" -c red -p top-left
```

**Large, semi-transparent blue watermark in the center:**
```bash
python main.py "D:\Pictures" --font-size 120 --color "0,0,255" --position center --opacity 50
```
