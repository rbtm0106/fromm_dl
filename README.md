Disclaimer
Your accound need to have access to the video to downlaod it... When you generate your fromm token, it will log you out, but the token is valid 14 days, you can log back on the fromm app.
The script is very simple and can be improve, you can ask gemini, gpt or other llm to help you improve it!
 - Add a package to manage your fromm token storing
 - Add some option on yt-dld to improve the efficiency of the download

Fromm (if you read this, your app is shitty by the way) reencode the video, so this way to downlaod them is not the best. The best quality is only available during live streaming. If you want to backup the live replay you will need to explore fromm apk and the agora sdk ;)

It's still better to use this than screen-reccord the live (and because fromm reencode the video and chose to use a low bitrate, the video size is way smaller than a screenreccord)


___

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
