import requests
import argparse
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

auth_token = os.getenv("AUTH_TOKEN")

parser = argparse.ArgumentParser(description="run enviro+ and post to stadtpuls.com")
parser.add_argument("--host", nargs="?", type=str, default="http://localhost:4000")
parser.add_argument("-v", "--verbose", type=bool, default=False)

args = parser.parse_args()

host = args.host
verbose = args.verbose


def post_data(payload, sensor_id):
    url = "{}/api/v3/sensors/{}/records".format(host, sensor_id)
    headers = {"authorization": "Bearer {}".format(auth_token)}
    if verbose:
        print(payload)
        print(payload, sensor_id, url)
    r = requests.post(url, json={"measurements": [payload]}, headers=headers)

    print(r.status_code)
    print(r.text)


post_data(3, 1)
