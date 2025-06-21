import json
import os
from typing import Any, Dict, Type, Optional, Callable, get_type_hints

class ConfigField:
    def __init__(self, *, sensitive=False, env_var=None, readonly=False):
        self.sensitive = sensitive
        self.env_var = env_var
        self.readonly = readonly

class ConfigMeta(type):
    def __new__(cls, name, bases, attrs):
        fields = {}
        annotations = attrs.get('__annotations__', {})
        for base in bases:
            if hasattr(base, '__fields__'):
                fields.update(base.__fields__)

        for key, typ in annotations.items():
            val = attrs.get(key, None)
            if isinstance(val, ConfigField):
                fields[key] = (typ, val)
                attrs[key] = None
            else:
                fields[key] = (typ, ConfigField())
        attrs['__fields__'] = fields
        return super().__new__(cls, name, bases, attrs)

class BaseConfig(metaclass=ConfigMeta):
    def __init__(self, **kwargs):
        self._load_env()
        for key, (typ, field) in self.__fields__.items():
            val = kwargs.get(key, getattr(self, key, None))
            if val is not None and not self._check_type(val, typ):
                raise TypeError(f"Field {key} expects type {typ} but got {type(val)}")
            setattr(self, key, val)

    def _load_env(self):
        for key, (typ, field) in self.__fields__.items():
            if field.env_var and field.env_var in os.environ:
                val = os.environ[field.env_var]
                val = self._convert_type(val, typ)
                setattr(self, key, val)

    def _convert_type(self, val: str, typ: Type) -> Any:
        if typ == int:
            return int(val)
        elif typ == float:
            return float(val)
        elif typ == bool:
            return val.lower() in ("true", "1", "yes")
        elif typ == str:
            return val
        elif issubclass(typ, BaseConfig):
            # For nested config from env not supported in this version
            return None
        else:
            return val

    def _check_type(self, val, typ):
        if val is None:
            return True
        if issubclass(type(val), BaseConfig):
            return isinstance(val, typ)
        # simple isinstance check for builtin types
        return isinstance(val, typ)

    @classmethod
    def from_json(cls, filepath: str) -> 'BaseConfig':
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'BaseConfig':
        kwargs = {}
        for key, (typ, field) in cls.__fields__.items():
            if key in data:
                val = data[key]
                if issubclass(typ, BaseConfig):
                    val = typ._from_dict(val)
                kwargs[key] = val
        return cls(**kwargs)

    def to_dict(self, *, include_sensitive=False) -> Dict[str, Any]:
        d = {}
        for key, (typ, field) in self.__fields__.items():
            val = getattr(self, key)
            if issubclass(typ, BaseConfig):
                val = val.to_dict(include_sensitive=include_sensitive)
            elif field.sensitive and not include_sensitive:
                val = "***REDACTED***"
            d[key] = val
        return d

    def reload_from_file(self, filepath: str, on_diff: Optional[Callable[[str, Any, Any], bool]] = None):
        """
        Reload config from JSON file and compare with current.
        on_diff is called with key, old_value, new_value.
        If on_diff returns True, new value is kept, else old value is retained.
        """
        with open(filepath, 'r') as f:
            new_data = json.load(f)
        self._reload_from_dict(new_data, on_diff)

    def _reload_from_dict(self, new_data: Dict[str, Any], on_diff: Optional[Callable[[str, Any, Any], bool]], prefix=""):
        for key, (typ, field) in self.__fields__.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if field.readonly:
                continue

            old_val = getattr(self, key)
            new_val = new_data.get(key, old_val)

            if issubclass(typ, BaseConfig) and isinstance(old_val, BaseConfig):
                old_val._reload_from_dict(new_val or {}, on_diff, prefix=full_key)
            else:
                if old_val != new_val:
                    keep_new = True
                    if on_diff is not None:
                        keep_new = on_diff(full_key, old_val, new_val)
                    if keep_new:
                        if not self._check_type(new_val, typ):
                            raise TypeError(f"Field {full_key} expects type {typ} but got {type(new_val)}")
                        setattr(self, key, new_val)