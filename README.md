This readme was generated with gemini.

# Simple Fromm Video Downloader CLI

This script allows you to easily generate a `yt-dlp` command to download videos from Fromm by either authenticating with your credentials or using an existing Bearer token.

## Prerequisites

Before running the script, ensure you have the required dependencies installed:

```bash
pip install pycryptodome requests

```

You also need [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) installed and added to your system's PATH for the automatic download feature to work.

---

## 1. Command to Generate Your Token

If you don't have a Bearer token or if your previous one expired, use this command to authenticate via your email and password. This will log you in, generate a random device UUID, and output your fresh token. This token will last 14 days.

```bash
python fromm_dl.py --generate-token -e "your_email@example.com" -p "YourPassword123"

```

* **What it does:** Authenticates with the Fromm API, prints your token to the console, and exits without downloading anything.

---

## 2. Command to Download the Video

Once you have your Bearer token, use this command to parse the shortlink and automatically start the video download via `yt-dlp`. You can also specify exactly where you want the file saved using the `-o` flag.

```bash
python fromm_dl.py https://fromm.my/1ps1e0 -t "YOUR_BEARER_TOKEN_HERE" -o "C:/Users/maxen/Downloads/fromis_video.mp4"

```

* **`https://fromm.my/1ps1e0`**: The target Fromm shortlink.
* **`-t`**: Your active Bearer token (copied from Step 1).
* **`-o`**: (Optional) The absolute path and filename where you want to save the final file. (just like the -o option in `yt-dlp`)
