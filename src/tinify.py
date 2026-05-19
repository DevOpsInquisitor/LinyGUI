import os
import json
import base64
import urllib.request
import urllib.error

key = ""

class AccountError(Exception): pass
class ClientError(Exception): pass
class ServerError(Exception): pass
class ConnectionError(Exception): pass

class Source:
    def __init__(self, url):
        self.url = url
        self.commands = {}

    def preserve(self, *args):
        self.commands["preserve"] = list(args)
        return self

    def resize(self, **kwargs):
        self.commands["resize"] = kwargs
        return self

    def to_file(self, path):
        req = urllib.request.Request(self.url)
        auth = base64.b64encode(f"api:{key}".encode()).decode()
        req.add_header("Authorization", f"Basic {auth}")
        
        if self.commands:
            req.add_header("Content-Type", "application/json")
            data = json.dumps(self.commands).encode()
            req.data = data

        try:
            with urllib.request.urlopen(req) as response:
                result_data = response.read()
                with open(path, "wb") as f:
                    f.write(result_data)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise AccountError("Invalid API key")
            elif e.code in (400, 415):
                raise ClientError(f"Bad request: {e.read().decode()}")
            else:
                raise ServerError(f"Server error: {e.code}")
        except Exception as e:
            raise ConnectionError(f"Network error: {str(e)}")

def from_file(path):
    auth = base64.b64encode(f"api:{key}".encode()).decode()
    with open(path, "rb") as f:
        data = f.read()
        
    req = urllib.request.Request("https://api.tinify.com/shrink", data=data)
    req.add_header("Authorization", f"Basic {auth}")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode())
            return Source(res_json["output"]["url"])
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise AccountError("Invalid API key")
        elif e.code in (400, 415):
            raise ClientError(f"Bad request: {e.read().decode()}")
        else:
            raise ServerError(f"Server error: {e.code}")
    except Exception as e:
        raise ConnectionError(f"Network error: {str(e)}")
