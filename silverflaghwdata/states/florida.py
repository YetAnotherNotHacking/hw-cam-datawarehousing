# Florida man
# florida man gets to drive a car?

# 511 base script modified!!!!! - videos are offered so it's modified to download videos.

#imports
import time
import urllib.request
import os
import re
import json
import csv
import math
import shutil
import ffmpeg
from concurrent.futures import ThreadPoolExecutor, as_completed

# Debugging variables
stableTime = False
debugParse = False

# State specific scraper settings
stateName = "Florida"
baseCCTVFrameLocation = "https://fl511.com/map/Cctv/"
serviceURL = "https://fl511.com/cctv?start=0&length=10&order%5Bi%5D=1&order%5Bdir%5D=asc"
APIURL = "https://fl511.com//List/GetData/Cameras?query={\"columns\":[{\"data\":null,\"name\":\"\"},{\"name\":\"sortOrder\",\"s\":true},{\"name\":\"roadway\",\"s\":true},{\"data\":3,\"name\":\"\"}],\"order\":[{\"column\":1,\"dir\":\"asc\"},{\"column\":2,\"dir\":\"asc\"}],\"start\":0,\"length\":100,\"search\":{\"value\":\"\"}}&lang=en-US"
imageFolderName = "img"
snapshotImageFolderName = "snaps"
apidataname = "apidata.json"
streamsFolderName = "streams"

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
streamsFolderLocation = f"{imageFolderLocation}/{snapshotImageFolderName}"

# This scales poorly, may require improvement in the future. This could be done concurrently, there is nothing stopping that.
def stepFetchAPI(api_url, step=100):
    parsed = urllib.parse.urlparse(api_url)
    qs = urllib.parse.parse_qs(parsed.query)
    base = api_url.split("?")[0]
    query_str = urllib.parse.unquote(qs['query'][0])
    query = json.loads(query_str)
    all_rows = []
    start = 0
    while True:
        query['start'] = start
        new_q = urllib.parse.quote(json.dumps(query))
        url = f"{base}?query={new_q}&lang=en-US"
        print(f"Fetching offset {start}")
        with urllib.request.urlopen(url) as r:
            page = json.load(r)
        rows = page.get('data', [])
        if not rows: break
        all_rows.extend(rows)
        if len(rows) < step: break
        start += step
    return {"data": all_rows}

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
        os.makedirs(streamsFolderLocation, exist_ok=True)
    elif os.path.isdir(scrapeFolderLocation):
        if not os.path.isdir(imageFolderLocation):
            os.makedirs(imageFolderLocation, exist_ok=True)
        if not os.path.isdir(snapshotImageFolderLocation):
            os.makedirs(snapshotImageFolderLocation, exist_ok=True)
        if not os.path.isdir(streamsFolderLocation):
            os.makedirs(streamsFolderLocation, exist_ok=True)


def convertToCSV(path):
    with open(path, 'r') as f:
        rawJSONData = json.load(f)
    rows = rawJSONData['data']
    out_path = scrapeFileLocation.replace('.json', '.csv')
    headers = ['DT_RowId','tooltipUrl','agencyLogoEnabled','visible','isDefault',
            'images','videoUrls','id','sourceId','source','type','areaId','area','sortOrder',
            'roadway','direction','location','lat','lng','linkId1','linkId2',
            'created','lastUpdated','lastEditedBy','defaultCameraSite','nickname',
            'language','jsonData','jsonDataSerialized','region','state','county',
            'city','dotDistrict']
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            lat = lng = None
            wkt = r.get('latLng',{}).get('geography',{}).get('wellKnownText')
            if wkt:
                m = re.search(r'POINT \((-?\d+\.\d+) (-?\d+\.\d+)\)', wkt)
                if m:
                    lng, lat = m.groups()
            video_urls = [img.get('videoUrl') for img in r.get('images', []) if img.get('videoUrl')]
            writer.writerow({
                'DT_RowId': r.get('DT_RowId'),
                'tooltipUrl': r.get('tooltipUrl'),
                'agencyLogoEnabled': r.get('agencyLogoEnabled'),
                'visible': r.get('visible'),
                'isDefault': r.get('isDefault'),
                'images': json.dumps(r.get('images')),
                'videoUrls': json.dumps(video_urls),
                'id': r.get('id'),
                'sourceId': r.get('sourceId'),
                'source': r.get('source'),
                'type': r.get('type'),
                'areaId': r.get('areaId'),
                'area': r.get('area'),
                'sortOrder': r.get('sortOrder'),
                'roadway': r.get('roadway'),
                'direction': r.get('direction'),
                'location': r.get('location'),
                'lat': lat,
                'lng': lng,
                'linkId1': r.get('linkId1'),
                'linkId2': r.get('linkId2'),
                'created': r.get('created'),
                'lastUpdated': r.get('lastUpdated'),
                'lastEditedBy': r.get('lastEditedBy'),
                'defaultCameraSite': r.get('defaultCameraSite'),
                'nickname': r.get('nickname'),
                'language': r.get('language'),
                'jsonData': json.dumps(r.get('jsonData')),
                'jsonDataSerialized': r.get('jsonDataSerialized'),
                'region': r.get('region'),
                'state': r.get('state'),
                'county': r.get('county'),
                'city': r.get('city'),
                'dotDistrict': r.get('dotDistrict')
            })
    return out_path

def getAllCameraIDs(csvpath):
    ids = []
    with open(csvpath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(int(row['id']))
    return ids

# img downloading
def downloadSingleImage(id, outputPath):
    url = f"{baseCCTVFrameLocation}{id}"
    out = os.path.join(outputPath, f"{id}.jpeg")
    with urllib.request.urlopen(url, timeout=10) as response, open(out, 'wb') as f: # use this instead of urlretrieve for timeout!!!! IT WILL BE STUCK OTHERWISE
        shutil.copyfileobj(response, f)
    return url

def downloadImages(ids, outputPath, max_workers=20):
    total = len(ids)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for i, url in enumerate(ex.map(lambda x: downloadSingleImage(x, outputPath), ids), start=1):
            print(f"Downloading image {i}/{total} from {url}")

def loadCameraRowsFromCSV(csv_path):
    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert the 'images' JSON string back to list of dicts
            row['images'] = json.loads(row['images'])
            rows.append(row)
    return rows

def doScrape():
    makeDirectories(scrapeFolderLocation, imageFolderLocation)
    downloadApiDataToFile(APIURL, apiSaveLocation)
    convertedCSVPath = convertToCSV(apiSaveLocation)
    ids = getAllCameraIDs(convertedCSVPath)
    downloadImages(ids, snapshotImageFolderLocation)

if __name__ == "__main__":
    doScrape()