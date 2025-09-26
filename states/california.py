# California
# daly city my beloved (neighborhood)
# anyways

#imports
import time
import urllib.request
import os
import re
import json
import csv
import math
from concurrent.futures import ThreadPoolExecutor

# Debugging variables
stableTime = False
debugParse = False

# State specific scraper settings
stateName = "California"
baseCCTVFrameLocation = "https://www.az511.gov/map/Cctv/"
serviceURL = "https://www.az511.gov/cctv?start=0&length=100&order%5Bi%5D=1&order%5Bdir%5D=asc"
APIURL = "https://www.az511.gov//List/GetData/Cameras?query={\"columns\":[{\"data\":null,\"name\":\"\"},{\"name\":\"sortOrder\",\"s\":true},{\"name\":\"roadway\",\"s\":true},{\"data\":3,\"name\":\"\"}],\"order\":[{\"column\":1,\"dir\":\"asc\"},{\"column\":2,\"dir\":\"asc\"}],\"start\":0,\"length\":100,\"search\":{\"value\":\"\"}}&lang=en-US"
apiTempFolder = "apidata/"
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
tempAPIFolderLocation = f"{scrapeFolderLocation}/{apiTempFolder}"
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
        os.makedirs(tempAPIFolderLocation, exist_ok=True)
        os.makedirs(imageFolderLocation, exist_ok=True)
        os.makedirs(streamsFolderLocation, exist_ok=True)
        os.makedirs(snapshotImageFolderLocation, exist_ok=True)
    elif os.path.isdir(scrapeFolderLocation): 
        if not os.path.isdir(tempAPIFolderLocation):
            os.makedirs(tempAPIFolderLocation, exist_ok=True)
        if not os.path.isdir(imageFolderLocation):
            os.makedirs(imageFolderLocation, exist_ok=True)
        if not os.path.isdir(streamsFolderLocation):
            os.makedirs(streamsFolderLocation, exist_ok=True)
        if not os.path.isdir(snapshotImageFolderLocation):
            os.makedirs(snapshotImageFolderLocation, exist_ok=True)

def downloadAPIChunks(type):
    jsonLocations = []
    csvLocations = []
    num_d = 12
    def download_chunk(d):
        fileCurrentD = f"{d:02}"
        url = f"https://cwwp2.dot.ca.gov/data/d{d}/cctv/cctvStatusD{fileCurrentD}.{type}"
        current_scrape_file_name = f"{tempAPIFolderLocation}/{d}.{type}"
        urllib.request.urlretrieve(url, current_scrape_file_name)
        if type == "json":
            jsonLocations.append(current_scrape_file_name)
        else:
            csvLocations.append(current_scrape_file_name)

    with ThreadPoolExecutor(max_workers=12) as executor:
        for d in range(1, num_d + 1):
            executor.submit(download_chunk, d)
    return jsonLocations, csvLocations

def csvGetColumnByName(file_paths, column_names):
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    if isinstance(column_names, str):
        column_names = [column_names]
    results = {col: [] for col in column_names}
    for file_path in file_paths:
        print(f"Reading {file_path}")
        with open(file_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for col in column_names:
                    if col in row:
                        results[col].append(row[col])
    return results

def genListSnapURLs(csvList):
    snapLinkList = []
    for csvfileloc in csvList:
        urls = csvGetColumnByName(csvfileloc, "currentImageURL")
        snapLinkList.extend(urls["currentImageURL"])
    return snapLinkList

def downloadImageData(snapLinks, folder):
    if isinstance(snapLinks, str):
        snapLinks = [snapLinks]
    os.makedirs(folder, exist_ok=True)
    def downloadThread(url, dest):
        urllib.request.urlretrieve(url, dest)
        print(f"Downloading {url} to {dest}")
    with ThreadPoolExecutor(max_workers=16) as ex:
        for i, url in enumerate(snapLinks, 1):
            ex.submit(downloadThread, url, f"{folder}/{i}.jpg")
            

def doScrape():
    makeDirectories()
    _, csvlocs = downloadAPIChunks("csv")
    snapLinks = genListSnapURLs(csvlocs)
    downloadImageData(snapLinks, snapshotImageFolderLocation)

if __name__ == "__main__":
    doScrape()