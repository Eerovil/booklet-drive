import os
import subprocess
import time
from PyPDF2._page import PageObject
from PyPDF2 import PdfReader, PdfWriter

# Define paths
GOOGLE_DRIVE_FOLDER = "gdrive:/" + os.environ.get("GOOGLE_DRIVE_FOLDER", "Books")
LOCAL_DOWNLOAD_FOLDER = "/data/google_drive"
BOOKLET_FOLDER = "/var/ftp/booklets"

# Ensure directories exist
os.makedirs(LOCAL_DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(BOOKLET_FOLDER, exist_ok=True)

# Function to ensure pages are a multiple of 4 for booklet printing
def ensure_multiple_of_four(pages):
    while len(pages) % 4 != 0:
        blank_page = PageObject.create_blank_page(width=pages[0].mediabox.width,
                                                  height=pages[0].mediabox.height)
        pages.append(blank_page)
    return pages

# Function to create booklet-imposed PDF
def convert_to_booklet(pdf_path, output_path):
    try:
        # Step 1: Load PDF
        reader = PdfReader(pdf_path)
        pages = list(reader.pages)
        total_pages = len(pages)

        if total_pages == 1:
            return  # Skip single-page PDFs

        # Step 2: Rearrange pages for booklet format
        booklet_order = []

        if total_pages == 2:
            # Special case for 2-page PDFs
            booklet_order = [pages[0], pages[1]]
        else:
            pages = ensure_multiple_of_four(pages)  # Ensure page count is a multiple of 4
            total_pages = len(pages)

            left = 0
            right = total_pages - 1

            while left < right:
                booklet_order.append(pages[right])  # Last page
                booklet_order.append(pages[left])   # First page
                left += 1
                right -= 1
                if left < right:
                    booklet_order.append(pages[left])  # Second page
                    booklet_order.append(pages[right]) # Second-last page
                    left += 1
                    right -= 1

        # Step 3: Save reordered pages as temporary PDF
        temp_pdf = output_path.replace(".pdf", "_reordered.pdf")
        writer = PdfWriter()
        for page in booklet_order:
            writer.add_page(page)
        with open(temp_pdf, "wb") as f:
            writer.write(f)

        # Step 4: Use Ghostscript or pdfjam for 2-up booklet imposition
        final_booklet = output_path.replace(".pdf", "_booklet.pdf")

        gs_command = [
            "pdfjam",
            "--outfile", final_booklet,
            "--landscape", "--nup", "2x1",
            "--paper", "a4paper",
            "--scale", "1.00",
            temp_pdf
        ]

        # Run pdfjam to impose booklet layout
        subprocess.run(gs_command, check=True)

        print(f"Converted {pdf_path} to booklet format at {final_booklet}")

        # Cleanup temp files
        os.remove(temp_pdf)

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        try:
            os.remove(temp_pdf)
        except:
            pass

# Function to sync Google Drive and process PDFs
def sync_and_process_pdfs():
    while True:
        print("Syncing Google Drive...")
        subprocess.run(["rclone", "sync", GOOGLE_DRIVE_FOLDER, LOCAL_DOWNLOAD_FOLDER], check=True)

        print("Processing PDFs...")
        for filename in os.listdir(LOCAL_DOWNLOAD_FOLDER):
            if filename.lower().endswith(".pdf"):
                input_pdf = os.path.join(LOCAL_DOWNLOAD_FOLDER, filename)
                booklet_filename = filename.replace(".pdf", "_booklet.pdf")
                processed_pdf = os.path.join(BOOKLET_FOLDER, booklet_filename)

                # If PDF is not already in booklet format
                if not os.path.exists(processed_pdf):
                    # Convert PDF to booklet format
                    convert_to_booklet(input_pdf, processed_pdf)
                # convert_to_booklet(input_pdf, processed_pdf)

        print("Waiting for next sync...")
        time.sleep(600)  # Sync every 10 minutes

if __name__ == "__main__":
    sync_and_process_pdfs()
