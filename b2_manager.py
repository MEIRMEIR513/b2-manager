import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from b2sdk.v1 import (
    InMemoryAccountInfo,
    B2Api,
    DoNothingProgressListener
)

class B2Manager:
    def __init__(self, root):
        self.root = root
        self.root.title("B2 Cloud Storage Manager")
        self.root.geometry("900x650")
        self.root.resizable(False, False)

        self.selected_bucket = None
        self.selected_file = None
        self.current_folder = ""
        self.b2_api = None
        self.account_info = InMemoryAccountInfo()

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="B2 Cloud Storage Manager", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Authentication Frame
        auth_frame = tk.LabelFrame(self.root, text="Authentication", font=("Arial", 10, "bold"))
        auth_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(auth_frame, text="Application Key ID:", font=("Arial", 9)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.key_id_entry = tk.Entry(auth_frame, font=("Arial", 9), width=40)
        self.key_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(auth_frame, text="Application Key:", font=("Arial", 9)).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.key_entry = tk.Entry(auth_frame, font=("Arial", 9), width=40, show="*")
        self.key_entry.grid(row=1, column=1, padx=5, pady=5)

        connect_btn = tk.Button(auth_frame, text="Connect", command=self.connect_to_b2,
                               font=("Arial", 9, "bold"), bg="#4CAF50", fg="white", width=15)
        connect_btn.grid(row=2, column=1, padx=5, pady=10, sticky=tk.E)

        # Lists Frame
        lists_frame = tk.Frame(self.root)
        lists_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Buckets List
        bucket_frame = tk.LabelFrame(lists_frame, text="Buckets", font=("Arial", 10, "bold"))
        bucket_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.bucket_listbox = tk.Listbox(bucket_frame, font=("Arial", 9), selectmode=tk.SINGLE)
        self.bucket_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.bucket_listbox.bind('<<ListboxSelect>>', self.on_bucket_select)

        # Files List
        file_frame = tk.LabelFrame(lists_frame, text="Files", font=("Arial", 10, "bold"))
        file_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Add navigation buttons
        nav_frame = tk.Frame(file_frame)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)

        self.back_btn = tk.Button(nav_frame, text="↑ Back", command=self.go_back, state=tk.DISABLED, width=10)
        self.back_btn.pack(side=tk.LEFT, padx=2)

        self.current_path_label = tk.Label(nav_frame, text="", font=("Arial", 8), fg="gray")
        self.current_path_label.pack(side=tk.LEFT, padx=5)

        self.file_listbox = tk.Listbox(file_frame, font=("Arial", 9), selectmode=tk.SINGLE)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        self.file_listbox.bind('<Double-Button-1>', self.on_file_double_click)

        # Upload Frame
        upload_frame = tk.LabelFrame(self.root, text="Upload File", font=("Arial", 10, "bold"))
        upload_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(upload_frame, text="File:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.upload_entry = tk.Entry(upload_frame, font=("Arial", 9), width=50)
        self.upload_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_upload_btn = tk.Button(upload_frame, text="Browse", command=self.browse_upload_file,
                                     font=("Arial", 9), width=8)
        browse_upload_btn.pack(side=tk.LEFT, padx=5)

        upload_btn = tk.Button(upload_frame, text="Upload", command=self.upload_file,
                             font=("Arial", 9, "bold"), bg="#2196F3", fg="white", width=10)
        upload_btn.pack(side=tk.LEFT, padx=5)

        # Download Frame
        download_frame = tk.LabelFrame(self.root, text="Download/Delete File", font=("Arial", 10, "bold"))
        download_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(download_frame, text="Download Path:", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        self.download_entry = tk.Entry(download_frame, font=("Arial", 9), width=40)
        self.download_entry.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        self.download_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_download_btn = tk.Button(download_frame, text="Browse", command=self.browse_download_path,
                                       font=("Arial", 9), width=8)
        browse_download_btn.pack(side=tk.LEFT, padx=5)

        download_btn = tk.Button(download_frame, text="Download", command=self.download_file,
                                font=("Arial", 9, "bold"), bg="#2196F3", fg="white", width=10)
        download_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(download_frame, text="Delete", command=self.delete_file,
                             font=("Arial", 9, "bold"), bg="#f44336", fg="white", width=10)
        delete_btn.pack(side=tk.LEFT, padx=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, mode='determinate', length=800)
        self.progress.pack(pady=5)

        # Status Label
        self.status_label = tk.Label(self.root, text="Ready", font=("Arial", 9), fg="gray")
        self.status_label.pack(pady=5)

    def connect_to_b2(self):
        key_id = self.key_id_entry.get().strip()
        key = self.key_entry.get().strip()

        if not key_id or not key:
            messagebox.showerror("Error", "Please enter Key ID and Key")
            return

        self.status_label.config(text="Connecting...", fg="blue")
        self.progress.start()

        def connect_thread():
            try:
                self.b2_api = B2Api(self.account_info)
                self.b2_api.authorize_account('production', key_id, key)
                self.root.after(0, self.connect_complete, True, "Connected successfully!")
            except Exception as e:
                self.root.after(0, self.connect_complete, False, str(e))

        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()

    def connect_complete(self, success, message):
        self.progress.stop()
        if success:
            self.status_label.config(text=message, fg="green")
            self.list_buckets()
        else:
            self.status_label.config(text=f"Connection failed: {message}", fg="red")

    def list_buckets(self):
        try:
            buckets = self.b2_api.list_buckets()
            self.bucket_listbox.delete(0, tk.END)
            for bucket in buckets:
                self.bucket_listbox.insert(tk.END, bucket.name)
        except Exception as e:
            self.status_label.config(text=f"Error listing buckets: {str(e)}", fg="red")

    def on_bucket_select(self, event):
        selection = self.bucket_listbox.curselection()
        if selection:
            self.selected_bucket = self.bucket_listbox.get(selection[0])
            self.current_folder = ""
            self.list_files()

    def list_files(self):
        if not self.selected_bucket or not self.b2_api:
            return

        try:
            bucket = self.b2_api.get_bucket_by_name(self.selected_bucket)
            folder_to_list = self.current_folder

            self.file_listbox.delete(0, tk.END)

            # List files and folders - ls returns generator of (file_version, folder_name) tuples
            folders_seen = set()
            for file_version, folder_name in bucket.ls(folder_to_list=folder_to_list, latest_only=True, recursive=False, fetch_count=1000):
                if folder_name and folder_name not in folders_seen:
                    # This is a folder
                    display_name = folder_name[len(folder_to_list):] if folder_to_list else folder_name
                    if display_name.endswith('/'):
                        display_name = display_name[:-1]
                    self.file_listbox.insert(tk.END, f"📁 {display_name}")
                    folders_seen.add(folder_name)
                else:
                    # This is a file
                    file_name = file_version.file_name[len(folder_to_list):] if folder_to_list else file_version.file_name
                    size = self.format_size(file_version.size)
                    self.file_listbox.insert(tk.END, f"📄 {file_name} ({size})")

            # Update navigation
            if self.current_folder:
                self.back_btn.config(state=tk.NORMAL)
                self.current_path_label.config(text=self.current_folder)
            else:
                self.back_btn.config(state=tk.DISABLED)
                self.current_path_label.config(text="")

        except Exception as e:
            self.status_label.config(text=f"Error listing files: {str(e)}", fg="red")

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            self.selected_file = self.file_listbox.get(selection[0])

    def on_file_double_click(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            item = self.file_listbox.get(selection[0])
            if item.startswith("📁"):
                # It's a folder, navigate into it
                folder_name = item[2:].strip()
                if self.current_folder:
                    self.current_folder = self.current_folder + '/' + folder_name
                else:
                    self.current_folder = folder_name
                self.list_files()

    def go_back(self):
        if self.current_folder:
            parent = os.path.dirname(self.current_folder)
            self.current_folder = parent
            self.list_files()

    def browse_upload_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            self.upload_entry.delete(0, tk.END)
            self.upload_entry.insert(0, filepath)

    def browse_download_path(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_entry.delete(0, tk.END)
            self.download_entry.insert(0, folder)

    def upload_file(self):
        if not self.selected_bucket or not self.b2_api:
            messagebox.showerror("Error", "Please connect and select a bucket first")
            return

        filepath = self.upload_entry.get().strip()
        if not filepath:
            messagebox.showerror("Error", "Please select a file to upload")
            return

        if not os.path.exists(filepath):
            messagebox.showerror("Error", "File does not exist")
            return

        filename = os.path.basename(filepath)
        if self.current_folder:
            b2_filename = self.current_folder + '/' + filename
        else:
            b2_filename = filename

        self.status_label.config(text="Uploading...", fg="blue")
        self.progress['value'] = 0

        def upload_thread():
            try:
                bucket = self.b2_api.get_bucket_by_name(self.selected_bucket)
                upload_info = bucket.upload_local_file(
                    local_file=filepath,
                    file_name=b2_filename
                )
                self.root.after(0, self.upload_complete, True, "Upload successful!")
            except Exception as e:
                self.root.after(0, self.upload_complete, False, str(e))

        thread = threading.Thread(target=upload_thread)
        thread.daemon = True
        thread.start()

    def upload_complete(self, success, message):
        self.progress['value'] = 0
        if success:
            self.status_label.config(text=message, fg="green")
            self.list_files()
        else:
            self.status_label.config(text=f"Upload failed: {message}", fg="red")

    def download_file(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file first")
            return

        if not self.selected_bucket or not self.b2_api:
            messagebox.showerror("Error", "Please connect and select a bucket first")
            return

        # Check if it's a folder
        if self.selected_file.startswith("📁"):
            messagebox.showerror("Error", "Cannot download folders. Please select a file.")
            return

        download_path = self.download_entry.get().strip()
        if not os.path.exists(download_path):
            messagebox.showerror("Error", "Invalid download path")
            return

        # Extract actual filename from display
        display_name = self.selected_file[2:].strip()
        # Remove size info if present
        if '(' in display_name:
            display_name = display_name.rsplit('(', 1)[0].strip()

        # Build full B2 path
        if self.current_folder:
            b2_filename = self.current_folder + '/' + display_name
        else:
            b2_filename = display_name

        output_path = os.path.join(download_path, os.path.basename(b2_filename))

        self.status_label.config(text="Downloading...", fg="blue")
        self.progress['value'] = 0

        def download_thread():
            try:
                bucket = self.b2_api.get_bucket_by_name(self.selected_bucket)
                file_info = bucket.get_file_info_by_name(b2_filename)

                # Download with progress
                progress_listener = DownloadProgressListener(self)
                downloaded_file = bucket.download_file_by_name(
                    b2_filename,
                    progress_listener=progress_listener
                )

                # Save to file
                with open(output_path, 'wb') as f:
                    downloaded_file.save_to(f)

                self.root.after(0, self.download_complete, True, "Download successful!")
            except Exception as e:
                self.root.after(0, self.download_complete, False, str(e))

        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

    def download_complete(self, success, message):
        self.progress['value'] = 0
        if success:
            self.status_label.config(text=message, fg="green")
        else:
            self.status_label.config(text=f"Download failed: {message}", fg="red")

    def delete_file(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file first")
            return

        if not self.selected_bucket or not self.b2_api:
            messagebox.showerror("Error", "Please connect and select a bucket first")
            return

        # Check if it's a folder
        if self.selected_file.startswith("📁"):
            messagebox.showerror("Error", "Cannot delete folders via this interface yet.")
            return

        # Extract actual filename
        display_name = self.selected_file[2:].strip()
        if '(' in display_name:
            display_name = display_name.rsplit('(', 1)[0].strip()

        if self.current_folder:
            b2_filename = self.current_folder + '/' + display_name
        else:
            b2_filename = display_name

        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete {display_name}?"):
            return

        self.status_label.config(text="Deleting...", fg="blue")
        self.progress['value'] = 0

        def delete_thread():
            try:
                bucket = self.b2_api.get_bucket_by_name(self.selected_bucket)
                file_info = bucket.get_file_info_by_name(b2_filename)
                bucket.delete_file_version(file_info.id_, file_info.file_name)
                self.root.after(0, self.delete_complete, True, "Delete successful!")
            except Exception as e:
                self.root.after(0, self.delete_complete, False, str(e))

        thread = threading.Thread(target=delete_thread)
        thread.daemon = True
        thread.start()

    def delete_complete(self, success, message):
        self.progress['value'] = 0
        if success:
            self.status_label.config(text=message, fg="green")
            self.list_files()
        else:
            self.status_label.config(text=f"Delete failed: {message}", fg="red")

    def update_progress(self, value):
        self.progress['value'] = value


class DownloadProgressListener(DoNothingProgressListener):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.bytes_total = 0
        self.bytes_so_far = 0

    def set_total_bytes(self, total_bytes):
        self.bytes_total = total_bytes

    def bytes_completed(self, byte_count):
        self.bytes_so_far = byte_count
        if self.bytes_total > 0:
            progress = (self.bytes_so_far / self.bytes_total) * 100
            self.app.root.after(0, self.app.update_progress, progress)


if __name__ == "__main__":
    root = tk.Tk()
    app = B2Manager(root)
    root.mainloop()
