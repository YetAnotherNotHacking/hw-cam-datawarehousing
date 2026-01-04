# New Jersey
# old jersey got dirty or smn ig

from playwright.sync_api import sync_playwright
import json
import time
import urllib.request
import urllib.parse
import requests # for session
import os
import re

import csv
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from hashlib import sha1

# special imports for this strange encrypted token handling logic the site has
import base64
import ssl

stableTime = False
debugParse = False

stateName = "New Jersey"
baseCCTVFrameLocation = "https://www.nvroads.com/map/Cctv/"
serviceURL = "https://511nj.org/camera"
APIURL = "https://511nj.org/client/trafficMap/getCameraDataByTourId"
imageFolderName = "img"
snapshotImageFolderName = "snaps"
apidataname = "apidata.json"

temp_folder = "data/"

if stableTime == True:
    timeSinceEpoch = 1
else:
    timeSinceEpoch = round(time.time())

scrapeFolderLocation = f"{temp_folder}/{stateName}/{timeSinceEpoch}"
scrapeFileLocation = f"{temp_folder}/{stateName}/{timeSinceEpoch}/{apidataname}"
apiSaveLocation = f"{scrapeFolderLocation}/{apidataname}"
imageFolderLocation = f"{scrapeFolderLocation}/{imageFolderName}"
snapshotImageFolderLocation = f"{imageFolderLocation}/{snapshotImageFolderName}"

def downloadApiDataToFile(api_url, out_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://511nj.org/camera")

        with page.expect_response(lambda r: api_url in r.url, timeout=30000) as resp_info:
            pass

        resp = resp_info.value
        data = resp.json()

        cookies = context.cookies()
        ua = page.evaluate("() => navigator.userAgent")

        browser.close()

    with open(out_path, "w") as f:
        json.dump({
            "api": data,
            "cookies": cookies,
            "ua": ua
        }, f)

def makeDirectories(scrapeFolderLocation=scrapeFolderLocation, imageFolderLocation=imageFolderLocation):
    os.makedirs(scrapeFolderLocation, exist_ok=True)
    os.makedirs(imageFolderLocation, exist_ok=True)
    os.makedirs(snapshotImageFolderLocation, exist_ok=True)

def extractM3U8Entries(path):
    with open(path, "r") as f:
        raw = json.load(f)


    # authenticate using the fake session recreation from the browser used to download the camera data index
    api = raw["api"]
    cookies = raw["cookies"]
    ua = raw["ua"]

    cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    out = []
    for cam in api.get("data", []):
        for d in cam.get("cameraMainDetail", []):
            url = d.get("url")
            if url and url.endswith(".m3u8"):
                out.append({
                    "url": url,
                    "cookie": cookie_header,
                    "ua": ua
                })
    return out

def downloadSingleStream(entry):
    uid = sha1(entry["url"].encode()).hexdigest()[:16]
    videoPath = os.path.join(snapshotImageFolderLocation, f"{uid}.mp4")
    thumbPath = os.path.join(snapshotImageFolderLocation, f"{uid}.jpg")

    subprocess.run([
        "ffmpeg","-y","-loglevel","error",
        "-i",entry["url"],
        "-t","10","-c","copy",videoPath
    ], check=False)

    subprocess.run([
        "ffmpeg","-y","-loglevel","error",
        "-i",videoPath,
        "-vf","select=eq(n\\,0)",
        "-frames:v","1",thumbPath
    ], check=False)

def downloadImages(entries, max_workers=8):
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        ex.map(downloadSingleStream, entries)

def doScrape():
    makeDirectories(scrapeFolderLocation, imageFolderLocation)
    downloadApiDataToFile(APIURL, apiSaveLocation)
    entries = extractM3U8Entries(apiSaveLocation)
    downloadImages(entries)


if __name__ == "__main__":
    doScrape()