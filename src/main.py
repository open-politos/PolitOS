"""PolitOS entrypoint."""

import os

from dotenv import load_dotenv

load_dotenv()

from src.api.app import create_app

app = create_app()


def main():
    import uvicorn

    host = os.getenv("POLITOS_HOST", "0.0.0.0")
    port = int(os.getenv("POLITOS_PORT", "8000"))
    uvicorn.run("src.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
