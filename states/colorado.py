# Scraper for Colorado
# square ahh state

# Debugging variables
stableTime = False
debugParse = False

# imports
import time
import urllib.request
import requests
import os
import json
import csv
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor

# State specific scraper settings
stateName = "Colorado"
serviceURL = "https://www.cotrip.org" 
APIURL = "https://www.cotrip.org/api/graphql"
imageFolderName = "img"
snapshotImageFolderName = "snaps"
streamsFolderName = "streams"

apidataname = "apidata.json"

# this needs to be dynamic in th efuture, most likely it would be to a webroot of some sort.
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

def makeDirectories(scrapeFolderLocation=scrapeFolderLocation, imageFolderLocation=imageFolderLocation, streamsFolderLocation=streamsFolderLocation, snapshotImageFolderLocation=snapshotImageFolderLocation):
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
    
def downloadAPIDataToFile(path):
    url = APIURL
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json",
        "Referer": "https://www.cotrip.org/list/cameras",
        "language": "en",
        "Origin": "https://www.cotrip.org",
        "Connection": "keep-alive",
        "DNT": "1",
        "Sec-GPC": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    data = {
        "query": "query ($input: ListArgs!) { listCameraViewsQuery(input: $input) { cameraViews { category icon lastUpdated { timestamp timezone } title uri url sources { type src } parentCollection { title uri icon color location { routeDesignator } lastUpdated { timestamp timezone } } } totalRecords error { message type } } }",
        "variables": {
            "input": {
                "west": -180,
                "south": -85,
                "east": 180,
                "north": 85,
                "sortDirection": "DESC",
                "sortType": "ROADWAY",
                "freeSearchTerm": "",
                "classificationsOrSlugs": [],
                "recordLimit": 4000,
                "recordOffset": 0
            }
        }
    }
    r = requests.post(url, headers=headers, json=data)
    with open(path, "wb") as f: 
        f.write(r.content)

def camerasJSONToCSV(file_path):
    with open(file_path) as f:
        data = json.load(f)
    cams = data["data"]["listCameraViewsQuery"]["cameraViews"]
    out_path = os.path.splitext(file_path)[0] + ".csv"
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name","location","snapshot_url","stream_url"])
        for c in cams:
            sources = c.get("sources") or []
            if not isinstance(sources, list) or not sources:
                continue
            stream = sources[0].get("src","")
            if not stream:
                continue
            name = c.get("title","")
            loc = c.get("parentCollection",{}).get("location",{}).get("routeDesignator","")
            snapshot = c.get("url","")
            w.writerow([name,loc,snapshot,stream])
    return out_path

def csvGetColumnByName(file_path, column_name):
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        data = [row[column_name] for row in reader if column_name in row]
        print(f"Queried {file_path} for {column_name} and found {len(data)} record(s)")
        return data

download_jobs = []

def addVideoToDownloadQueue(url, output_location, seconds):
    download_jobs.append((url, output_location, seconds))

def dorecording():
    print("Starting to download videos from the server...")
    def record(job):
        print(f"Recording: {job}")
        url, out, secs = job
        subprocess.run([
            "ffmpeg", "-y", "-i", url, "-t", str(secs), "-c", "copy", out
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #])
    with ThreadPoolExecutor(max_workers=16) as ex:
        futures = [ex.submit(record, job) for job in download_jobs]
        for f in futures:
            f.result()
    download_jobs.clear()

def addVideosToDownloadQueue(csvpath):
    videoUrls = csvGetColumnByName(csvpath, "stream_url")
    viddy = 1
    for videoUrl in videoUrls:
        filename = f"{viddy}-{videoUrl.rsplit('/', 1)[-1]}"
        addVideoToDownloadQueue(videoUrl, f"{streamsFolderLocation}/{filename}", 20)
        viddy += 1

def downloadImages(imageList):
    badpasses = 0
    for imageurl in imageList:
        if imageurl == "/images/icon-camera-closed-fill-solid-padded.svg":
            badpasses += 1
            print(f"Image was bad, skipping it. This makes {badpasses} bad passes so far.")
            pass
        else:
            filename = imageurl.rsplit('/', 1)[-1]
            print(f"Downloading image {filename} from {imageurl}")
            urllib.request.urlretrieve(imageurl, f"{snapshotImageFolderLocation}/{filename}")

def doScrape():
    makeDirectories()
    downloadAPIDataToFile(scrapeFileLocation)
    csvpath = camerasJSONToCSV(scrapeFileLocation)
    addVideosToDownloadQueue(csvpath)
    time.sleep(0.1) # waut for populate
    dorecording()
    images = csvGetColumnByName(csvpath, "snapshot_url")
    downloadImages(images)

if __name__ == "__main__":
    doScrape()