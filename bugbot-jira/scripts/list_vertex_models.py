from google.cloud.aiplatform_v1beta1 import ModelGardenServiceClient
from google.oauth2 import service_account
import os, sys
from dotenv import load_dotenv
load_dotenv()

PROJECT   = os.getenv("GCP_PROJECT")
LOCATION  = os.getenv("GCP_LOCATION", "us-central1")
KEYFILE   = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not (PROJECT and KEYFILE):
    sys.exit("Set GCP_PROJECT and GOOGLE_APPLICATION_CREDENTIALS env vars first")

creds  = service_account.Credentials.from_service_account_file(KEYFILE)
client = ModelGardenServiceClient(credentials=creds)

# parent is ONLY 'publishers/{publisher}'
pager = client.list_publisher_models(
    parent="publishers/google",
    # region is implicit in the endpoint; set via client_options if needed
    # client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
)

print(f"\nGoogle-published models visible in region {LOCATION}:\n")
for m in pager:
    # m.name looks like projects/{proj}/locations/{loc}/publishers/google/models/{id}
    model_id = m.name.split("/")[-1]
    print(f"{model_id:<35} — ")
