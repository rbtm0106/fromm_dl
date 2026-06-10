#generate via gemini
import argparse
import shutil
import subprocess

import requests
import urllib.parse
import re
import uuid
import binascii
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


# ==========================================
# Authentication & Encryption Logic
# ==========================================
def encrypt_password_for_signin(password, device_id):
    try:
        key_source = device_id.encode('utf-8')
        key = key_source[:32]
        iv = key[:16]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        password_bytes = password.encode('utf-8')
        padded_password = pad(password_bytes, AES.block_size, style='pkcs7')
        encrypted_data = cipher.encrypt(padded_password)
        encrypted_hex = binascii.hexlify(encrypted_data).decode('utf-8')
        return encrypted_hex
    except Exception as e:
        return f"An error occurred during encryption of the password: {e}"


def signin(email: str, password: str, device_id: str, base_url: str):
    """Signs into the account and returns the API response and access token."""
    headers = {
        'Accept-Encoding': 'gzip',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'okhttp/5.1.0',
        'uuid': device_id
    }

    payload = {
        "username": email,
        "password": encrypt_password_for_signin(password, device_id),
        "deviceId": device_id,
        "from": "app",
        "allowUpdateDeviceId": True
    }

    print(f"[*] Authenticating with {base_url} ...")

    try:
        response = requests.post(f"{base_url}/auth/signin", headers=headers, json=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"[!] HTTP Error: {err}")
        print(f"[!] Server Response: {response.text}")
        return None, None

    response_data = response.json()
    access_token = None
    if response_data.get("success"):
        access_token = response_data.get("data", {}).get("accessToken")

    return response_data, access_token


# ==========================================
# Fetching & Command Generation Logic
# ==========================================
def get_fromm_playlist(short_url, bearer_token, output_path=""):
    print(f"\n[*] Fetching short link: {short_url} ...")

    response_redirect = requests.get(short_url, allow_redirects=False)

    if response_redirect.status_code not in [301, 302]:
        print(f"[!] Error: Expected a redirect, but got status code {response_redirect.status_code}")
        return

    location = response_redirect.headers.get('Location')
    decoded_location = urllib.parse.unquote(urllib.parse.unquote(location))
    match = re.search(r'channels/([^/]+)/media/(\d+)', decoded_location)

    if not match:
        print("[!] Error: Could not find the media ID in the redirect URL.")
        return

    channel_slug = match.group(1)
    media_id = match.group(2)
    print(f"[*] Extracted Channel Name: {channel_slug} | Media ID: {media_id}")

    # --- Dynamic Channel ID Lookup ---
    print(f"[*] Fetching channel ID for '{channel_slug}'...")
    channel_url = f"https://channel-api.frommyarti.com/channels/{channel_slug}"
    channel_headers = {
        "Host": "channel-api.frommyarti.com",
        "uuid": str(uuid.uuid4())
    }

    try:
        response_channel = requests.get(channel_url, headers=channel_headers)
        response_channel.raise_for_status()
        channel_json = response_channel.json()

        if not channel_json.get("success"):
            print(f"[!] Error: Channel metadata request failed. {channel_json}")
            return

        channel_id = channel_json["data"]["channel"]["id"]
        print(f"[*] Successfully resolved Channel ID: {channel_id}")

    except Exception as e:
        print(f"[!] Failed to resolve channel details: {e}")
        return
    # ---------------------------------

    api_url = f"https://channel-api.frommyarti.com/media/posts/{media_id}"
    print(f"[*] Fetching API: {api_url} ...")

    api_headers = {
        "Accept": "*/*",
        "Authorization": f"Bearer {bearer_token}",
        "channel-id": channel_id,
        "country": "KO",
        "language": "ko",
        "Origin": "https://channel.frommyarti.com",
        "Referer": "https://channel.frommyarti.com/",
        "timezone": "Asia/Seoul",
        "User-Agent": "Mozilla/5.0 (Linux; Android 16; SM-S938B Build/BP4A.251205.006; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/148.0.7778.225 Mobile Safari/537.36",
        "uuid": str(uuid.uuid4())
    }

    response_api = requests.get(api_url, headers=api_headers)

    if response_api.status_code != 200:
        print(f"[!] API Error: Failed to fetch data. Status code {response_api.status_code}")
        print(response_api.text)
        return

    json_data = response_api.json()

    if json_data.get("success"):
        playlist_url = json_data["data"]["post"]["url"]
        playlist_url = re.sub(r'_\d+x\d+', '', playlist_url) if "watermark_thumbnail" in playlist_url else playlist_url
        post_title = json_data["data"]["post"].get("title", "Unknown Title")

        parsed_url = urllib.parse.urlparse(playlist_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        cf_key_pair = query_params.get("CloudFront-Key-Pair-Id", [""])[0]
        cf_signature = query_params.get("CloudFront-Signature", [""])[0]
        cf_policy = query_params.get("CloudFront-Policy", [""])[0]

        cookie_string = f"CloudFront-Key-Pair-Id={cf_key_pair}; CloudFront-Signature={cf_signature}; CloudFront-Policy={cf_policy}"

        yt_dlp_cmd = ["yt-dlp"]

        if output_path:
            yt_dlp_cmd.extend(["-o", output_path])

        yt_dlp_cmd.extend([
            "--add-header", "Origin: https://channel.frommyarti.com",
            "--add-header", "Referer: https://channel.frommyarti.com/",
            "--add-header",
            "User-Agent: Mozilla/5.0 (Linux; Android 16; SM-S938B Build/BP4A.251205.006; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/148.0.7778.225 Mobile Safari/537.36",
            "--add-header", "X-Requested-With: com.knowmerce.fromm.fan",
            "--add-header", f"Cookie: {cookie_string}",
            playlist_url
        ])

        print("\n" + "=" * 70)
        print(f"TITLE: {post_title}")
        print("=" * 70)

        if shutil.which("yt-dlp"):
            print("\n[*] yt-dlp detected! Starting automatic download...\n")
            try:
                # This runs the download and pipes the live output straight to your terminal
                subprocess.run(yt_dlp_cmd, check=True)
                print("\n✅ Download completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n[!] yt-dlp encountered an error during download: {e}")
        else:
            print("\n[!] yt-dlp is not installed or not in system PATH.")
            print(">>> MANUAL COMMAND is:\n")
            print(" ".join(yt_dlp_cmd))
            print("\n" + "=" * 70)

    else:
        print("[!] Error: The API returned success: false.")


# ==========================================
# CLI Interface
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Fromm to yt-dlp Command Generator")

    # Target URL is optional so we can use the --generate-token flag alone
    parser.add_argument("url", nargs="?", help="The Fromm shortlink (e.g., https://fromm.my/1ps1e0)")

    # yt-dlp output option
    parser.add_argument("-o", "--output", help="Output path and filename for yt-dlp (e.g., C:/videos/fromis.mp4)",
                        default="")

    # Auth options
    auth_group = parser.add_argument_group("Authentication")
    auth_group.add_argument("-t", "--token", help="Provide an existing Bearer Token")
    auth_group.add_argument("-e", "--email", help="Email for login (requires -p)")
    auth_group.add_argument("-p", "--password", help="Password for login (requires -e)")

    # Utility option
    parser.add_argument("--generate-token", action="store_true",
                        help="Only authenticate and print the Bearer Token, then exit")

    args = parser.parse_args()
    AUTH_BASE_URL_LOGIN = "https://account-api.frommyarti.com"
    # ---------------------------------------------------------
    # MODE A: Just generate and print the token
    # ---------------------------------------------------------
    if args.generate_token:
        if not args.email or not args.password:
            print("[!] Error: You must provide --email and --password to generate a token.")
            sys.exit(1)

        device_id = str(uuid.uuid4())
        _, token = signin(args.email, args.password, device_id, AUTH_BASE_URL_LOGIN)
        if token:
            print("\n✅ Token Generated Successfully! Copy the string below:\n")
            print(token)
            print("\n(You can now use this with the -t flag!)")
        else:
            print("\n❌ Failed to generate token.")
        sys.exit(0)

    # ---------------------------------------------------------
    # Check if we have a URL to process
    # ---------------------------------------------------------
    if not args.url:
        print("[!] Error: You must provide a TARGET_URL unless using --generate-token.")
        parser.print_help()
        sys.exit(1)

    # ---------------------------------------------------------
    # MODE B: Get URL using an existing Token
    # ---------------------------------------------------------
    if args.token:
        print("[*] Using provided Bearer Token.")
        get_fromm_playlist(args.url, args.token, args.output)

    # ---------------------------------------------------------
    # MODE C: Get URL by logging in with Email/Password
    # ---------------------------------------------------------
    elif args.email and args.password:
        print("[*] Using Email/Password to authenticate...")
        device_id = str(uuid.uuid4())
        _, token = signin(args.email, args.password, device_id, AUTH_BASE_URL_LOGIN)

        if token:
            print("[*] Successfully retrieved Bearer Token.")
            get_fromm_playlist(args.url, token, args.output)
        else:
            print("[!] Authentication failed. Cannot generate command.")
            sys.exit(1)

    else:
        print("[!] Error: You must provide either a Token (-t) OR Email (-e) and Password (-p).")
        sys.exit(1)


if __name__ == "__main__":
    main()
