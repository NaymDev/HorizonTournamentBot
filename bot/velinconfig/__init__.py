import hashlib
from dataclasses import field
import json

# Features / Ideas / ToDo
# Define fields attributes: sensitive, dynamic (can be changed at runtime)

class VelinConfig:
    _file_hash: str = field(init=False, default="")
    _data_hash: str = field(init=False, default="")
    def compute_data_hash(self, data) -> (str, str):
        normalized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
            
    def load_from_file(self, path: str):
        with open(path, 'r') as f:
            content = f.read()
        data = json.loads(content)
        self._data_hash = self.compute_data_hash(data)
        for key, value in data.items():
            setattr(self, key, value)
        
        return self

    def has_changed(self, path: str) -> bool:
        with open(path, 'r') as f:
            content = f.read()
        return self.compute_data_hash(content) != self._data_hash