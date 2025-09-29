# Michigan
# Mish again?

#imports
import time
import urllib.request
from urllib.parse import urlparse
import os
import re
import json
import csv
import math
import re
import gzip
import requests
import io
import ffmpeg
from concurrent.futures import ThreadPoolExecutor

# Debugging variables
stableTime = False
debugParse = False

# State specific scraper settings
stateName = "Michigan" 
baseCCTVFrameLocation = "https://mdotjboss.state.mi.us/docs/drive/camfiles/rwis/"
serviceURL = "https://mdotjboss.state.mi.us/MiDrive/cameras"
APIURL = "https://mdotjboss.state.mi.us/MiDrive//camera/list?_=1759129156812"
imageFolderName = "img"
snapshotImageFolderName = "snaps"
apidataname = "apidata.json"
streamsFolderName = "streams"

# make this dynamic in the future
temp_folder = "data/"

# Gen the variables that are dynamic
if stableTime == True:
    timeSinceEpoch = 1
elif stableTime == False:
    timeSinceEpoch = round(time.time())

# Generate the save paths
scrapeFolderLocation = f"{temp_folder}/{stateName}/{timeSinceEpoch}"
scrapeFileLocation = f"{temp_folder}/{stateName}/{timeSinceEpoch}/{apidataname}"
apiSaveLocation = f"{scrapeFolderLocation}/{apidataname}"
imageFolderLocation = f"{scrapeFolderLocation}/{imageFolderName}"
snapshotImageFolderLocation = f"{imageFolderLocation}/{snapshotImageFolderName}"
streamsFolderLocation = f"{imageFolderLocation}/{streamsFolderName}"

def makeDirectories(scrapeFolderLocation=scrapeFolderLocation, imageFolderLocation=imageFolderLocation):
    if not os.path.isdir(scrapeFolderLocation):
        print(f"No folder exists for thwis scrape, so creating it at {scrapeFolderLocation}")
        # os.makedirs(path, exist_ok=True)
        os.makedirs(scrapeFolderLocation, exist_ok=True)
        os.makedirs(imageFolderLocation, exist_ok=True)
        os.makedirs(snapshotImageFolderLocation, exist_ok=True)
        os.makedirs(streamsFolderLocation, exist_ok=True)
    elif os.path.isdir(scrapeFolderLocation):
        if not os.path.isdir(imageFolderLocation):
            os.makedirs(imageFolderLocation, exist_ok=True)
        if not os.path.isdir(snapshotImageFolderLocation):
            os.makedirs(snapshotImageFolderLocation, exist_ok=True)
        if not os.path.isdir(streamsFolderLocation):
            os.makedirs(streamsFolderLocation, exist_ok=True)

def downloadApiDataToFile(APIURL, apiSaveLocation):
    print(f"Downloading {APIURL} to {apiSaveLocation}")
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Referer": "https://mdotjboss.state.mi.us",
    }
    req = urllib.request.Request(APIURL, headers=headers)
    with urllib.request.urlopen(req) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
    with open(apiSaveLocation, "wb") as f:
        f.write(data)
    return apiSaveLocation

def safe_strip(val):
    return val.strip() if isinstance(val, str) else ""

def json_to_clean_csv(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    csv_path = os.path.splitext(json_path)[0] + ".csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["route", "county", "location", "direction", "image_url"])
        for item in data:
            county = re.sub(r"<.*?>", "", safe_strip(item.get("county")))
            image_match = re.search(r'src="([^"]+)"', item.get("image") or "")
            image_url = image_match.group(1) if image_match else ""
            writer.writerow([
                safe_strip(item.get("route")),
                county,
                safe_strip(item.get("location")),
                safe_strip(item.get("direction")),
                image_url
            ])
    return csv_path

def csvGetColumnByName(file_path, column_name):
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row[column_name] for row in reader if column_name in row]

def downloadSingleImage(jpgurl, folder):
    print(f"Downloading {jpgurl} to {folder}")
    savename = os.path.basename(urlparse(jpgurl).path)
    urllib.request.urlretrieve(jpgurl, f"{folder}/{savename}")

def downloadJPGImages(jpgurllist, max_workers=16):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for jpgurl in jpgurllist:
            executor.submit(downloadSingleImage, jpgurl, snapshotImageFolderLocation)

def doScrape():
    # real_url = resolve_md_stream("00012848007300bc004c823633235daa")
    # print(real_url)
    makeDirectories()
    apifile = downloadApiDataToFile(APIURL, apiSaveLocation)
    csvloc = json_to_clean_csv(apifile)
    imageurls = csvGetColumnByName(csvloc, "image_url")
    downloadJPGImages(imageurls)


if __name__ == "__main__":
    doScrape()


