
1. **Підключення зовнішнього жорсткого диска:**
   Підключіть зовнішній жорсткий диск до Raspberry Pi.

2. **Визначте пристрій:**
   Використовуйте команду `lsblk` або `fdisk -l`, щоб визначити ім'я пристрою вашого зовнішнього жорсткого диска, наприклад, `/dev/sda1`.

3. **Створити точку монтування:**
   Вирішіть, куди ви хочете прикріпити диск. Наприклад, давайте використовувати `/data`.

   ```bash
   sudo mkdir /data
   ```

4. **Монтування диска:**
   Використовуйте команду `mount`, щоб прикріпити диск до визначеної точки монтування.

   ```bash
   sudo mount /dev/sda1 /data
   ```

5. **Зробіть монтування постійним:**
   Редагуйте файл `/etc/fstab`, щоб переконатися, що диск буде монтуватися при завантаженні.

   ```bash
   sudo nano /etc/fstab
   ```

   Додайте наступний рядок в кінці файлу:

   ```
   /dev/sda1 /data ext4 defaults 0 2
   ```

   Збережіть і закрийте текстовий редактор.

6. **Створити директорії:**
   В монтованому диску створіть бажані директорії.

   ```bash
   sudo mkdir /data/video /data/books /data/software /data/music /data/incomplete
   ```

7. **Встановіть Transmission:**
   Встановіть сервер BitTorrent Transmission.

   ```bash
   sudo apt update
   sudo apt install transmission-daemon
   ```

8. **Налаштування Transmission:**
   Зупиніть службу Transmission перед зміною налаштувань.

   ```bash
   sudo service transmission-daemon stop
   ```

   Відредагуйте файл налаштувань Transmission:

   ```bash
   sudo nano /etc/transmission-daemon/settings.json
   ```

   Встановіть `"incomplete-dir": "/data/incomplete"` і `"incomplete-dir-enabled": true`.

9. **Аутентифікація користувача:**
   Розкоментуйте рядок `"rpc-authentication-required": true`.
   
   Встановіть ваше ім'я користувача та пароль:

   ```json
   "rpc-username": "test",
   "rpc-password": "pass",
   ```

10. **Дозволи:**
    Змініть власника директорії `/data` на користувача Transmission:

    ```bash
    sudo chown -R debian-transmission:debian-transmission /data
    ```

11. **Запустіть Transmission:**
    Запустіть службу Transmission.

    ```bash
    sudo service transmission-daemon start
    ```

12. **Отримайте доступ до веб-інтерфейсу Transmission:**
    Відкрийте веб-браузер та введіть IP-адресу вашого Raspberry Pi, за яким слідує номер порту `9091`. Наприклад, `http://ip_адреса_raspberry_pi:9091`.

13. **Увійдіть:**
    Введіть ім'я користувача та пароль, які ви встановили раніше.
