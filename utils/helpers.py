import os
import json
from typing import Any

def save_file(content:Any, filename:str, file_type:str="json"):
    if file_type == "json":
        with open(filename, 'w') as f:
            json.dump(content, f, ensure_ascii=False)
    else:
        with open(filename, 'w') as f:
            f.write(content)


def init_tmp_path():
    os.makedirs("raw/api/details", exist_ok=True)
    os.makedirs("raw/ui/details", exist_ok=True)
