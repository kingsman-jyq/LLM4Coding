# Image Watermark App

A user-friendly desktop application for adding customizable text watermarks to your images in batches. Built with Python and customtkinter, it offers a modern and intuitive graphical user interface (GUI).

## Features

- **Intuitive GUI**: A clean and modern interface that is easy to navigate.
- **Batch Processing**: Add images individually, by folder, or simply by dragging and dropping them into the app.
- **Live Preview**: See your watermark adjustments in real-time on a selected image before processing.
- **Flexible Input**: Supports common image formats like `JPEG` and `PNG`.
- **Customizable Watermark**:
    - **Text**: Use any custom text for your watermark.
    - **Opacity**: Adjust transparency from 0% to 100% with a simple slider.
    - **Position**: Place your watermark using a 9-point grid for quick placement, or simply drag the watermark on the preview image to position it exactly where you want.
- **Output Control**:
    - Choose between `JPEG` or `PNG` as the output format.
    - Specify a dedicated output folder to keep your original images safe and untouched.
    - Define file naming rules: keep the original name, add a prefix, or add a suffix.
- **Settings Persistence**: The app automatically saves your last-used settings (e.g., output path, opacity) and reloads them on startup for a faster workflow.

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

1.  **Run the application from your terminal:**
    ```bash
    python main.py
    ```

2.  **Add Images**: Use the "Select Images" or "Select Folder" buttons. You can also drag and drop image files directly onto the application window. Your selected images will appear in the list on the right.

3.  **Set Output Location**: Click "Select Output Folder" to choose where your watermarked images will be saved.

4.  **Customize Watermark**: Use the controls in the left-hand panel to:
    - Change the watermark text.
    - Adjust the opacity.
    - Select an output format (`JPEG` or `PNG`).
    - Define the file naming rule.

5.  **Position the Watermark**:
    - Click one of the nine buttons in the position grid for quick placement.
    - For precise control, click and drag the watermark directly within the preview image area.

6.  **Start Processing**: Once you are happy with the settings and preview, click the "Start Processing" button to apply the watermark to all the images in your list.