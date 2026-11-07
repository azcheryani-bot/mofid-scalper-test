#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
لانچر ابری و ۱۰۰٪ امن شکارچی صف فروش برای GitHub Actions (scalper_launcher.py)

ویژگی‌ها:
۱) فاقد هرگونه اطلاعات محرمانه، پسورد یا توکن در داخل کد (۱۰۰٪ امن برای قراردادن در گیت‌هاب)
۲) خواندن توکن‌های محیطی (GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN, GDRIVE_FOLDER_ID) از متغیرهای محیطی
   مستقیماً از GitHub Actions Secrets
۳) گوگل درایو github_scalper از پوشه «sell_queue_scalper_sim.py» دانلود خودکار آخرین ویرایش فایل
   بدون نیاز به کامیت مجدد در گیت‌هاب برای تغییرات بعدی (RAM) و اجرا مستقیم آن در حافظه رم
"""

import json
import os
import sys
import urllib.parse
import urllib.request

TARGET_SCRIPT_NAME = "sell_queue_scalper_sim.py"

def get_gdrive_access_token():
    client_id = os.environ.get("GDRIVE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GDRIVE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("GDRIVE_REFRESH_TOKEN", "").strip()
    folder_id = os.environ.get("GDRIVE_FOLDER_ID", "").strip()

    if not (client_id and client_secret and refresh_token and folder_id):
        print(
            "[!] در محیط اجرا تنظیم نشده‌اند (GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN, GDRIVE_FOLDER_ID) خطا: متغیرهای محیطی گوگل درایو"
        )
        return None, folder_id

    data = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[!] خطا در دریافت access_token از گوگل: {e}")
        return None, folder_id
    token = payload.get("access_token")
    if not token:
        print(f"[!] پاسخ گوگل فاقد access_token است: {payload}")
        return None, folder_id
    return token, folder_id

def download_target_from_drive(access_token, folder_id):
    query = urllib.parse.quote(
        f"name = '{TARGET_SCRIPT_NAME}' and '{folder_id}' in parents and trashed = false"
    )
    url = (
        "https://www.googleapis.com/drive/v3/files"
        f"?q={query}&fields=files(id,name,modifiedTime)&orderBy=modifiedTime desc&pageSize=1"
    )
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[!] خطا در جستجوی فایل در گوگل درایو: {e}")
        return None
    files = payload.get("files", [])
    if not files:
        print(f"[!] فایل {TARGET_SCRIPT_NAME} در پوشه گوگل درایو یافت نشد.")
        return None
    file_id = files[0]["id"]
    print(f"[+] فایل هدف یافت شد: {files[0].get('name')} (modifiedTime={files[0].get('modifiedTime')})")
    media_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    req = urllib.request.Request(media_url, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"[!] خطا در دانلود فایل از گوگل درایو: {e}")
        return None

def main():
    print("[*] شروع لانچر ابری شکارچی صف فروش ...")
    access_token, folder_id = get_gdrive_access_token()
    if not access_token:
        print("[!] توقف به دلیل عدم دسترسی به گوگل درایو.")
        sys.exit(1)
    code = download_target_from_drive(access_token, folder_id)
    if code is None:
        print("[!] توقف به دلیل عدم دریافت اسکریپت اصلی.")
        sys.exit(1)
    print(f"[+] اسکریپت اصلی دریافت شد ({len(code)} کاراکتر). اجرای آن در حافظه ...")
    try:
        compiled = compile(code, TARGET_SCRIPT_NAME, "exec")
    except Exception as e:
        print(f"[!] خطا در کامپایل اسکریپت دانلودشده: {e}")
        sys.exit(1)
    globals_dict = {"__name__": "__main__", "__file__": TARGET_SCRIPT_NAME}
    try:
        exec(compiled, globals_dict)
    except SystemExit as e:
        print(f"[*] اسکریپت اصلی با کد خروج {e.code} پایان یافت.")
        sys.exit(e.code if isinstance(e.code, int) else 0)
    except Exception as e:
        print(f"[!] خطا در اجرای اسکریپت اصلی: {e}")
        sys.exit(1)
    print("[*] اجرای اسکریپت اصلی با موفقیت پایان یافت.")

if __name__ == "__main__":
    main()
