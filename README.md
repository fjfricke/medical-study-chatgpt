# LLM-assisted patient preparation study app

This repository contains the Streamlit application used for the LLM-assisted preparation session in a randomised study of physician-led informed consent for elective orthopaedic trauma surgery.

## Study version

The application deployed for the study corresponds to commit [`109b63d`](https://github.com/fjfricke/medical-study-chatgpt/commit/109b63daa4b2e28e17b30755cc6ed71cbe3cf782), deployed on Fly.io. The deployment set `MODEL_NAME=gpt-4o`.

## Run locally

Python 3.12 and [Poetry](https://python-poetry.org/) are required.

```sh
poetry install
poetry run streamlit run src/1_Studie.py
```

Set `OPENAI_API_KEY`, `MODEL_NAME`, and `PASSWORD_HASH` (a SHA-256 hash of the login password) as environment variables. The app reads `settings.json` from its working directory; on Fly.io it reads the file from the mounted `/data` volume. An administrator can create this file through the Admin page by entering the system and assistant start messages. The study system prompt is documented in the manuscript's supplementary material.

## License

The application source code is available under the [MIT License](LICENSE).
