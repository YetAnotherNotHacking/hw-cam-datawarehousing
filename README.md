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
The python package installs the commands `sfd-server` and `sfd-client` to your machine. These are how you interface with this program.

The model is that you have clients submitting scraped packs to the server to spread out the load of the scraping, and allowing for the server to be run a nas and have higher performance dedicated computers running the scrapers.

### Server
To run the server, you are going to need to do the following:

1. Create a blank creds.csv (or another name) file:
    ```
    sfd-server gen-creds creds.csv
    ```
2. Add users to the creds file. Here, a username is optional, one will be generated if not supplied.
    ```
    sfd-server add creds.csv --user USER
    ```
3. Start the server. The servers takes in `--uploaddir` as a location to deposit uploaded artifacts. It takes in `--cred-file-location` to use for credentials, this is creds.csv
    ```
    sfd-server run run --uploaddir ups/ --credfilelocation creds.csv
    ```

### Client
To run a client, you must do the following
1. Generate a config with your API token (from adding the user) and the server's internet location.
    ```
    sfd-client-config set --server https://ilove.penguins:12345 --apikey ath15f15nT041r34134P1dk3y0u4fu6k1ng1dum34553a629fbd42cf80513caa3e09
    ```
2. Run the client and submit the data to the server
    ```
    sfd-client --state alaska --upload
    ```
    OR
    ```
    sfd-client --all --upload
    ```
    Warning: running all is INSANELY resources intensive!

## Data sources
State highway data sources: https://silverflag.net/resources/publicdata/dotcctv.html

## Siege info
This program is being made along with the HackClub Siege hackathon. Below is information about it.
Siege 1: Coins are the name for the downloaded packets that each state is generating after their scrapes. All code that processes this will reflect this.
Coins are downloaded by scrapers and then submitted to a server for storage. Coins track scraper trust/reliability.