"""This is a patch to https://github.com/abraunegg/onedrive to support SSO authentication.

This handler simply responds to any POST request by:
    - getting the token from the SSO broker
    - returning the token as a JSON object.

Author: @gchers
"""

import sys
import uvicorn
import datetime
import importlib
from fastapi import FastAPI

# We don't want to change the original name of the module,
# so here's a workaround to import it.
sso = importlib.import_module("linux-entra-sso.linux-entra-sso")
# Init the SSO module.
ssomib = sso.SsoMib(daemon=False)

app = FastAPI()


@app.get("/")
def get_home():
    return "The SSO broker proxy is running"


@app.post("/{path:path}")
def post_home():
    accounts = ssomib.get_accounts()
    if not len(accounts["accounts"]):
        print("No accounts found.")
        sys.exit(1)
    account = accounts["accounts"][0]

    # Get the token.
    response = ssomib.acquire_token_silently(account)

    if not "brokerTokenResponse" in response:
        raise ValueError("No brokerTokenResponse in response")

    token = response["brokerTokenResponse"]

    # Expires on to expire in.
    expires_on = token["expiresOn"]
    expires_on = datetime.datetime.fromtimestamp(expires_on / 1000)
    expires_in = int((expires_on - datetime.datetime.now()).total_seconds())

    return {
        "access_token": token["accessToken"],
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": "NOT_PROVIDED",
        "scope": "Files.ReadWrite Files.ReadWrite.All Sites.ReadWrite.All offline_access",
    }

if __name__ == "__main__":
    uvicorn.run("ssoproxy:app", port=8539, log_level="info")
