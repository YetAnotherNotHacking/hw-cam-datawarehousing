# Kentucky
# Coincidence? I think not.

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
from concurrent.futures import ThreadPoolExecutor

# Debugging variables
stableTime = False
debugParse = False

# State specific scraper settings
stateName = "Kentucky"
baseCCTVFrameLocation = "http://www.trimarc.org/images/snapshots/"
serviceURL = "https://goky.ky.gov/"
APIURL = "https://services2.arcgis.com/CcI36Pduqd0OR4W9/ArcGIS/rest/services/trafficCamerasCur_Prd/FeatureServer/0/query?where=1=1&outFields=name,description,snapshot,status,latitude,longitude,county&returnGeometry=false&f=pjson"
imageFolderName = "img"
snapshotImageFolderName = "snaps"
apidataname = "apidata.json"

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

def makeDirectories(scrapeFolderLocation=scrapeFolderLocation, imageFolderLocation=imageFolderLocation):
    if not os.path.isdir(scrapeFolderLocation):
        print(f"No folder exists for thwis scrape, so creating it at {scrapeFolderLocation}")
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
    print(f"Downloading {APIURL} to {apiSaveLocation}")
    # no special processing, its not json
    urllib.request.urlretrieve(APIURL, apiSaveLocation)

def getSnapshotUrls(apiSaveLocation):
    with open(apiSaveLocation, 'r') as f:
        data = json.load(f)
    return [f["attributes"]["snapshot"] for f in data["features"] if f["attributes"].get("snapshot")]
    

def downloadSingleImage(jpgurl, folder):
    print(f"Downloading {jpgurl} to {folder}")
    savename = os.path.basename(urlparse(jpgurl).path)
    urllib.request.urlretrieve(jpgurl, f"{folder}/{savename}")

def downloadJPGImages(jpgurllist, max_workers=16):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for jpgurl in jpgurllist:
            executor.submit(downloadSingleImage, jpgurl, snapshotImageFolderLocation)

def doScrape():
    makeDirectories()
    downloadApiDataToFile(APIURL, apiSaveLocation)
    jpgurls = getSnapshotUrls(apiSaveLocation)
    downloadJPGImages(jpgurls)

if __name__ == "__main__":
    doScrape()


