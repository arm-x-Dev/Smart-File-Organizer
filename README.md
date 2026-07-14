#  Smart Photo & File Organizer

![Python Version](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python&logoColor=white)
![OS Compatibility](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-success?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Repo Status](https://img.shields.io/badge/Repo%20Status-Production%20Ready-brightgreen)

A modern, high-performance desktop application designed to catalog files and media instantly. Built with Python and Tkinter, it groups images, videos, and general documents into clean, flat, chronological timelines.

---

## Overview

The **Smart Photo & File Organizer** solves the chaos of cluttered download folders and unsorted camera rolls. It automatically scans any chosen directory and groups files by their metadata.

### Key Features
*   **Automatic Category Routing**: Automatically separates files into `/Media` and `/Other_Files` directories.
*   **Flat Chronological Timelines**: Places files in directories formatted as `DD-Month-YYYY` (e.g., `10-October-2025`).
*   **Duplicate Detection**: Employs cryptographic hash validation to detect and isolate duplicates.
*   **Modern Desktop Interface**: Crisp High-DPI UI scaling on Windows with real-time progress bars and status logging.

> [!IMPORTANT]
> **Backup Recommended**: It is always a good practice to keep a backup of your files before running organization workflows for extra safety

---

## Core Architecture & How It Works

This application is built for stability, data integrity, and non-blocking performance:

*   **Asynchronous Processing (Background Daemon)**: The main file processing loop runs inside a dedicated, daemonized background worker thread (`threading.Thread`). This keeps the Tkinter event loop fully fluid and responsive, preventing window freezes or "Not Responding" errors on large directories.
*   **Seamless Permission Isolation**: Every file-read, hash calculation, and `shutil.move` operation is isolated inside local `try-except (PermissionError, OSError)` blocks. If a file is locked or open in another application, the organizer safely registers it as skipped and proceeds with the rest of the directory without aborting.
*   **Cryptographic MD5 Hashing**: Rather than relying on fragile parameters like filename or size, the app reads files in 4096-byte streams to compute their MD5 signature. Exact matches are moved to a root `/Duplicates/` folder, protecting unique files from accidental overwrites.
*   **Pre-computed Collision Suffixes**: In the event of a naming conflict (e.g., different photos sharing a name like `IMG_0001.jpg`), a suffix handler automatically appends `_copy`, `_copy2`, etc., before the file is shifted.

---

## Download & Installation (Pre-compiled Binary)

For users who want to run the application immediately without installing Python:

1.  Navigate to the **Releases** tab in the repository.
2.  Download the `SmartOrganizer_Setup.zip` package.
3.  Extract the contents to a local directory.
4.  Launch the `SmartOrganizer.exe` executable or run the installer to create a desktop shortcut.

---

## Developer Setup & Source Code Execution

To run the application from source or contribute to development, follow these steps:

### Prerequisites
*   Python 3.13 or higher installed globally.

### Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/arm-x-Dev/Smart-File-Organizer.git
    cd Smart-File-Organizer
    ```

2.  **Initialize the Virtual Environment**:
    Create a clean, isolated environment to run the code:
    ```powershell
    python -m venv venv
    ```

3.  **Activate the Environment**:
    *   **Windows (PowerShell)**:
        ```powershell
        Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
        .\venv\Scripts\Activate.ps1
        ```
    *   **macOS / Linux**:
        ```bash
        source venv/bin/activate
        ```

4.  **Launch the Application**:
    Start the organizer GUI directly using Python:
    ```bash
    python organizer.py
    ```

---

## Security & Validation Audit

This codebase has undergone a comprehensive production-grade safety review. 
*   No destructive deletion routines (such as `os.remove` or `shutil.rmtree`) exist in the application pipeline.
*   For the complete security log, error handling specs, and thread-safety review, see [review.md](file:///d:/File%20Organizer/review.md).

---

## Contributor

*   **Alok Muranal** - [arm-x-Dev](https://github.com/arm-x-Dev)
