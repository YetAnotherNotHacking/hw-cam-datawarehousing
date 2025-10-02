# Mississippi
# legit only useful for counting seconds :100:

#imports
import time
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import os
import re
import json
import csv
import math
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Debugging variables
stableTime = False
debugParse = False

# State specific scraper settings
stateName = "Mississippi"
baseCCTVFrameLocation = "https://streaminghat1.mdottraffic.com/thumbnail"
serviceURL = "https://www.mdottraffic.com/?showMain=true"
APIURL = "https://www.mdottraffic.com/default.aspx/LoadCameraData"
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
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json; charset=utf-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.mdottraffic.com",
        "Connection": "keep-alive",
        "Referer": "https://www.mdottraffic.com/?showMain=true",
        "Cookie": 'MDOTtrafficLoad={"lat":31.38456625100456,"lon":-89.25216,"zoom":12,"hasSeenPopup1":true,"camerasOn":true,"msgSignsOn":1,"incidentsOn":1}',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "DNT": "1",
        "Sec-GPC": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers"
    }
    r = requests.post(APIURL, headers=headers, json={})
    with open(apiSaveLocation, "wb") as f:
        f.write(r.content)

def convertJSONToCSV(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)["d"]

    output_path = os.path.splitext(input_path)[0] + ".csv"
    keys = ["markerid", "tooltip", "lat", "lon", "markergroup", "icontype"]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for item in data:
            writer.writerow({k: item.get(k, "") for k in keys})
    return output_path

def csvGetColumnByName(file_path, column_name):
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row[column_name] for row in reader if column_name in row]

    return output_path

def getThumbUrl(cam_id):
    url = f"https://www.mdottraffic.com/mapbubbles/camerasite.aspx?site={cam_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    # look for image tags or scripts containing the thumbnail url
    # sample pattern: thumbnail?application=rtplive&streamname=...&...
    img = soup.find("img", src=re.compile(r"thumbnail\?"))
    if img:
        return img["src"]

    # fallback: search in scripts
    scripts = soup.find_all("script")
    for script in scripts:
        text = script.string
        if not text:
            continue
        m = re.search(r'(https?://[^"\']*thumbnail\?[^"\']*)', text)
        if m:
            return m.group(1)

    return None

def getSnapshotUrls(csvloc, max_workers=16):
    camids = [camid.replace("camsite_", "") for camid in csvGetColumnByName(csvloc, "markerid")]
    camurl_map = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(getThumbUrl, camid): camid for camid in camids}
        for future in as_completed(future_map):
            camid = future_map[future]
            try:
                url = future.result()
                if url:
                    camurl_map[camid] = url
                    print(f"camid {camid} -> {url}")
                else:
                    print(f"camid {camid} -> no thumbnail found")
            except Exception as e:
                print(f"camid {camid} -> error {e}")
    return camurl_map

def downloadSingleImage(jpgurl, folder, camid):
    savename = f"{camid}.png"
    path = os.path.join(folder, savename)
    try:
        resp = requests.get(jpgurl, stream=True, timeout=10)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        print(f"Downloaded {camid} -> {path}")
    except Exception as e:
        print(f"Failed {camid} -> {e}")

def downloadJPGImages(camurl_map, folder, max_workers=16):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for camid, jpgurl in camurl_map.items():
            executor.submit(downloadSingleImage, jpgurl, folder, camid)

def doScrape():
    makeDirectories()
    downloadApiDataToFile(APIURL, apiSaveLocation)
    csvloc = convertJSONToCSV(apiSaveLocation)
    camurlmap = getSnapshotUrls(csvloc)
    downloadJPGImages(camurlmap, snapshotImageFolderLocation)

if __name__ == "__main__":
    doScrape()