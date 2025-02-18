FROM ubuntu:latest

# Install required packages
RUN apt-get update && apt-get install -y \
    rclone \
    python3 \
    python3-venv \
    python3-pip \
    ghostscript \
    poppler-utils \
    texlive-latex-base \
    texlive-extra-utils \
    texlive-fonts-recommended \
    vsftpd \
    && apt-get clean

# Create a virtual environment and install dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir PyPDF2

# Copy script files
COPY sync_and_process.py /usr/local/bin/
COPY vsftpd.conf /etc/vsftpd.conf
COPY entrypoint.sh /usr/local/bin/

# Set execute permissions
RUN chmod +x /usr/local/bin/entrypoint.sh

# Ensure directories exist
RUN mkdir -p /data/google_drive /data/booklets /var/ftp/unprocessed /var/ftp/booklets

# Expose FTP ports
EXPOSE 21 10000-10100

# Start the script and FTP server
CMD ["/usr/local/bin/entrypoint.sh"]
