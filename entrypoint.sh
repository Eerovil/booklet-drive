#!/bin/bash

# Check if user exists, if not create it
if ! id "$FTP_USER" &>/dev/null; then
    echo "Creating FTP user: $FTP_USER"
    useradd -m -d /var/ftp -s /usr/sbin/nologin $FTP_USER
fi
echo "$FTP_USER:$FTP_PASS" | chpasswd

# Set up FTP directories
mkdir -p /var/ftp/google_drive /var/ftp/booklets
chown -R $FTP_USER:$FTP_USER /var/ftp

# Start Google Drive sync & processing script in the background
python3 /usr/local/bin/sync_and_process.py &

# Start FTP server
vsftpd /etc/vsftpd.conf
