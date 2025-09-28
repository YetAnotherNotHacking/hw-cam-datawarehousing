# Kansas
# arkansas without the ark


# Iowa
# Iowa-es aaplee?
# Indiana
# thor and doctor joooooooooones - howard/rajesh/bert

#imports
import time
import urllib.request
from urllib.parse import urlparse
import requests
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
stateName = "Kansas"

# Base URLs
serviceURL = "https://www.kandrive.gov/list/cameras"
serviceDomain = "www.kandrive.gov" 
apiEndpoint = "https://www.kandrive.gov/api/graphql"
baseCCTVFrameLocation = "https://www.kcscout.net/TransSuite.VCS.CameraSnapshots/"
apiURL = "https://www.kandrive.gov//List/GetData/Cameras?query={\"columns\":[{\"data\":null,\"name\":\"\"},{\"name\":\"sortOrder\",\"s\":true},{\"name\":\"roadway\",\"s\":true},{\"data\":3,\"name\":\"\"}],\"order\":[{\"column\":1,\"dir\":\"asc\"},{\"column\":2,\"dir\":\"asc\"}],\"start\":0,\"length\":100,\"search\":{\"value\":\"\"}}&lang=en-US"


# basic naming (DO NOT CHANGE THIS FOR ONE SPECIFIC STATE, IF YOU CHANGE THEM CHANGE THEM ALL)
imageFolderName = "img"
snapshotImageFolderName = "snaps"
apidataname = "apidata.json"
temp_folder = "data/"

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

# def downloadApiDataToFile(APIURL, apiSaveLocation):
#     print(f"Downloading \"{APIURL}\" to {apiSaveLocation}")
#     urllib.request.urlretrieve(APIURL, apiSaveLocation)

# dynamic rapid configs
GRAPHQL_QUERY = """query ($input: ListArgs!) {
    listCameraViewsQuery(input: $input) {
        cameraViews {
            category icon
            lastUpdated { timestamp timezone }
            title uri url
            sources { type src }
            parentCollection {
                title uri icon color
                location { routeDesignator }
                lastUpdated { timestamp timezone }
            }
        }
        totalRecords
        error { message type }
    }
}"""
GRAPHQL_VARIABLES = {
    "west": -180, "south": -85, "east": 180, "north": 85,
    "sortDirection": "DESC", "sortType": "ROADWAY",
    "freeSearchTerm": "", "classificationsOrSlugs": [],
    "recordLimit": 150, "recordOffset": 0
}

FIELD_MAP = {
    "id": lambda r: r.get("uri", "").split("/")[1] if r.get("uri") else "",
    "title": lambda r: r.get("title", ""),
    "url": lambda r: r.get("url", ""),
    "source": lambda r: r["sources"][0]["src"] if r.get("sources") else "",
    "roadway": lambda r: r.get("parentCollection", {}).get("location", {}).get("routeDesignator", ""),
    "lastUpdated": lambda r: r.get("lastUpdated", {}).get("timestamp", ""),
}

def stepFetchAPI(api_url=apiURL, scrapeFileLocation=scrapeFileLocation, step=100):
    url = apiEndpoint
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": f"https://{serviceDomain}",
        "Referer": f"https://{serviceDomain}",
        "language": "en",
    }
    query = {
        "query": """query ($input: ListArgs!) {
            listCameraViewsQuery(input: $input) {
                cameraViews {
                    category icon
                    lastUpdated { timestamp timezone }
                    title uri url
                    sources { type src }
                    parentCollection {
                        title uri icon color
                        location { routeDesignator }
                        lastUpdated { timestamp timezone }
                    }
                }
                totalRecords
                error { message type }
            }
        }""",
        "variables": {"input": {
            "west": -180, "south": -85, "east": 180, "north": 85,
            "sortDirection": "DESC", "sortType": "ROADWAY",
            "freeSearchTerm": "", "classificationsOrSlugs": [],
            "recordLimit": 150, "recordOffset": 0
        }}
    }
    all_rows = []
    offset = 0
    while True:
        query["variables"]["input"]["recordOffset"] = offset
        data = json.dumps(query).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            page = json.load(resp)
        rows = page["data"]["listCameraViewsQuery"]["cameraViews"]
        if not rows: break
        all_rows.extend(rows)
        if len(rows) < 150: break
        offset += 150
    result = {"data": all_rows}
    with open(scrapeFileLocation, "w") as f:
        json.dump(result, f, indent=2)
    return result

def downloadApiDataToFile(api_url, out_path):
    combined = stepFetchAPI(api_url)
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
    with open(path, "r") as f:
        rawJSONData = json.load(f)
    rows = rawJSONData["data"]

    out_path = path.replace(".json", ".csv")
    headers = ["id", "title", "url", "source", "roadway", "lastUpdated"]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            row = {
                "id": r.get("uri", "").split("/")[1] if r.get("uri") else "",
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "source": r["sources"][0]["src"] if r.get("sources") else "",
                "roadway": (
                    r["parentCollection"]["location"]["routeDesignator"]
                    if r.get("parentCollection") and r["parentCollection"].get("location")
                    else ""
                ),
                "lastUpdated": r["lastUpdated"]["timestamp"]
                if r.get("lastUpdated")
                else "",
            }
            writer.writerow(row)
    return out_path

def getAllSnapshotURLs(csv_path):
    urls = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("url"):
                urls.append(row["url"])
    return urls

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
})

def downloadSingleImage(url, outputPath):
    try:
        if not url.lower().startswith(("http://", "https://")):
            return None

        name = os.path.basename(urlparse(url).path)
        out = os.path.join(outputPath, name)

        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        headers = {
            "Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
            "Referer": domain,
        }

        r = session.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        with open(out, "wb") as f:
            f.write(r.content)
        return url
    except Exception as e:
        print(f"Error downloading image, {e}")
        pass
        
def downloadImages(ids, outputPath, max_workers=20):
    total = len(ids)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for i, url in enumerate(ex.map(lambda x: downloadSingleImage(x, outputPath), ids), start=1):
            print(f"Downloading image {i}/{total} from {url}")

def doScrape():
    makeDirectories(scrapeFolderLocation, imageFolderLocation)
    stepFetchAPI()
    convertedCSVPath = convertToCSV(apiSaveLocation)
    urls = getAllSnapshotURLs(convertedCSVPath)
    downloadImages(urls, snapshotImageFolderLocation)

if __name__ == "__main__":
    doScrape()