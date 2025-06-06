"""
Serializadores y deserializadores para distintos tipos de datos en el módulo de almacenamiento de TauseStack.
Incluye soporte para texto, JSON, binario y DataFrame (pandas).
"""
import json
from typing import Any

try:
    import pandas as pd
except ImportError:
    pd = None

# Texto

def serialize_text(data: str) -> bytes:
    return data.encode("utf-8")

def deserialize_text(data: bytes) -> str:
    return data.decode("utf-8")

# JSON

def serialize_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")

def deserialize_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"))

# Binario (passthrough)

def serialize_bytes(data: bytes) -> bytes:
    return data

def deserialize_bytes(data: bytes) -> bytes:
    return data

# DataFrame (pandas, CSV)

def serialize_dataframe(df: "pd.DataFrame") -> bytes:
    if pd is None:
        raise ImportError("pandas no está instalado")
    return df.to_csv(index=False).encode("utf-8")

def deserialize_dataframe(data: bytes) -> "pd.DataFrame":
    if pd is None:
        raise ImportError("pandas no está instalado")
    from io import StringIO
    return pd.read_csv(StringIO(data.decode("utf-8")))
