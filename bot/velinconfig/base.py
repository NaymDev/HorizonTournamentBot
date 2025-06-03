from dataclass import field

class VineConfig:
    _file_hash_: str = field(init=False, default="")
    def compute_hash(self, raw_content: str) -> str:
        return hashlib.sha256(raw_content.encode()).hexdigest()
            
    def load_from_file(self, path: str):
        with open(path, 'r') as f:
            content = f.read()
        self._file_hash = self.compute_hash(content)
        data = json.loads(content)
        for key, value in data.items():
            setattr(self, key, value)

    def has_changed(self, path: str) -> bool:
    with open(path, 'r') as f:
        content = f.read()
    return self.compute_hash(content) != self._file_hash