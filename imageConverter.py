import requests
from bs4 import BeautifulSoup
from multiprocessing import Process, Queue, cpu_count
import multiprocessing
from multiprocessing.dummy import Pool
import re
import sys
import time
import os
import tkinter as tk
from tkinter import  filedialog
from tkinter import ttk, messagebox
from PIL import Image
import concurrent.futures
import sv_ttk
import time
import shutil
from sys import platform
import tempfile
from urllib.parse import urlparse, urljoin


def normalize_path(path):
            """ Normalize and clean the path. """
            return os.path.normpath(os.path.abspath(path)) 
        
def combine_and_normalize(*paths):
    """ Combines multiple path components and normalizes the result. """
    combined_path = os.path.join(*paths)
    return normalize_path(combined_path)

class ImageConverterGUI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        cursor_point = "hand2" if platform != "darwin" else "pointinghand"
        
        def resource_path(relative_path):
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
                
            return os.path.join(base_path, relative_path)
        
        self.style = ttk.Style(self)
        self.style.configure("TFrame", background="#1c1c1c")

        self.folder_path = tk.StringVar()
        self.destination_folder_path = tk.StringVar()
        self.quality = tk.IntVar(value=100)
        self.progress = tk.DoubleVar(value=0)
        self.overide_images = tk.BooleanVar()
        self.rename = tk.BooleanVar()
        self.convert = tk.BooleanVar()
        self.compress = tk.BooleanVar()
        self.fileOut = tk.StringVar()
        self.extension = tk.StringVar()
        self.start_time = None
        self.end_time = None
        self.new_width_percentage = tk.IntVar(value=100)
        
        
        sv_ttk.set_theme("dark")
        
        url_entry_label = ttk.Label(self, text="Page URL:")
        url_entry_label.grid(column=0, row=1, padx=20, pady=20, sticky=tk.W)

        self.url_entry = ttk.Entry(self, width=30)
        self.url_entry.grid(column=1, row=0, padx=20, pady=20, sticky=tk.W)
        
        destination_folder_label = ttk.Label(self, text="Destination Folder:")
        destination_folder_label.grid(column=0, row=1, padx=20, pady=20, sticky=tk.W)

        destination_folder_entry = ttk.Entry(self, width=30, textvariable=self.destination_folder_path)
        destination_folder_entry.grid(column=1, row=1, padx=20, pady=20, sticky=tk.W)
        
        destination_folder_button = ttk.Button(self, text="Select Folder", command=self.destination_select_folder, cursor=cursor_point)
        destination_folder_button.grid(column=2, row=1, padx=20, pady=20, sticky=tk.W)
        
        convert_checkbox = ttk.Checkbutton(self, text="Convert", variable=self.convert, cursor=cursor_point)
        convert_checkbox.grid(column=1, row=2, padx=20, pady=20, sticky=tk.W)
        
        rename_checkbox = ttk.Checkbutton(self, text="Rename", variable=self.rename, cursor=cursor_point)
        rename_checkbox.grid(column=2, row=2, padx=20, pady=20, sticky=tk.W)
        
        compress_checkbox = ttk.Checkbutton(self, text="Compress", variable=self.compress, command=self.toggle_compress, cursor=cursor_point)
        compress_checkbox.grid(column=0, row=2, padx=20, pady=20, sticky=tk.W)

        quality_label_text = ttk.Label(self, text="Quality:")
        quality_label_text.grid(column=0, row=3, padx=20, pady=20, sticky=tk.W)
        
        self.quality = tk.IntVar(value=100)

        self.quality_slider = ttk.Scale(self, length=250, orient="horizontal", from_=0, to=100, variable=self.quality, command=self.update_quality_label, state=tk.DISABLED, cursor="arrow")
        self.quality_slider.grid(column=1, row=3, padx=20, pady=20, sticky=tk.W)

        self.quality_label = ttk.Label(self, text="Quality: {}%".format(self.quality.get()), state=tk.DISABLED)
        self.quality_label.grid(column=3, row=3, padx=20, pady=20, sticky=tk.W)
        
        
        self.quality_entry = ttk.Entry(self, textvariable=self.quality, width=5, state=tk.DISABLED, cursor="arrow")
        self.quality_entry.grid(column=2, row=3, padx=20, pady=20, sticky=tk.W)
        
        self.resize_checkbox = tk.BooleanVar()
        resize_checkbox = ttk.Checkbutton(self, text="Enable Resizing", variable=self.resize_checkbox, command=self.toggle_resize_slider, cursor=cursor_point)
        resize_checkbox.grid(column=0, padx=20, pady=20, row=4, sticky=tk.W)
        
        resize_label = ttk.Label(self, text="Resize Width (%):")
        resize_label.grid(column=0, row=5, padx=20, pady=20, sticky=tk.W)

        self.new_width_percentage = tk.IntVar(value=100)  # Default value of 100

        self.resize_slider = ttk.Scale(self, length=250, from_=1, to=100, orient="horizontal", variable=self.new_width_percentage, command=self.update_resize_label, state=tk.DISABLED, cursor="arrow")
        self.resize_slider.grid(column=1, row=5, padx=20, pady=20, sticky=tk.W)
        
        
        self.resize_entry = ttk.Entry(self, textvariable=self.new_width_percentage, width=5, state=tk.DISABLED, cursor="arrow")
        self.resize_entry.grid(column=2, row=5, padx=20, pady=20, sticky=tk.W)

        self.resize_label = ttk.Label(self, text="Resize: {}%".format(self.new_width_percentage.get()), state=tk.DISABLED)
        self.resize_label.grid(column=3, row=5, padx=20, pady=20, sticky=tk.W)

        convert_button = ttk.Button(self, text="Run", command=self.download_images, cursor=cursor_point)
        convert_button.grid(column=0, row=6, padx=20, pady=20, sticky=tk.W)

        progress_bar = ttk.Progressbar(self, orient="horizontal", mode="determinate", variable=self.progress, style="green.Horizontal.TProgressbar")
        progress_bar.grid(column=0, row=7, columnspan=4, padx=20, pady=20, sticky=tk.W+tk.E)
        
        self.time_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.time_label.grid(column=1, row=6, padx=20, pady=20, sticky=tk.W)
        
        # Get the required width and height of the window based on its content
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        self.new_width_percentage.trace('w', self.validate_resize_percentage)
        self.quality.trace('w', self.validate_quality_percentage)
    

        # Update the geometry of the window to fit the content
    
    def update_resize_label(self, value):
        self.resize_label.configure(text="Resize: {}%".format(round(float(value))))
        
    def toggle_resize_slider(self):
        cursor_point = "hand2" if platform != "darwin" else "pointinghand"
        if self.resize_checkbox.get():
            self.resize_label.config(state=tk.NORMAL)
            self.resize_slider.config(state=tk.NORMAL)
            self.resize_entry.config(state=tk.NORMAL)
            self.resize_slider.config(cursor=cursor_point)
            self.resize_entry.config(cursor="xterm")
        else:
            self.resize_label.config(state=tk.DISABLED)
            self.resize_slider.config(state=tk.DISABLED)
            self.resize_entry.config(state=tk.DISABLED)
            self.resize_slider.config(cursor="arrow")
            self.resize_entry.config(cursor="arrow")


    def toggle_compress(self):
        cursor_point = "hand2" if platform != "darwin" else "pointinghand"
        if not self.compress.get():
            self.quality_label.config(state=tk.DISABLED)
            self.quality_slider.config(state=tk.DISABLED)
            self.quality_entry.config(state=tk.DISABLED)
            self.quality_slider.config(cursor="arrow")
            self.quality_entry.config(cursor="arrow")
        else:
            self.quality_label.config(state=tk.NORMAL)
            self.quality_slider.config(state=tk.NORMAL)
            self.quality_entry.config(state=tk.NORMAL)
            self.quality_slider.config(cursor=cursor_point)
            self.quality_entry.config(cursor="xterm")
            
    def validate_quality_percentage(self, *args):
        try:
            value_str = self.quality.get()
            
            # Check if the string is empty first
            if not value_str:
                value = 0
            else:
                value = round(float(value_str))
                
            if value < 1:
                self.quality.set(1)
            elif value > 100:
                self.quality.set(100)
            else:
                self.quality.set(value)
        except ValueError:
            # The string is not a number, set to 0
            self.quality.set(0)
        self.quality_label.configure(text="Quality: {}%".format(self.quality.get()))

        
    def validate_resize_percentage(self, *args):
        try:
            value_str = self.new_width_percentage.get()
            
            # Check if the string is empty first
            if not value_str:
                value = 0
            else:
                value = round(float(value_str))
                
            if value < 1:
                self.new_width_percentage.set(1)
            elif value > 100:
                self.new_width_percentage.set(100)
            else:
                self.new_width_percentage.set(value)
        except ValueError:
            # The string is not a number, set to 0
            self.new_width_percentage.set(0)
        self.resize_label.configure(text="Resize: {}%".format(self.new_width_percentage.get()))
        
    def download_images(self):
        self.start_time = time.time()  # Set the start time here before downloading starts
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "URL is empty")
            return

        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract page title or use a sanitized version of the URL as folder name
            page_title = soup.title.text if soup.title else url.split('//')[-1].split('/')[0]
            page_title = re.sub(r'[^\w\s-]', '', page_title).strip().replace(' ', '_')

            # Collect images excluding those in <header> and <footer>
            images = []
            for img in soup.find_all('img'):
                if img.get('src') and not any(parent.name in ['header', 'footer'] for parent in img.parents):
                    if not (img['src'].endswith('.webp') or img['src'].endswith('.svg')):
                        images.append(img)


            destination_folder = self.destination_folder_path.get()
            if not destination_folder:
                messagebox.showerror("Error", "Destination folder is not set")
                return

            page_folder = os.path.join(destination_folder, page_title)
            os.makedirs(page_folder, exist_ok=True)  # Create page folder

            with tempfile.TemporaryDirectory() as tmp_dir:
                self.folder_path.set(tmp_dir)  # Temporary folder for initial download
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_to_image = {executor.submit(self.save_image, urljoin(url, img['src']), tmp_dir, page_folder): img for img in images}
                    for future in concurrent.futures.as_completed(future_to_image):
                        img = future_to_image[future]
                        try:
                            future.result()  # wait for each image to be saved
                        except Exception as exc:
                            print('%r generated an exception: %s' % (img, exc))
                    
                messagebox.showinfo("Success", "Images downloaded successfully.")
                self.convert_images()
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", str(e))
            
    def save_image(self, src, tmp_dir, page_folder):
        response = requests.get(src)
        if response.status_code == 200:
            parsed_url = urlparse(src)
            parent_folder = os.path.basename(os.path.dirname(parsed_url.path))
            final_folder = os.path.join(page_folder, parent_folder)
            os.makedirs(final_folder, exist_ok=True)
            
            image_path = os.path.join(final_folder, os.path.basename(parsed_url.path))
            image_path = os.path.normpath(image_path)  # Normalize the path

            with open(image_path, 'wb') as f:
                f.write(response.content)
            print("File saved to:", image_path)
        else:
            print("Failed to download image from:", src)





        
    def select_file(self):
        file_selected = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=(("jpeg, png, webp files", "*.jpg *.png *.webp"), ("all files", "*.*"))
        )
        self.folder_path.set(file_selected)


    def select_folder(self):
        file_or_folder_selected = filedialog.askdirectory(
            title="Select folder where the images are",
        )
        self.folder_path.set(file_or_folder_selected)
    def fix_path(path):
        absolute_path = os.path.abspath(path)
        normalized_path = os.path.normpath(absolute_path)
        print(f"Original: {path}, Absolute: {absolute_path}, Normalized: {normalized_path}")
        return normalized_path
    
    def destination_select_folder(self):
        destination_folder_selected = filedialog.askdirectory(title="Select folder where the images will go")
        if destination_folder_selected:
            normalized_path = os.path.normpath(destination_folder_selected)
            self.destination_folder_path.set(normalized_path)
            print("Destination Folder Selected:", normalized_path)
        else:
            print("No folder was selected.")




    def update_quality_label(self, value):
        self.quality_label.configure(text="Quality: {}%".format(round(float(value))))
        
    def format_time(self, seconds):
        # Logic to format the time goes here
        if seconds >= 60:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes} minutes {int(seconds)} seconds"
        else:
            return f"{int(seconds)} seconds"
        
    def adjust_ppi(image, desired_ppi):
        """Adjust the PPI (pixels per inch) of the image to the desired value."""
        # Get current dpi
        dpi = image.info.get('dpi', (72, 72))
        if dpi[0] > desired_ppi:
            # Change the DPI without changing pixel data
            image = image.copy()
            image.info['dpi'] = (desired_ppi, desired_ppi)
        return image


    def convert_images(self):
        if not self.folder_path.get() or not os.path.exists(self.folder_path.get()):
            tk.messagebox.showerror("Error", "The specified source folder does not exist or is not set.")
            return

        destination_folder_path = self.destination_folder_path.get()
        if not destination_folder_path:
            tk.messagebox.showerror("Error", "Destination folder is not set.")
            return

        if self.compress.get():
            quality = self.quality.get()
        else:
            quality = 100

        files = []
        for root, dirs, filenames in os.walk(self.destination_folder_path.get()):
            for filename in filenames:
                if re.search(r'\.(jpg|jpeg|png|bmp|tiff)$', filename, re.IGNORECASE):
                    files.append(os.path.join(root, filename))

        if not files:
            tk.messagebox.showerror("Error", "No image files found in the selected folder.")
            return

        total_files = len(files)
        processed_files = 0

        with multiprocessing.Pool(processes=cpu_count()) as pool:
            results = []
            for file in files:
                # Assume these values need to be set or retrieved correctly
                rename = self.rename.get()
                overide_image = self.overide_images.get()
                extension = "webp" if self.convert.get() else os.path.splitext(file)[1][1:].lower()
                folder_path = self.folder_path.get()
                destination_folder_path = self.destination_folder_path.get()
                new_width_percentage = self.new_width_percentage.get()
                single_file_selected = os.path.isfile(folder_path)  # Or however this is determined

                # Correctly pass all required arguments
                result = pool.apply_async(
                    ImageConverterGUI.convert_file,
                    args=(
                        file, rename, quality, overide_image, extension, 
                        folder_path, destination_folder_path, 
                        new_width_percentage
                    )
                )
                results.append(result)

            for result in results:
                result.get()  # This will now wait for each task to complete
                processed_files += 1
                self.progress.set(processed_files / total_files * 100)
                self.update()
                
        if self.start_time is not None:
            self.end_time = time.time()
            time_taken = self

        self.end_time = time.time()
        time_taken = self.end_time - self.start_time
        formatted_time = self.format_time(time_taken)  # Correct way to call the method
        self.time_label.config(text=f"Time taken: {formatted_time}")     


    @staticmethod
    def convert_file(file_path, rename, quality, overide_image, extension, folder_path, destination_folder_path, new_width_percentage):
        print(f"Converting: {file_path}")

        # Normalize the incoming paths
        file_path = os.path.normpath(os.path.abspath(file_path))
        folder_path = os.path.normpath(os.path.abspath(folder_path))
        destination_folder_path = os.path.normpath(os.path.abspath(destination_folder_path))
        print(f"Normalized: {file_path}, {folder_path}, {destination_folder_path}")

        with Image.open(file_path) as image:
            # Calculate new dimensions while maintaining the aspect ratio
            width_percent = new_width_percentage / 100
            new_width = int(image.width * width_percent)
            new_height = int(image.height * (new_width / image.width))

            # Resize the image
            image = image.resize((new_width, new_height), Image.LANCZOS)
            image = ImageConverterGUI.adjust_ppi(image, 72)

            # Handle renaming and choosing file extension
            directory, original_file_name = os.path.split(file_path)
            original_base_name, original_ext = os.path.splitext(original_file_name)
            if rename:
                new_base_name = re.sub(r'[^\w\s-]', '', original_base_name)
                new_base_name = new_base_name.lower().replace(' ', '-').replace('_', '-')
                new_base_name = re.sub(r'[-]+', '-', new_base_name).strip('-')
            else:
                new_base_name = original_base_name

            # Decide on the final file extension
            new_extension = extension if extension else original_ext.lstrip('.')
            new_file_name = f"{new_base_name}.{new_extension}"
            new_file_path = os.path.join(directory, new_file_name)

            # Save the new image, possibly replacing the original
            image.save(new_file_path, quality=quality, method=6)
            print(f"Saved converted file to: {new_file_path}")

            # Optionally delete the original file if overwriting is enabled
            os.remove(file_path)
            print(f"Original file removed: {file_path}")



            
    processes = []