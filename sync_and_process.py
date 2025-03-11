import os
import subprocess
import time
from PyPDF2._page import PageObject
from PyPDF2 import PdfReader, PdfWriter

# Define paths
GOOGLE_DRIVE_FOLDER = "gdrive:/" + os.environ.get("GOOGLE_DRIVE_FOLDER", "Books")
LOCAL_DOWNLOAD_FOLDER = "/var/ftp/google_drive"
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
        temp2_pdf = output_path.replace(".pdf", "_2up.pdf")

        gs_command = [
            "pdfjam",
            "--outfile", temp2_pdf,
            "--landscape", "--nup", "2x1",
            "--paper", "a3paper",
            "--scale", "1.00",
            temp_pdf
        ]

        # Run pdfjam to impose booklet layout
        subprocess.run(gs_command, check=True)
        # Rotate every other page by 180 degrees (if needed)

        # Get total number of pages in the PDF
        with open(temp2_pdf, "rb") as f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)

        # Generate `pdftk` command
        flip_command = ["pdftk", temp2_pdf, "cat"]

        for i in range(1, total_pages + 1):
            if i % 2 == 0:  # Only flip even pages
                flip_command.append(f"{i}south")
            else:
                flip_command.append(str(i))  # Keep odd pages unchanged

        flip_command.extend(["output", output_path])

        subprocess.run(flip_command, check=True)

        print(f"Converted {pdf_path} to booklet format at {output_path}")

        # Cleanup temp files
        os.remove(temp_pdf)
        os.remove(temp2_pdf)

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        try:
            os.remove(temp_pdf)
            os.remove(temp2_pdf)
        except:
            pass

# Function to sync Google Drive and process PDFs
def sync_and_process_pdfs():
    while True:
        print("Syncing Google Drive...")
        try:
            subprocess.run(["rclone", "sync", GOOGLE_DRIVE_FOLDER, LOCAL_DOWNLOAD_FOLDER, '--include', '*.pdf'], check=True)
        except Exception as e:
            print(f"Error syncing Google Drive: {e}")

        print("Processing PDFs...")
        for folderpath, _, filelist in os.walk(LOCAL_DOWNLOAD_FOLDER):
            for filename in filelist:
                if filename.lower().endswith(".pdf"):
                    # set permissions
                    input_pdf = os.path.join(folderpath, filename)
                    booklet_folderpath = input_pdf.replace(".pdf", "_booklet.pdf")
                    booklet_folderpath = booklet_folderpath.replace(LOCAL_DOWNLOAD_FOLDER, BOOKLET_FOLDER)

                    # If PDF is not already in booklet format
                    if not os.path.exists(booklet_folderpath):
                        # Make the directory if it doesn't exist
                        os.makedirs(os.path.dirname(booklet_folderpath), exist_ok=True)
                        # Convert PDF to booklet format
                        convert_to_booklet(input_pdf, booklet_folderpath)
                    # convert_to_booklet(input_pdf, processed_pdf)

        print("Waiting for next sync...")
        time.sleep(600)  # Sync every 10 minutes

if __name__ == "__main__":
    sync_and_process_pdfs()
