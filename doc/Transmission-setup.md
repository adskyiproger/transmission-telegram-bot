
1. **Connect External Hard Drive:**
   Plug in your external hard drive to the Raspberry Pi.

2. **Identify the Drive:**
   Use the command `lsblk` or `fdisk -l` to identify the device name of your external hard drive, such as `/dev/sda1`.

3. **Create Mount Point:**
   Decide where you want to mount the drive. For example, let's use `/data`.

   ```bash
   sudo mkdir /data
   ```

4. **Mount the Drive:**
   Use the `mount` command to mount the drive to the designated mount point.

   ```bash
   sudo mount /dev/sda1 /data
   ```

5. **Make Mount Permanent:**
   Edit the `/etc/fstab` file to ensure the drive is mounted on boot.

   ```bash
   sudo nano /etc/fstab
   ```

   Add the following line at the end of the file:

   ```
   /dev/sda1 /data ext4 defaults 0 2
   ```

   Save and exit the text editor.

6. **Create Directories:**
   Inside the mounted drive, create the desired directories.

   ```bash
   sudo mkdir /data/video /data/books /data/software /data/music /data/incomplete
   ```

7. **Install Transmission:**
   Install the Transmission BitTorrent server.

   ```bash
   sudo apt update
   sudo apt install transmission-daemon
   ```

8. **Configure Transmission:**
   Stop the Transmission service before modifying the settings.

   ```bash
   sudo service transmission-daemon stop
   ```

   Edit the Transmission settings file:

   ```bash
   sudo nano /etc/transmission-daemon/settings.json
   ```

   Set `"incomplete-dir": "/data/incomplete"` and `"incomplete-dir-enabled": true`.

9. **User Authentication:**
   Uncomment the `"rpc-authentication-required": true` line.
   
   Set your username and password:

   ```json
   "rpc-username": "test",
   "rpc-password": "pass",
   ```

10. **Permissions:**
    Change ownership of the `/data` directory to the Transmission user:

    ```bash
    sudo chown -R debian-transmission:debian-transmission /data
    ```

11. **Start Transmission:**
    Start the Transmission service.

    ```bash
    sudo service transmission-daemon start
    ```

12. **Access Transmission Web Interface:**
    Open your web browser and enter your Raspberry Pi's IP address followed by the port number `9091`. For example, `http://raspberry_pi_ip:9091`.

13. **Login:**
    Enter the username and password you set earlier.
