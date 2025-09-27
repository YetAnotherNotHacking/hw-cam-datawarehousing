import time
import urllib.request
import os
import re
import json
import csv
import math
import requests
import ffmpeg
from concurrent.futures import ThreadPoolExecutor

# Debugging variables
stableTime = False
debugParse = False

# make this dynamic in the future
temp_folder = "data/"

if stableTime == True:
    timeSinceEpoch = 1
elif stableTime == False:
    timeSinceEpoch = round(time.time())

# State specific scraper settings
stateName = "Delaware"
serviceURL = "https://deldot.gov/map/index.shtml?tab=TrafficCameras"
APIURL = "https://tmc.deldot.gov/json/videocamera.json?id=4yte&_=1758942502716"
imageFolderName = "img"
streamsFolderName = "streams"
snapshotImageFolderName = "snaps"
apidataname = "apidata.json"

scrapeFolderLocation = f"{temp_folder}/{stateName}/{timeSinceEpoch}"
scrapeFileLocation = f"{temp_folder}/{stateName}/{timeSinceEpoch}/{apidataname}"
apiSaveLocation = f"{scrapeFolderLocation}/{apidataname}"
imageFolderLocation = f"{scrapeFolderLocation}/{imageFolderName}"
streamsFolderLocation = f"{imageFolderLocation}/{streamsFolderName}"
snapshotImageFolderLocation = f"{imageFolderLocation}/{snapshotImageFolderName}"


def makeDirectories(scrapeFolderLocation=scrapeFolderLocation, imageFolderLocation=imageFolderLocation):
    if not os.path.isdir(scrapeFolderLocation):
        print(f"No folder exists for this scrape, so creating it at {scrapeFolderLocation}")
        # os.makedirs(path, exist_ok=True)
        os.makedirs(scrapeFolderLocation, exist_ok=True)
        os.makedirs(imageFolderLocation, exist_ok=True)
        os.makedirs(streamsFolderLocation, exist_ok=True)
        os.makedirs(snapshotImageFolderLocation, exist_ok=True)
    elif os.path.isdir(scrapeFolderLocation):
        if not os.path.isdir(imageFolderLocation):
            os.makedirs(imageFolderLocation, exist_ok=True)
        if not os.path.isdir(streamsFolderLocation):
            os.makedirs(streamsFolderLocation, exist_ok=True)
        if not os.path.isdir(snapshotImageFolderLocation):
            os.makedirs(snapshotImageFolderLocation, exist_ok=True)

def fetchAPIDataToJSON(APIURL, apiSaveLocation):
    data = requests.get(APIURL).json()
    with open(apiSaveLocation, "w") as f:
        json.dump(data, f)
    return apiSaveLocation

def json_to_csv(apiSaveLocation):
    out_path = scrapeFileLocation.replace('.json', '.csv')
    with open(apiSaveLocation) as f:
        data = json.load(f)
    video_cams = data.get("videoCameras", [])
    keys = [
        "id",
        "title",
        "county",
        "lat",
        "lon",
        "status",
        "m3u8"
    ]
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(keys)
        for cam in video_cams:
            row = [
                cam.get("id"),
                cam.get("title"),
                cam.get("county"),
                cam.get("lat"),
                cam.get("lon"),
                cam.get("status"),
                cam.get("urls", {}).get("m3u8")
            ]
            writer.writerow(row)
    return out_path

def getURLsFromCSV(csvpath):
    urls = []
    with open(csvpath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls.append(row["m3u8"])
    print(f"Read {len(urls)} from the CSV file.")
    time.sleep(0.2)
    return urls

def capture_frame(url):
    name = url.split('/')[-2].split('.stream')[0]
    output_file = f"{name}.png"
    try:
        (
            ffmpeg
            .input(url, ss=0)
            .output(output_file, vframes=1)
            .run(quiet=True, overwrite_output=True)
        )
    except:
        pass

def download_clip(url, duration=20):
    name = url.split('/')[-2].split('.stream')[0]
    output_file = f"{name}.mp4"
    try:
        (
            ffmpeg
            .input(url, t=duration)
            .output(output_file, c='copy')
            .run(quiet=True, overwrite_output=True)
        )
    except:
        pass

def process_stream(url, duration=20):
    name = url.split('/')[-2].split('.stream')[0]
    try:
        ffmpeg.input(url, ss=0).output(f"{snapshotImageFolderLocation}/{name}.png", vframes=1).run(quiet=False, overwrite_output=True)
        ffmpeg.input(url, t=duration).output(f"{streamsFolderLocation}/{name}.mp4", c='copy').run(quiet=False, overwrite_output=True)
    except Exception as e:
        print(f"FAIL: {e}")

def process_streams(url_list):
    with ThreadPoolExecutor(max_workers=16) as executor:
        executor.map(process_stream, url_list)

def doScrape():
    makeDirectories()
    fetchAPIDataToJSON(APIURL, apiSaveLocation)
    csvloc = json_to_csv(apiSaveLocation)
    m3u8urls = getURLsFromCSV(csvloc)
    process_streams(m3u8urls)


if __name__ == "__main__":
    doScrape()

