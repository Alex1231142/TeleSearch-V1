# 📜 README for TeleSearch V1

## 📦 Description

**TeleSearch V1** is a powerful script for searching and processing files in Telegram channels. It downloads messages from a channel, searches for the specified text in various file formats, and outputs the results to log files. The script uses asynchronous methods and multithreading for maximum performance.

## 🛠 Installation

1. **Clone the repository**

    ```bash
    git clone <repository URL>
    cd <folder_name>
    ```

2. **Create and activate a virtual environment**

    ```bash
    python -m venv venv
    source venv/bin/activate  # For Unix
    venv\Scripts\activate     # For Windows
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

## 🔧 Configuration

1. **Create a `config.json` configuration file**

    Example content:

    ```json
    {
      "api_id": "",
      "api_hash": "",
      "phone_number": "",
      "channel_username": "",
      "results_file": "results.txt",
      "max_workers": 100,
      "semaphore_limit": 100,
      "logging_level": "INFO"
    }
    ```

    **Configuration parameters:**

    - **`api_id`**: Your API ID obtained from Telegram.
    - **`api_hash`**: Your API Hash obtained from Telegram.
    - **`phone_number`**: Your phone number for authentication.
    - **`channel_username`**: The username of the channel to search files in.
    - **`results_file`**: The name of the file where search results will be saved.
    - **`max_workers`**: The number of threads for file processing.
    - **`semaphore_limit`**: Semaphore limit for concurrent requests.
    - **`logging_level`**: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).

2. **Ensure you have the required libraries installed**

    Ensure that `requirements.txt` lists all necessary dependencies:

    ```text
    telethon
    pdfplumber
    pandas
    tqdm
    rarfile
    ```

## 🚀 Running

1. **Run the script**

    ```bash
    python main.py
    ```

2. **Enter search data**

    After starting, the script will prompt you to enter the search text. Enter the desired text and press Enter.

## 📜 Usage

- The script connects to the Telegram API and downloads messages from the specified channel.
- It processes files of various formats (PDF, CSV, XLSX, GZ, ZIP, RAR).
- Search results are saved to `results.txt`.
- Error logs are saved to `errors.txt`.

## ⚙ Performance Settings

1. **Increasing the number of threads and semaphores**

    You can increase the `max_workers` and `semaphore_limit` parameters in the configuration file to boost performance.

2. **Optimizing file loading and processing**

    The script loads files asynchronously and processes them in a streaming mode for better efficiency.

3. **Increasing virtual machine resources**

    If necessary, increase the allocated CPU and RAM resources in your execution environment.

4. **Checking Telegram API limits**

    Ensure that you do not exceed Telegram API request limits.

5. **Parallel file processing**

    The script supports parallel file processing to enhance speed.

## 📜 Important Notes

- This is the first version of the script (V1), so future updates may include new features and fixes.
- Before using, ensure your Telegram API credentials and configuration parameters are correct.

---

Thank you for using **TeleSearch V1**! 🚀
