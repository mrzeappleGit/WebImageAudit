from multiprocessing import Process, Queue, cpu_count
import multiprocessing
from multiprocessing.dummy import Pool
import re
import sys
import time
import os
import tkinter as tk
from tkinter import  filedialog
from tkinter import ttk
from tkinter import messagebox
from PIL import Image
import sv_ttk
import time
import shutil
from selenium import webdriver
from sys import platform
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.chrome.service import Service
from io import BytesIO
import requests
from urllib.parse import urlparse
import threading

class urlPickerGUI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        
        sv_ttk.set_theme("dark")
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Create entry widgets for URL input
        self.url_entry1 = ttk.Entry(self.toolbar, width=50)
        self.url_entry1.grid(row=0, column=1, padx=10, pady=10)
        self.url_entry2 = ttk.Entry(self.toolbar, width=50)
        self.url_entry2.grid(row=1, column=1, padx=10, pady=10)

        # Labels for entries
        ttk.Label(self.toolbar, text="Enter Production URL:").grid(row=0, column=0, pady=5, padx=10)
        ttk.Label(self.toolbar, text="Enter Test URL:").grid(row=1, column=0, pady=5, padx=10)

        # Button to trigger comparison
        compare_button = ttk.Button(self.toolbar, text="Compare", command=self.compare_images)
        compare_button.grid(row=2, column=0, pady=10, padx=10, columnspan=2, sticky="ew")
        
        # Progress bar
        self.progress = ttk.Progressbar(self.toolbar, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.grid(row=3, column=0, pady=10, padx=10, columnspan=2, sticky="ew")

        # Label to display results
        self.result_frame = ttk.Frame(self)
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        self.result_label = ttk.Label(self.result_frame, text="Results will be shown here.")
        self.result_label.pack(pady=10)
    def update_progress(self, value):
        """Update the progress bar to the specified value."""
        self.progress['value'] = value
        self.progress.update_idletasks()  # Update the GUI to reflect changes
        
    def compare_images(self):
        # Start the comparison in a new thread to keep the GUI responsive
        self.progress['value'] = 0
        thread = threading.Thread(target=self.run_comparison)
        thread.start()
        
    def run_comparison(self):
        def resource_path(relative_path):
            try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
                
            return os.path.join(base_path, relative_path)
        RemoteConnection.set_timeout(30)
        # Placeholder function for the logic to compare image URLs
        url1 = self.url_entry1.get()
        url2 = self.url_entry2.get()
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')  # Last I checked this was necessary.
        driver_path = resource_path("chromedriver.exe")
        options.binary_location = resource_path("chrome.exe")
        s = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=s, options=options)
        urls_to_compare = [url1, url2]
        total_steps = len(urls_to_compare)  # Total steps for the progress bar
        current_step = 0

       # Helper function to get image file sizes
        def get_image_file_sizes(url_list):
            image_sizes = {}
            for url in url_list:
                response = requests.get(url, verify=False)
                if response.status_code == 200:
                    image_size = len(response.content)  # Get size of image in bytes
                    image_sizes[url] = image_size
            return image_sizes

        # Navigate and extract image URLs
        driver.get(url1)
        images1 = driver.execute_script(
            "return Array.from(document.querySelectorAll('body *:not(header) *:not(footer) img')).map(img => img.src);")
        image_sizes1 = get_image_file_sizes(images1)
        current_step += 1
        progress_update = int((current_step / total_steps) * 100)
        self.master.after(0, self.update_progress, progress_update)

        driver.get(url2)
        images2 = driver.execute_script(
            "return Array.from(document.querySelectorAll('body *:not(header) *:not(footer) img')).map(img => img.src);")
        image_sizes2 = get_image_file_sizes(images2)
        current_step += 1
        progress_update = int((current_step / total_steps) * 100)
        self.master.after(0, self.update_progress, progress_update)

        driver.quit()
        
        # Update GUI from thread

        # Function to extract path after .com
        def extract_path(url):
            parts = urlparse(url)
            match = re.search(r'\.com(.*)', parts.geturl())
            return match.group(1) if match else None

        # Map paths to file sizes
        path_to_size1 = {extract_path(url): self.get_image_size(url) for url in images1 if extract_path(url)}
        path_to_size2 = {extract_path(url): self.get_image_size(url) for url in images2 if extract_path(url)}

        # Compare file sizes for common paths and list URLs not in URL1
        differing_sizes = {path for path, size in path_to_size2.items() if path in path_to_size1 and path_to_size1[path] != size}
        not_in_url1 = {path for path in path_to_size2 if path not in path_to_size1}

        self.master.after(0, self.update_results, differing_sizes, not_in_url1)

    def get_image_size(self, url):
        try:
            response = requests.get(url, verify=False)
            return len(response.content) if response.status_code == 200 else None
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to get image: {e}")
            return None

    def update_results(self, differing_sizes, not_in_url1):
        """ Update GUI to display results and provide copy-to-clipboard functionality. """
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        if not differing_sizes and not not_in_url1:
            ttk.Label(self.result_frame, text="No differences found.").pack()
            return

        if differing_sizes:
            ttk.Label(self.result_frame, text="Images with differing sizes:").pack()
            for path in differing_sizes:
                frame = ttk.Frame(self.result_frame)
                frame.pack(fill=tk.X, expand=True)
                ttk.Label(frame, text=path).pack(side=tk.LEFT, padx=10)
                button = ttk.Button(frame, text="Copy", command=lambda p=path: self.copy_to_clipboard(p))
                button.pack(side=tk.RIGHT)

        if not_in_url1:
            ttk.Label(self.result_frame, text="New Images:").pack()
            for path in not_in_url1:
                frame = ttk.Frame(self.result_frame)
                frame.pack(fill=tk.X, expand=True)
                ttk.Label(frame, text=path).pack(side=tk.LEFT, padx=10)
                button = ttk.Button(frame, text="Copy", command=lambda p=path: self.copy_to_clipboard(p))
                button.pack(side=tk.RIGHT)

    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Clipboard", "Copied to clipboard: " + text)