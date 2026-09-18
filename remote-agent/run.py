import uvicorn

from aurion_remote.config import get_settings


if __name__ == "__main__":
    cfg = get_settings()
    uvicorn.run("aurion_remote.app:app", host=cfg.bind_host, port=cfg.port, reload=False)

