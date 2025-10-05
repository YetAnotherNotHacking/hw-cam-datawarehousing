# hw-cam-datawarehousing
Mass data colleciton of highway cameras.

## Video Demo
https://silverflag.net/sfdatawaredemo.mp4

## Installation
There is a package uploaded to PyPi for this program. Install it with:
```
pip install silverflaghwdata
```

## Usage
The python package installs the commands `sfd-server`, `sfd-clientcfg`, `sfd-client` to your machine. These are how you interface with this program.

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
    sfd-server run --uploaddir ups/ --credfilelocation creds.csv
    ```
You are also able to see client contributions using the `sfd-server` command.
```
sfd-server leaderboard trust-file.json LENGTH
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

Siege Week 1: The program follows the coin theme, the reliability and contributions of the scraping clients are tracked and visible through the leaderboard command. According to organizers, a loose interpretation like this is suffecient. ([source](https://hackclub.slack.com/archives/C08SKC6P85V/p1759184234278029?thread_ts=1759183466.135219&cid=C08SKC6P85V))