FROM ubuntu:latest

# Install required packages
RUN apt-get update && apt-get install -y \
    rclone \
    python3 \
    python3-pip \
    ghostscript \
    poppler-utils \
    vsftpd \
    && apt-get clean

# Install Python dependencies for PDF manipulation
RUN pip3 install PyPDF2 pdfbook

# Copy script files
COPY sync_and_process.py /usr/local/bin/
COPY vsftpd.conf /etc/vsftpd.conf
COPY entrypoint.sh /usr/local/bin/

# Create necessary directories
RUN mkdir -p /data/google_drive /data/booklets /var/ftp/unprocessed /var/ftp/booklets

# Set permissions
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose FTP ports
EXPOSE 21 10000-10100

# Start script and FTP server
CMD ["/usr/local/bin/entrypoint.sh"]
