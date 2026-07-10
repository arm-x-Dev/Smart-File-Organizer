import os
import sys
import shutil
import string
import hashlib
import re
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Enable High-DPI awareness on Windows
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

def get_attached_drives():
    drives = []
    if sys.platform == 'win32':
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    else:
        # Default root
        drives.append('/')
        # Common mount points for Mac/Linux
        for mount_dir in ['/media', '/mnt', '/Volumes']:
            if os.path.exists(mount_dir):
                try:
                    for item in os.listdir(mount_dir):
                        path = os.path.join(mount_dir, item)
                        if os.path.isdir(path):
                            drives.append(path)
                except Exception:
                    pass
    return drives

def get_file_md5(file_path):
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def is_generic_name(base, is_media):
    base_lower = base.lower()
    
    # Generic prefixes
    media_prefixes = ('img', 'dsc', 'image', 'photo', 'screenshot', 'download', 'pic', 'video', 'vid', 'mvp')
    doc_prefixes = ('scan', 'document', 'doc', 'download', 'new_document', 'untitled')
    
    prefixes = media_prefixes if is_media else doc_prefixes
    
    # Check starts with generic prefixes
    for prefix in prefixes:
        if base_lower.startswith(prefix):
            return True
            
    # Check if purely numeric/dashes/underscores (like system generated timestamps)
    if re.match(r'^[0-9_\-]+$', base):
        return True
        
    # Check UUID pattern
    if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', base_lower):
        return True
        
    # Check long random hex strings (e.g. hash names, >= 8 hex chars)
    if len(base) >= 8 and re.match(r'^[a-f0-9]+$', base_lower):
        return True
        
    return False

def get_next_sequence_num(dest_dir, prefix, cache):
    key = (dest_dir, prefix)
    if key in cache:
        num = cache[key]
        cache[key] = num + 1
        return num
        
    # scan dest_dir to find highest counter
    max_num = 0
    pattern = re.compile(rf'^{prefix}_(\d{{4}})\.')
    if os.path.exists(dest_dir):
        try:
            for name in os.listdir(dest_dir):
                match = pattern.match(name)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
        except Exception:
            pass
    next_num = max_num + 1
    cache[key] = next_num + 1
    return next_num

def organize_photos(target_folder, progress_callback=None):
    media_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.3gp', '.3gpp', '.mkv', '.wmv')
    moved_count = 0
    duplicate_count = 0
    skipped_count = 0
    seen_hashes = set()
    seq_cache = {}
    
    # Scan target directory to count total files first
    total_files = 0
    try:
        for entry in os.scandir(target_folder):
            if entry.is_file():
                total_files += 1
    except Exception:
        pass
            
    if progress_callback:
        progress_callback(total=total_files)
        
    # Scan the target folder for ALL files (top-level only)
    for entry in os.scandir(target_folder):
        if entry.is_file():
            try:
                ext_orig = os.path.splitext(entry.name)[1]
                ext_lower = ext_orig.lower()
                file_path = entry.path
                
                if progress_callback:
                    progress_callback(current_file=entry.name)
                
                # Calculate MD5 hash safely
                file_hash = get_file_md5(file_path)
                if file_hash is None:
                    skipped_count += 1
                    if progress_callback:
                        progress_callback(step=1)
                    continue
                    
                is_media = ext_lower in media_extensions
                
                if file_hash in seen_hashes:
                    # Duplicate file - route to Duplicates folder
                    dest_dir = os.path.join(target_folder, 'Duplicates')
                    os.makedirs(dest_dir, exist_ok=True)
                    duplicate_count += 1
                    final_name = entry.name
                else:
                    # Unique file - register hash and determine standard destination
                    seen_hashes.add(file_hash)
                    
                    # Determine destination root category folder
                    if is_media:
                        category = 'Media'
                        prefix = 'PHOTO'
                    else:
                        category = 'Other_Files'
                        prefix = 'DOC'
                        
                    # Get modification time (mtime is standard across systems)
                    mtime = os.path.getmtime(file_path)
                    dt = datetime.fromtimestamp(mtime)
                    
                    # Format the folder name as 'DD-Month-YYYY' (flat timeline structure)
                    date_folder = dt.strftime("%d-%B-%Y")
                    
                    # Create destination directory (Category/DateFolder)
                    dest_dir = os.path.join(target_folder, category, date_folder)
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    # Determine if filename is generic/system name
                    base_name = os.path.splitext(entry.name)[0]
                    if is_generic_name(base_name, is_media):
                        num = get_next_sequence_num(dest_dir, prefix, seq_cache)
                        final_name = f"{prefix}_{num:04d}{ext_orig}"
                    else:
                        final_name = entry.name
                
                # Handle duplicates path collisions in the destination folder
                base_dest, ext_dest = os.path.splitext(final_name)
                dest_path = os.path.join(dest_dir, final_name)
                
                counter = 1
                while os.path.exists(dest_path):
                    suffix = f"_copy{counter}" if counter > 1 else "_copy"
                    dest_path = os.path.join(dest_dir, f"{base_dest}{suffix}{ext_dest}")
                    counter += 1
                
                shutil.move(file_path, dest_path)
                moved_count += 1
            except (PermissionError, OSError):
                skipped_count += 1
                
            if progress_callback:
                progress_callback(step=1)
            
    return moved_count, duplicate_count, skipped_count

class SmartPhotoOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Smart Photo Organizer")
        self.root.geometry("600x420")
        self.root.resizable(False, False)
        
        # Configure layout and styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Color palette (modern, clean gray and blue look)
        self.style.configure('.', background='#f4f5f7')
        self.style.configure('TFrame', background='#f4f5f7')
        self.style.configure('TLabel', font=('Segoe UI', 10), background='#f4f5f7', foreground='#333333')
        self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), background='#f4f5f7', foreground='#2c3e50')
        self.style.configure('TButton', font=('Segoe UI', 10), padding=6)
        self.style.configure('Browse.TButton', font=('Segoe UI', 10, 'bold'))
        
        # Style for the main Action button
        self.style.configure('Action.TButton', font=('Segoe UI', 12, 'bold'), padding=10, background='#3498db', foreground='white')
        self.style.map('Action.TButton',
                       background=[('active', '#2980b9'), ('disabled', '#bdc3c7')],
                       foreground=[('disabled', '#7f8c8d')])
        
        # Progressbar styling
        self.style.configure('Clean.Horizontal.TProgressbar', thickness=12, troughcolor='#e0e0e0', background='#3498db')

        # Main container
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header Section
        header_label = ttk.Label(main_frame, text="⚡ Smart Photo Organizer", style='Title.TLabel')
        header_label.pack(anchor=tk.W, pady=(0, 15))
        
        desc_label = ttk.Label(main_frame, text="Select a drive and target folder to organize your photos by date.")
        desc_label.pack(anchor=tk.W, pady=(0, 20))

        # 2. Drive Selection Row
        drive_frame = ttk.Frame(main_frame)
        drive_frame.pack(fill=tk.X, pady=(0, 15))
        
        drive_label = ttk.Label(drive_frame, text="Source Drive:", width=15, anchor=tk.W)
        drive_label.pack(side=tk.LEFT)
        
        self.drives = get_attached_drives()
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(drive_frame, textvariable=self.drive_var, values=self.drives, state="readonly", width=10)
        self.drive_combo.pack(side=tk.LEFT)
        if self.drives:
            self.drive_combo.set(self.drives[0])
        
        self.drive_combo.bind("<<ComboboxSelected>>", self.on_drive_changed)

        # 3. Folder Selection Row
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        folder_label = ttk.Label(folder_frame, text="Target Folder:", width=15, anchor=tk.W)
        folder_label.pack(side=tk.LEFT)
        
        self.browse_btn = ttk.Button(folder_frame, text="Browse...", style='Browse.TButton', command=self.browse_folder)
        self.browse_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Path display (read-only entry)
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, state="readonly")
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 4. Spacer
        spacer = ttk.Frame(main_frame)
        spacer.pack(fill=tk.BOTH, expand=True)

        # 5. Progress Bar & Status (packed in order: organize_btn bottom-most, status_label above it, progress_bar above status_label)
        self.status_var = tk.StringVar(value="Select a folder to begin.")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, font=('Segoe UI', 10, 'italic'), foreground='#7f8c8d')
        
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate', style='Clean.Horizontal.TProgressbar')
        
        # Packing layout
        self.organize_btn = ttk.Button(main_frame, text="ORGANIZE NOW", style='Action.TButton', state=tk.DISABLED, command=self.run_organization)
        self.organize_btn.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self.status_label.pack(side=tk.BOTTOM, pady=(5, 5))
        self.progress_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 5))

    def on_drive_changed(self, event):
        # Option to reset folder path if the drive changes
        pass

    def browse_folder(self):
        initial_dir = self.drive_var.get()
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = None
            
        selected = filedialog.askdirectory(title="Select Folder to Organize", initialdir=initial_dir)
        if selected:
            selected = os.path.normpath(selected)
            self.folder_var.set(selected)
            self.organize_btn.config(state=tk.NORMAL)
            self.status_var.set("Ready to organize.")

    def run_organization(self):
        target_folder = self.folder_var.get()
        if not target_folder or not os.path.exists(target_folder):
            messagebox.showerror("Error", "Selected target folder does not exist.")
            return
        
        # Disable all UI inputs during processing
        self.set_ui_state(tk.DISABLED)
        self.progress_bar['value'] = 0
        self.status_var.set("Starting organization...")
        
        def update_progress(total=None, current_file=None, step=None):
            # Schedule updates safely on the main thread
            self.root.after(0, self._safe_update_progress, total, current_file, step)
            
        def worker():
            try:
                moved_count, duplicate_count, skipped_count = organize_photos(target_folder, progress_callback=update_progress)
                self.root.after(0, self.on_organization_complete, moved_count, duplicate_count, skipped_count)
            except Exception as e:
                self.root.after(0, self.on_organization_error, str(e))
                
        # Start background thread
        threading.Thread(target=worker, daemon=True).start()

    def _safe_update_progress(self, total=None, current_file=None, step=None):
        if total is not None:
            self.progress_bar['maximum'] = total
            self.progress_bar['value'] = 0
        if current_file is not None:
            self.status_var.set(f"Processing: {current_file}...")
        if step is not None:
            self.progress_bar['value'] += step

    def on_organization_complete(self, moved_count, duplicate_count, skipped_count):
        # Fill progress bar completely
        self.progress_bar['value'] = self.progress_bar['maximum']
        
        status_msg = f"Success! Organized {moved_count} files. Found {duplicate_count} duplicates. Skipped {skipped_count}."
        self.status_var.set(status_msg)
        
        # Re-enable all UI controls
        self.set_ui_state(tk.NORMAL)
        
        messagebox.showinfo("Success", f"Organization Complete!\nSuccessfully moved {moved_count} total files.\n({duplicate_count} duplicates moved, {skipped_count} skipped due to locks/permissions)")

    def on_organization_error(self, err_msg):
        self.status_var.set("Error during organization.")
        self.set_ui_state(tk.NORMAL)
        messagebox.showerror("Error", f"An error occurred during organization:\n{err_msg}")

    def set_ui_state(self, state):
        self.organize_btn.config(state=state)
        self.browse_btn.config(state=state)
        self.drive_combo.config(state="readonly" if state == tk.NORMAL else tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartPhotoOrganizerApp(root)
    root.mainloop()
