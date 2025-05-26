"""
List all Google-published models that you can load in the chosen region.
Run with:  poetry run python list_vertex_models.py
"""

from google.cloud import aiplatform
from google.oauth2 import service_account
import os, textwrap

PROJECT   = os.getenv("GCP_PROJECT")
LOCATION  = os.getenv("GCP_LOCATION", "us-central1")   # default region
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# ── auth ──────────────────────────────────────────────────────────────
creds = (
    service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
    if CREDENTIALS_PATH else None
)

client = aiplatform.gapic.ModelGardenServiceClient(credentials=creds)
parent = f"projects/{PROJECT}/locations/{LOCATION}"

# filter: only Google-published models
resp = client.list_models(
    parent=parent,
    publisher_filter="google"
)

print(f"\nGoogle-published models in {LOCATION} for project {PROJECT}\n")
for model in resp:
    model_id = model.name.split("/")[-1]          # tail = MODEL_ID
    print(f"{model_id:<35} — {model.display_name}")
print("\nTotal:", len(resp.models))
