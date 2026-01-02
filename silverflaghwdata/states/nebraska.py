# Nebraska
# lol imagine being triple landlocked :skull:

# Type:
# 511alt-graphql

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
stateName = "Nebraska"
baseCCTVFrameLocation = "https://dot511.nebraska.gov/images/"
serviceURL = "https://new.511.nebraska.gov/list/cameras"
APIURL = "https://www.511.nebraska.gov/api/graphql"
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

def downloadApiDataToFile(api_url, out_path):
    combined = stepFetchGraphQL(api_url)
    with open(out_path, "w") as f:
        json.dump(combined, f)

# ONLY for graphql, no longer standard api with this new edition of the graphql endpoint.
def stepFetchGraphQL(api_url, step=100):
    query = """
    query ($input: ListArgs!) {
      listCameraViewsQuery(input: $input) {
        cameraViews {
          category
          icon
          lastUpdated { timestamp timezone }
          title
          uri
          url
          sources { type src }
          parentCollection {
            title
            uri
            icon
            color
            location { routeDesignator }
            lastUpdated { timestamp timezone }
          }
        }
        totalRecords
        error { message type }
      }
    }
    """
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "language": "en",
        "origin": "https://www.511.nebraska.gov",
        "referer": "https://www.511.nebraska.gov/"
    }
    all_rows = []
    offset = 0
    while True:
        payload = {
            "query": query,
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
                    "recordLimit": step,
                    "recordOffset": offset
                }
            }
        }
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as r:
            resp = json.load(r)
        block = resp["data"]["listCameraViewsQuery"]
        rows = block["cameraViews"]
        if not rows:
            break
        all_rows.extend(rows)
        offset += step
        if offset >= block["totalRecords"]:
            break
    return {"data": all_rows}


def downloadApiDataToFile(api_url, out_path):
    combined = stepFetchGraphQL(api_url)
    with open(out_path, "w") as f:
        json.dump(combined, f)

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

def convertToCSV(path):
    with open(path, 'r') as f:
        raw = json.load(f)
    rows = raw["data"]
    out_path = scrapeFileLocation.replace(".json", ".csv")
    headers = [
        "title",
        "category",
        "route",
        "collection",
        "image_url",
        "uri",
        "updated_ts",
        "updated_tz",
        "collection_updated_ts",
        "collection_updated_tz",
        "sources"
    ]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            pc = r.get("parentCollection") or {}
            lu = r.get("lastUpdated") or {}
            plu = pc.get("lastUpdated") or {}
            w.writerow({
                "title": r.get("title"),
                "category": r.get("category"),
                "route": pc.get("location", {}).get("routeDesignator"),
                "collection": pc.get("title"),
                "image_url": r.get("url"),
                "uri": r.get("uri"),
                "updated_ts": lu.get("timestamp"),
                "updated_tz": lu.get("timezone"),
                "collection_updated_ts": plu.get("timestamp"),
                "collection_updated_tz": plu.get("timezone"),
                "sources": json.dumps(r.get("sources"))
            })
    return out_path

def getAllImageURLs(csvpath):
    urls = []
    with open(csvpath, "r") as f:
        for r in csv.DictReader(f):
            if r["image_url"]:
                urls.append(r["image_url"])
    return urls

def downloadSingleImage(url, outputPath, i):
    out = os.path.join(outputPath, f"{i}.jpg")
    urllib.request.urlretrieve(url, out)
    return url

def downloadImages(urls, outputPath, max_workers=20):
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for i, u in enumerate(urls, 1):
            ex.submit(downloadSingleImage, u, outputPath, i)

def doScrape():
    makeDirectories(scrapeFolderLocation, imageFolderLocation)
    downloadApiDataToFile(APIURL, apiSaveLocation)
    csvpath = convertToCSV(apiSaveLocation)
    urls = getAllImageURLs(csvpath)
    downloadImages(urls, snapshotImageFolderLocation)

if __name__ == "__main__":
    doScrape()