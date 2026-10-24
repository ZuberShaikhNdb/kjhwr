import os

# Must be set before the app/config modules are imported anywhere.
os.environ["DEMO_MODE"] = "1"
os.environ["STATIC_DIR"] = "/nonexistent"
