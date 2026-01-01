# Montana
# Mountaina?

# imports
import time
import subprocess
import requests
import urllib.request
import os
import json
import csv
import math
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path
from hashlib import sha1

from concurrent.futures import ThreadPoolExecutor

# debug variables
stableTime = True

# standard variables
stateName = "Montana"
serviceURL = "https://app.mdt.mt.gov/atms/public/cameras" 
APIURL = "https://app.mdt.mt.gov/atms/public/cameras"
imageFolderName = "img"
snapshotImageFolderName = "snaps"
streamsFolderName = "streams"
apidataname = "apidata.json"

# this needs to be dynamic in the future, most likely it would be to a webroot of some sort.
temp_folder = "data/"

# Gen the variables that are dynamic
if stableTime == True:
    timeSinceEpoch = 1
elif stableTime == False:
    timeSinceEpoch = round(time.time())

scrapeFolderLocation = f"{temp_folder}/{stateName}/{timeSinceEpoch}"
scrapeFileLocation = f"{temp_folder}/{stateName}/{timeSinceEpoch}/{apidataname}"
apiSaveLocation = f"{scrapeFolderLocation}/{apidataname}"
imageFolderLocation = f"{scrapeFolderLocation}/{imageFolderName}"
snapshotImageFolderLocation = f"{imageFolderLocation}/{snapshotImageFolderName}"
streamsFolderLocation = f"{imageFolderLocation}/{streamsFolderName}"


def makeDirectories():
    if not os.path.isdir(scrapeFolderLocation):
        print(f"No folder exists for this scrape, so creating it at {scrapeFolderLocation}")
        # os.makedirs(path, exist_ok=True)
        os.makedirs(scrapeFolderLocation, exist_ok=True)
        os.makedirs(imageFolderLocation, exist_ok=True)
        os.makedirs(snapshotImageFolderLocation, exist_ok=True)
    elif os.path.isdir(scrapeFolderLocation):
        if not os.path.isdir(imageFolderLocation):
            os.makedirs(imageFolderLocation, exist_ok=True)
        if not os.path.isdir(snapshotImageFolderLocation):
            os.makedirs(snapshotImageFolderLocation, exist_ok=True)
    
# We have to do a bit of html parsing to find the elements
def downloadAndExtractCameraData(url, json_path, csv_path):
    html = requests.get(url, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    cameras = []

    for card in soup.select("div.card.mdt-card"):
        title_block = card.select_one(".card-title")
        if not title_block:
            continue

        name_divs = title_block.select("div.col-md-10 > div")
        if len(name_divs) < 2:
            continue

        name = name_divs[0].get_text(strip=True)
        route = name_divs[1].get_text(strip=True)

        img = card.select_one("img.default-img-thumb")
        if not img:
            continue

        img_url = img.get("src")
        alt = img.get("alt", "")
        timestamp = None
        if "-" in alt:
            timestamp = alt.split("-")[-1].strip()

        cameras.append({
            "name": name,
            "route": route,
            "image_url": img_url,
            "timestamp": timestamp
        })

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(cameras, f, indent=2)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cameras[0].keys() if cameras else [])
        writer.writeheader()
        writer.writerows(cameras)

    return cameras

def csvGetColumnByName(file_path, column_name):
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row[column_name] for row in reader if column_name in row]

def threadedDownloadImages(jpeg_urls, output_dir):
    threads = 8
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    def handle(url):
        uid = sha1(url.encode()).hexdigest()[:16]
        out_path = os.path.join(output_dir, f"{uid}.jpg")
        print(f"Downloading data from URL {url} with UID {uid} and saving it to {out_path}")
        subprocess.run([
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", url,
            "-frames:v", "1",
            out_path
        ], check=False)

    with ThreadPoolExecutor(max_workers=threads) as pool:
        pool.map(handle, jpeg_urls)

def doScrape():
    makeDirectories()
    downloadAndExtractCameraData(APIURL, apiSaveLocation, apiSaveLocation.replace(".json", ".csv"))
    cameralinks = csvGetColumnByName(apiSaveLocation.replace(".json", ".csv"), "image_url")
    threadedDownloadImages(cameralinks, snapshotImageFolderLocation)

if __name__ == "__main__":
    doScrape()