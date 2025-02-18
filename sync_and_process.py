import os
import subprocess
import time
from PyPDF2 import PdfReader, PdfWriter

# Define paths
GOOGLE_DRIVE_FOLDER = "gdrive:/your-folder"  # Change to your folder path
LOCAL_DOWNLOAD_FOLDER = "/data/google_drive"
UNPROCESSED_FOLDER = "/var/ftp/unprocessed"
BOOKLET_FOLDER = "/var/ftp/booklets"

# Ensure directories exist
os.makedirs(LOCAL_DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(UNPROCESSED_FOLDER, exist_ok=True)
os.makedirs(BOOKLET_FOLDER, exist_ok=True)

# Function to convert PDF to booklet format
def convert_to_booklet(pdf_path, output_path):
    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        pages = reader.pages
        total_pages = len(pages)

        # Ensure even number of pages
        if total_pages % 2 != 0:
            pages.append(None)

        for i in range(0, len(pages), 2):
            if pages[i + 1] is not None:
                writer.add_page(pages[i + 1])
            writer.add_page(pages[i])

        with open(output_path, "wb") as out_file:
            writer.write(out_file)

        print(f"Converted {pdf_path} to booklet format at {output_path}")

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

# Function to sync Google Drive and process PDFs
def sync_and_process_pdfs():
    while True:
        print("Syncing Google Drive...")
        subprocess.run(["rclone", "sync", GOOGLE_DRIVE_FOLDER, LOCAL_DOWNLOAD_FOLDER], check=True)

        print("Processing PDFs...")
        for filename in os.listdir(LOCAL_DOWNLOAD_FOLDER):
            if filename.lower().endswith(".pdf"):
                input_pdf = os.path.join(LOCAL_DOWNLOAD_FOLDER, filename)
                unprocessed_pdf = os.path.join(UNPROCESSED_FOLDER, filename)
                processed_pdf = os.path.join(BOOKLET_FOLDER, f"booklet_{filename}")

                # Copy original PDF to FTP unprocessed folder
                subprocess.run(["cp", input_pdf, unprocessed_pdf], check=True)

                # Convert PDF to booklet format
                convert_to_booklet(input_pdf, processed_pdf)

        print("Waiting for next sync...")
        time.sleep(600)  # Sync every 10 minutes

if __name__ == "__main__":
    sync_and_process_pdfs()
