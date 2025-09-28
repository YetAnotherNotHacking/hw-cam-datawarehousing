# Illinois
# idk about this to even write anything

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
stateName = "Illinois"
baseCCTVFrameLocation = "https://cctv.travelmidwest.com/snapshots/"
serviceURL = "https://www.arcgis.com/apps/dashboards/1548e02d489742f5aacc2d51a800cebe"
APIURL = "https://services2.arcgis.com/aIrBD8yn1TDTEXoz/arcgis/rest/services/TrafficCamerasTM_Public/FeatureServer/0/query?f=pbf&cacheHint=true&maxRecordCountFactor=4&resultOffset=0&resultRecordCount=4000&where=1%3D1&orderByFields=OBJECTID%20ASC&outFields=*&outSR=102100&returnGeometry=false&spatialRel=esriSpatialRelIntersects"
imageFolderName = "img"
snapshotImageFolderName = "snaps"
apidataname = "apidata.pbf"

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

def regexExtractCameraSnapshots(apiSaveLocation):
    with open(apiSaveLocation, "rb") as f:
        data = f.read().decode(errors="ignore")
    results = re.findall(r"https?://[^\s]+\.jpg", data)
    print(f"PFB regex search found {len(results)} urls.")
    return results

def downloadSingleImage(jpgurl, folder):
    print(f"Downloading {jpgurl} to {folder}")
    savename = os.path.basename(urlparse(jpgurl).path)
    urllib.request.urlretrieve(jpgurl, f"{folder}/{savename}")

def downloadJPGImages(jpgurllist, max_workers=16):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for jpgurl in jpgurllist:
            executor.submit(downloadSingleImage, jpgurl, apiSaveLocation)

def doScrape():
    makeDirectories()
    downloadApiDataToFile(APIURL, apiSaveLocation)
    jpgurls = regexExtractCameraSnapshots(apiSaveLocation)
    downloadJPGImages(jpgurls)

if __name__ == "__main__":
    doScrape()

