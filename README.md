# hw-cam-datawarehousing
Mass data colleciton of highway cameras.

## Video Demo
http://silverflag.net/sfdatawaredemo.mp4

## Installation
There is a package uploaded to PyPi for this program. Install it with:
```
pip install silverflaghwdata
```

## Usage
The python package installs the following command to your system:
```
silverflag-dot-scraper
```
You are able to run it for all states by just running that command, or run a specific state (see currently supported list as it's still in development)
```
silverflag-dot-scraper alaska
```
All data is outputted to a `data/` directory where you run the command.

## Data sources
State highway data sources: https://silverflag.net/resources/publicdata/dotcctv.html
