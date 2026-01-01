# Missouri
# what the hell even happens in this state idfk anything about it :sob:

# imports
import time
import subprocess
import urllib.request
import os
import json
import csv
import math
from pathlib import Path
from hashlib import sha1

from concurrent.futures import ThreadPoolExecutor

# debug variables
stableTime = True

# standard variables
stateName = "Missouri"
serviceURL = "https://traveler.modot.org/map/index.html" 
APIURL = "https://traveler.modot.org/timconfig/feed/desktop/StreamingCams2.json"
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
    
def downloadApiDataToFile(APIURL, apiSaveLocation):
    print(f"Downloading \"{APIURL}\" to {apiSaveLocation}")
    urllib.request.urlretrieve(APIURL, apiSaveLocation)

def parseDownloadedFiles(input_path):
    print(f"Converting {input_path} to csv format")
    output_path = os.path.splitext(input_path)[0] + ".csv"
    print(f"Writing csv data to {output_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "location", "latitude", "longitude", "stream_url"]
        )
        writer.writeheader()
        for entry in data:
            writer.writerow({
                "name": entry.get("location"),
                "location": entry.get("location"),
                "latitude": entry.get("y"),
                "longitude": entry.get("x"),
                "stream_url": entry.get("html") or entry.get("rtmp")
            })
    return output_path

def csvGetColumnByName(file_path, column_name):
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row[column_name] for row in reader if column_name in row]

def fetch_m3u8_media(m3u8_list, video_out_dir, thumb_out_dir):
    threads = 8

    Path(video_out_dir).mkdir(parents=True, exist_ok=True)
    Path(thumb_out_dir).mkdir(parents=True, exist_ok=True)

    def handle(url):
        uid = sha1(url.encode()).hexdigest()[:16]
        video_path = os.path.join(video_out_dir, f"{uid}.mp4")
        thumb_path = os.path.join(thumb_out_dir, f"{uid}.jpg")
        print(f"Thread spawn, executing download task with UID {uid}")

        subprocess.run([
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", url,
            "-t", "10",
            "-c", "copy",
            video_path
        ], check=False)

        subprocess.run([
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", video_path,
            "-vf", "select=eq(n\\,0)",
            "-frames:v", "1",
            thumb_path
        ], check=False)

    with ThreadPoolExecutor(max_workers=threads) as pool:
        pool.map(handle, m3u8_list)

def doScrape():
    makeDirectories()
    downloadApiDataToFile(APIURL, scrapeFileLocation)
    csv_path = parseDownloadedFiles(scrapeFileLocation)
    camLinks = csvGetColumnByName(csv_path, "stream_url") 
    fetch_m3u8_media(camLinks, streamsFolderLocation, snapshotImageFolderLocation)

if __name__ == "__main__":
    doScrape()