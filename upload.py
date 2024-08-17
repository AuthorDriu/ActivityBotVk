from typing import Optional
from tempfile import NamedTemporaryFile
import requests


def upload_file(file, filename: str = None) -> Optional[str]:
    url = "https://file.io"
    data = {
        "maxDownloads": 100,
        "autoDelete": True,
        "expires": "12h"
    }
    response = requests.post(
        url,
        data=data,
        files={"file": (filename, file) if filename else file},
    )
    
    if response.status_code != 200:
        print(response.status_code)
        return None
    
    response_json = response.json()
    
    if not response_json["success"]:
        return None
    
    file_url = f"{url}/{response_json['key']}"
    return file_url


def upload_file_from_bytes(content: bytes, filename: str = None) -> Optional[str]:
    with NamedTemporaryFile("wb") as tmp_writable:
        tmp_writable.write(content)
        tmp_writable.flush()
        
        with open(tmp_writable.name, "rb") as tmp_readable:
            result = upload_file(tmp_readable, filename)
    
    return result