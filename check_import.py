import sys
import os

print(f"Current working directory: {os.getcwd()}")
print("--- Attempting to import tausestack.sdk.storage.main ---")
try:
    import tausestack.sdk.storage.main
    print("Successfully imported tausestack.sdk.storage.main")
    print(f"Location: {tausestack.sdk.storage.main.__file__}")
except ImportError as e:
    print(f"Failed to import tausestack.sdk.storage.main: {e}")
except Exception as e:
    print(f"An unexpected error occurred while importing tausestack.sdk.storage.main: {e}")

print("\n--- Attempting to import json_client from tausestack.sdk.storage ---")
try:
    from tausestack.sdk.storage import json_client
    print("Successfully imported json_client from tausestack.sdk.storage")
    print(f"json_client type: {type(json_client)}")
    # Attempt to access the underlying main module if possible
    if hasattr(json_client, '__module__') and 'main' in json_client.__module__:
        print(f"json_client seems to originate from a module related to 'main': {json_client.__module__}")
except ImportError as e:
    print(f"Failed to import json_client from tausestack.sdk.storage: {e}")
except Exception as e:
    print(f"An unexpected error occurred while importing json_client: {e}")


print("\n--- sys.path contents ---")
for p in sys.path:
    print(p)

print("\n--- Checking existence of key files ---")
key_files = [
    "tausestack/__init__.py",
    "tausestack/sdk/__init__.py",
    "tausestack/sdk/storage/__init__.py",
    "tausestack/sdk/storage/main.py"
]
for kf in key_files:
    exists = os.path.exists(kf)
    print(f"{kf}: {'Exists' if exists else 'DOES NOT EXIST'}")
