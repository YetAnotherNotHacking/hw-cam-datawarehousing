# Maryland
# Marry the land or something idk what to write here

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
import gzip
import requests
import io
import ffmpeg
from concurrent.futures import ThreadPoolExecutor

# Debugging variables
stableTime = False
debugParse = False

# State specific scraper settings
stateName = "Maryland" 
baseCCTVFrameLocation = "https://chart.maryland.gov/Video/GetVideo/"
serviceURL = "https://chart.maryland.gov/TrafficCameras/GetTrafficCameras"
APIURL = "https://chartexp1.sha.maryland.gov/CHARTExportClientService/getCameraMapDataJSON.do?callback=jQuery35108111033125544597_1759106625910&_=1759106625911"
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
streamsFolderLocation = f"{imageFolderLocation}/{streamsFolderName}"

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

def downloadApiDataToFile(APIURL, apiSaveLocation):
    print(f"Downloading {APIURL} to {apiSaveLocation}")
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Referer": "https://chart.maryland.gov/",
    }
    req = urllib.request.Request(APIURL, headers=headers)
    with urllib.request.urlopen(req) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
    with open(apiSaveLocation, "wb") as f:
        f.write(data)
    return apiSaveLocation

def convert_jsonp_to_csv(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    start = content.find('(') + 1
    end = content.rfind(')')
    data = json.loads(content[start:end])["data"]
    if not data:
        return
    keys = list(data[0].keys())
    output_file = input_file.replace('.json', '.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    return output_file

def build_headers_dict():
    return {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Referer": "https://chart.maryland.gov/",
        "DNT": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }

def build_header_str():
    return ''.join([f"{k}: {v}\r\n" for k, v in build_headers_dict().items()])

def get_name_from_url(url):
    return url.rstrip('/').split('/')[-1]

def resolve_md_stream(video_id):
    url = f"https://chart.maryland.gov/Video/GetVideo/{video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Referer": "https://chart.maryland.gov/"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        text = r.read().decode("utf-8", errors="ignore")
    m_ip = re.search(r"videoIP\s*=\s*'([^']+)'", text)
    m_id = re.search(r"videoID\s*=\s*'([^']+)'", text)
    if not m_ip or not m_id:
        return None
    video_ip = m_ip.group(1)
    video_id = m_id.group(1)
    return f"https://{video_ip}/rtplive/{video_id}/playlist.m3u8"


def csvGetColumnByName(file_path, column_name):
    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        return [row[column_name] for row in reader if column_name in row]

def extract_video_id(url):
    # Handles both full URLs and plain IDs
    m = re.search(r"([0-9a-f]{32})", url)
    return m.group(1) if m else url

def download_clip(url, duration=20):
    header_str = build_header_str()
    video_id = extract_video_id(url)
    resolved = resolve_md_stream(video_id)
    name = video_id
    output_file = f"{streamsFolderLocation}/{name}.mp4"
    try:
        (
            ffmpeg
            .input(resolved, t=duration, headers=header_str)
            .output(output_file, c='copy')
            .run(quiet=False, overwrite_output=True)
        )
    except Exception as e:
        print(f"FAIL clip {url}: {e}")

def process_stream(url, duration=20):
    header_str = build_header_str()
    video_id = extract_video_id(url)
    resolved = resolve_md_stream(video_id)
    name = video_id
    try:
        ffmpeg.input(resolved, ss=0, headers=header_str).output(f"{snapshotImageFolderLocation}/{name}.png", vframes=1).run(quiet=False, overwrite_output=True)
        ffmpeg.input(resolved, t=duration, headers=header_str).output(f"{streamsFolderLocation}/{name}.mp4", c='copy').run(quiet=False, overwrite_output=True)
    except Exception as e:
        print(f"FAIL process {url}: {e}")

def process_streams(url_list):
    with ThreadPoolExecutor(max_workers=16) as executor:
        executor.map(process_stream, url_list)

def genListOfM3U8s(m3u8urls):
    m3s = []
    for url in m3u8urls:
        m3s.append(f"{url}/playlist.m3u8")
    return m3s

def doScrape():
    # real_url = resolve_md_stream("00012848007300bc004c823633235daa")
    # print(real_url)
    makeDirectories()
    apifile = downloadApiDataToFile(APIURL, apiSaveLocation)
    csvlocation = convert_jsonp_to_csv(apifile)
    urls = csvGetColumnByName(csvlocation, "id")
    process_streams(urls)

if __name__ == "__main__":
    doScrape()


