# Arkansas
# Assault Rifle Kansas?

# imports
import time
import subprocess
import urllib.request
import os
import json
import csv
import math
from concurrent.futures import ProcessPoolExecutor

# debug variables
stableTime = False

# standard variables
stateName = "Arkansas"
serviceURL = "https://www.idrivearkansas.com/" 
APIURL = "https://layers.idrivearkansas.com/cameras.geojson"
imageFolderName = "img"
snapshotImageFolderName = "streams"
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

def parseDownloadedFiles(path):
    with open(path) as f:
        data = json.load(f)
    features = data.get("features", [])
    out_path = os.path.splitext(path)[0] + ".csv"
    headers = ["id","status","name","description","route","route_type","direction","lat","lng"]
    with open(out_path,"w",newline="") as f:
        w = csv.DictWriter(f,fieldnames=headers)
        w.writeheader()
        for feat in features:
            p = feat.get("properties",{})
            coords = feat.get("geometry",{}).get("coordinates",[None,None])
            w.writerow({
                "id":p.get("id"),
                "status":p.get("status"),
                "name":p.get("name"),
                "description":p.get("description"),
                "route":p.get("route"),
                "route_type":p.get("route_type"),
                "direction":p.get("direction_name"),
                "lat":coords[1],
                "lng":coords[0]
            })
    return out_path

def csvGetColumnByName(file_path, column_name):
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row[column_name] for row in reader if column_name in row]

def fakeWebBrowserStreamVideo(cam_id, duration, output_file):
    ffmpeg_cmd = [
        "ffmpeg",
        "-headers",
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0\r\nReferer: https://www.idrivearkansas.com/\r\nOrigin: https://www.idrivearkansas.com",
        "-i",
        f"https://actis.idrivearkansas.com/index.php/api/cameras/feed/{cam_id}.m3u8",
        "-t",
        str(duration),
        "-c",
        "copy",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def threadSwarmStreamVideos(camIDs, duration=20):
    print(f"Spawning {len(camIDs)} threads for ffmpeg capture")
    with ProcessPoolExecutor(max_workers=len(camIDs)) as executor:
        futures = [executor.submit(fakeWebBrowserStreamVideo, c, duration, f"{snapshotImageFolderLocation}/{c}.mp4") for c in camIDs]
        for f in futures:
            f.result()

def doScrape():
    makeDirectories()
    downloadApiDataToFile(APIURL, scrapeFileLocation)
    csv_path = parseDownloadedFiles(scrapeFileLocation)
    camIDs = csvGetColumnByName(csv_path, "id") 
    threadSwarmStreamVideos(camIDs, 10)

if __name__ == "__main__":
    doScrape()