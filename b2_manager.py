import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class B2Manager:
    def __init__(self, root):
        self.root = root
        self.root.title("B2 Cloud Storage Manager")
        self.root.geometry("900x650")
        self.root.resizable(False, False)

        self.selected_bucket = None
        self.selected_file = None
        self.b2_exe = self.get_b2_path()

        self.create_widgets()

    def get_b2_path(self):
        # Check if running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Check in current directory
        b2_path = os.path.join(os.getcwd(), "b2-windows.exe")
        if os.path.exists(b2_path):
            return b2_path

        # Check in bundle directory
        b2_path = os.path.join(base_path, "b2-windows.exe")
        if os.path.exists(b2_path):
            return b2_path

        # Check if b2 is in PATH
        try:
            subprocess.run(["b2", "--version"], capture_output=True, check=True)
            return "b2"
        except:
            return None

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

        self.file_listbox = tk.Listbox(file_frame, font=("Arial", 9), selectmode=tk.SINGLE)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

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
        self.progress = ttk.Progressbar(self.root, mode='indeterminate', length=800)
        self.progress.pack(pady=5)

        # Status Label
        self.status_label = tk.Label(self.root, text="Ready", font=("Arial", 9), fg="gray")
        self.status_label.pack(pady=5)

        # Check b2 executable
        if not self.b2_exe:
            self.status_label.config(text="Warning: b2-windows.exe not found!", fg="red")

    def run_command(self, command):
        try:
            if self.b2_exe and os.path.exists(self.b2_exe):
                cmd = [self.b2_exe] + command.split()[1:]
            else:
                cmd = command.split()

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return e.stderr
        except Exception as e:
            return str(e)

    def set_env_and_run(self, key_id, key, command):
        env = os.environ.copy()
        env['B2_APPLICATION_KEY_ID'] = key_id
        env['B2_APPLICATION_KEY'] = key

        try:
            if self.b2_exe and os.path.exists(self.b2_exe):
                cmd = [self.b2_exe] + command.split()[1:]
            else:
                cmd = command.split()

            result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return e.stderr
        except Exception as e:
            return str(e)

    def connect_to_b2(self):
        key_id = self.key_id_entry.get().strip()
        key = self.key_entry.get().strip()

        if not key_id or not key:
            messagebox.showerror("Error", "Please enter Key ID and Key")
            return

        self.status_label.config(text="Connecting...", fg="blue")
        self.progress.start()

        def connect_thread():
            result = self.set_env_and_run(key_id, key, "b2 account authorize")
            self.root.after(0, self.connect_complete, result)

        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()

    def connect_complete(self, result):
        self.progress.stop()
        if "accountId" in result:
            self.status_label.config(text="Connected successfully!", fg="green")
            self.list_buckets()
        else:
            self.status_label.config(text="Connection failed. Check your keys.", fg="red")

    def list_buckets(self):
        result = self.run_command("b2 bucket list")
        self.bucket_listbox.delete(0, tk.END)

        lines = result.split('\n')
        for line in lines:
            if line.strip() and "accountId" not in line:
                parts = line.strip().split()
                if len(parts) >= 3:
                    self.bucket_listbox.insert(tk.END, parts[2])

    def on_bucket_select(self, event):
        selection = self.bucket_listbox.curselection()
        if selection:
            self.selected_bucket = self.bucket_listbox.get(selection[0])
            self.list_files()

    def list_files(self):
        if not self.selected_bucket:
            return

        result = self.run_command(f"b2 ls b2://{self.selected_bucket}")
        self.file_listbox.delete(0, tk.END)

        lines = result.split('\n')
        for line in lines:
            if line.strip():
                self.file_listbox.insert(tk.END, line.strip())

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            self.selected_file = self.file_listbox.get(selection[0])

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
        if not self.selected_bucket:
            messagebox.showerror("Error", "Please select a bucket first")
            return

        filepath = self.upload_entry.get().strip()
        if not filepath:
            messagebox.showerror("Error", "Please select a file to upload")
            return

        if not os.path.exists(filepath):
            messagebox.showerror("Error", "File does not exist")
            return

        filename = os.path.basename(filepath)

        self.status_label.config(text="Uploading...", fg="blue")
        self.progress.start()

        def upload_thread():
            result = self.run_command(f"b2 file upload {self.selected_bucket} \"{filepath}\" \"{filename}\"")
            self.root.after(0, self.upload_complete, result)

        thread = threading.Thread(target=upload_thread)
        thread.daemon = True
        thread.start()

    def upload_complete(self, result):
        self.progress.stop()
        if "fileId" in result:
            self.status_label.config(text="Upload successful!", fg="green")
            self.list_files()
        else:
            self.status_label.config(text="Upload failed.", fg="red")

    def download_file(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file first")
            return

        if not self.selected_bucket:
            messagebox.showerror("Error", "Please select a bucket first")
            return

        download_path = self.download_entry.get().strip()
        if not os.path.exists(download_path):
            messagebox.showerror("Error", "Invalid download path")
            return

        filename = self.selected_file.split('/')[-1] if '/' in self.selected_file else self.selected_file
        output_path = os.path.join(download_path, filename)

        self.status_label.config(text="Downloading...", fg="blue")
        self.progress.start()

        def download_thread():
            result = self.run_command(f"b2 file download b2://{self.selected_bucket}/{self.selected_file} \"{output_path}\"")
            self.root.after(0, self.download_complete, result)

        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

    def download_complete(self, result):
        self.progress.stop()
        if "Download finished" in result or "File size:" in result:
            self.status_label.config(text="Download successful!", fg="green")
        else:
            self.status_label.config(text="Download failed.", fg="red")

    def delete_file(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file first")
            return

        if not self.selected_bucket:
            messagebox.showerror("Error", "Please select a bucket first")
            return

        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete {self.selected_file}?"):
            return

        self.status_label.config(text="Deleting...", fg="blue")
        self.progress.start()

        def delete_thread():
            result = self.run_command(f"b2 file delete b2://{self.selected_bucket}/{self.selected_file}")
            self.root.after(0, self.delete_complete, result)

        thread = threading.Thread(target=delete_thread)
        thread.daemon = True
        thread.start()

    def delete_complete(self, result):
        self.progress.stop()
        if "fileId" in result or "fileName" in result:
            self.status_label.config(text="Delete successful!", fg="green")
            self.list_files()
        else:
            self.status_label.config(text="Delete failed.", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = B2Manager(root)
    root.mainloop()
