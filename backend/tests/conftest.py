import os

# Unit tests run fully offline: blank every sponsor key before the app loads .env
# (python-dotenv does not override variables that are already set).
for key in ("SIE_API_KEY", "SINGLESTORE_URL", "STATSIG_SERVER_KEY", "AMPLITUDE_API_KEY",
            "PERSONA_API_KEY", "LLM_API_KEY"):
    os.environ[key] = ""
os.environ["COGNEE_ENABLED"] = "0"
