# Windows machines with antivirus HTTPS scanning (e.g. Avast) intercept TLS
# with a locally-generated certificate that's trusted by the OS but not by
# Python's bundled certifi CA list, causing SSLCertVerificationError on every
# request. truststore makes Python's ssl module defer to the OS trust store
# instead, which already trusts it. Must run before any ssl.SSLContext is
# created, so it's done here at package import time.
import truststore

truststore.inject_into_ssl()

# Load backend/.env (if present) before any submodule reads a process env var
# at import time — e.g. race_summary.narrator constructs its Anthropic()
# client as soon as it's imported, so ANTHROPIC_API_KEY must already be set.
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
