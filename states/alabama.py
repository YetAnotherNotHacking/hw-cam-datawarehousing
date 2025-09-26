# Scraper for Alabama
# Sweet hooommeee Alabaaa....

# Debugging variables
stableTime = False
debugParse = False

# imports
import time
import urllib.request
import os
import json
import csv
import math
from concurrent.futures import ThreadPoolExecutor

# State specific scraper settings
stateName = "Alabama"
serviceURL = "https://algotraffic.com/Cameras" 
APIURL = "https://api.algotraffic.com/v4.0/Cameras"
imageFolderName = "img"
mapImageFolderName = "map"
snapshotImageFolderName = "snaps"
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
mapImageFolderLocation = f"{imageFolderLocation}/{mapImageFolderName}"
snapshotImageFolderLocation = f"{imageFolderLocation}/{snapshotImageFolderName}"

def makeDirectories(scrapeFolderLocation=scrapeFolderLocation, imageFolderLocation=imageFolderLocation, mapImageFolderLocation=mapImageFolderLocation, snapshotImageFolderLocation=snapshotImageFolderLocation):
    if not os.path.isdir(scrapeFolderLocation):
        print(f"No folder exists for this scrape, so creating it at {scrapeFolderLocation}")
        # os.makedirs(path, exist_ok=True)
        os.makedirs(scrapeFolderLocation, exist_ok=True)
        os.makedirs(imageFolderLocation, exist_ok=True)
        os.makedirs(mapImageFolderLocation, exist_ok=True)
        os.makedirs(snapshotImageFolderLocation, exist_ok=True)
    elif os.path.isdir(scrapeFolderLocation):
        if not os.path.isdir(imageFolderLocation):
            os.makedirs(imageFolderLocation, exist_ok=True)
        if not os.path.isdir(mapImageFolderLocation):
            os.makedirs(mapImageFolderLocation, exist_ok=True)
        if not os.path.isdir(snapshotImageFolderLocation):
            os.makedirs(snapshotImageFolderLocation, exist_ok=True)
    

def downloadApiDataToFile(APIURL, apiSaveLocation):
    print(f"Downloading \"{APIURL}\" to {apiSaveLocation}")
    urllib.request.urlretrieve(APIURL, apiSaveLocation)

def parseDownloadedFiles():
    with open(scrapeFileLocation, 'r') as file:
        rawJSON = file.read()
        print(f"Loaded {len(rawJSON)} entries {scrapeFileLocation}")
    parseMe = json.loads(rawJSON)
    csv_path = scrapeFileLocation.replace('.json', '.csv')
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Latitude", "Longitude", "hlsURL", "snapshotImageURL", "mapImageURL"])
        iteration = 1
        for camera in parseMe:
            if debugParse == True:
                print(f"Parsing line {iteration} out of {len(parseMe)}\nThis camera is located at {round(camera["location"]["latitude"], 5)}, {round(camera["location"]["longitude"], 5)}")
            lat = camera["location"]["latitude"]
            lon = camera["location"]["longitude"]
            hls = camera.get("playbackUrls", {}).get("hls", "")
            snapshot = camera.get("snapshotImageUrl", "")
            mapimg = camera.get("mapImageUrl", "")
            writer.writerow([lat, lon, hls, snapshot, mapimg])
            iteration += 1 
    return csv_path

def csvGetColumnByName(file_path, column_name):
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row[column_name] for row in reader if column_name in row]

def downloadImages(csvPath):
    print(f"Downloader loading links from path {csvPath}")
    mapLinks = csvGetColumnByName(csvPath, "mapImageURL")
    snapLinks = csvGetColumnByName(csvPath, "snapshotImageURL")
    print(f"Downloading {stateName}'s images, {len(mapLinks)} map images and {len(snapLinks)} snapshots.")

    def downloadThread(url, dest):
        print(f"Thread spawned and downloading {url} to {dest}")
        urllib.request.urlretrieve(url, dest)

    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, url in enumerate(mapLinks, 1):
            ex.submit(downloadThread, url, f"{mapImageFolderLocation}/{i}.jpg")
        for i, url in enumerate(snapLinks, 1):
            ex.submit(downloadThread, url, f"{snapshotImageFolderLocation}/{i}.jpg")

def doScrape():
    makeDirectories()
    downloadApiDataToFile(APIURL, apiSaveLocation)
    csvPath = parseDownloadedFiles()
    time.sleep(2) # Wait for the csv to exist
    downloadImages(csvPath)

if __name__ == "__main__":
    doScrape()