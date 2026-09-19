import uvicorn

from aurion_remote.config import get_settings
from aurion_remote.app import app
from aurion_remote.one_panel import router as one_router

app.include_router(one_router)

if __name__ == "__main__":
    cfg = get_settings()
    uvicorn.run(app, host=cfg.bind_host, port=cfg.port, reload=False)
