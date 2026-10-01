import uvicorn
from fastapi import Depends

from aurion_remote.config import get_settings
from aurion_remote.app import app, require_token
from aurion_remote.one_panel import router as one_router
from aurion_remote.t8i_lab import router as t8i_router

app.include_router(one_router)
app.include_router(t8i_router, dependencies=[Depends(require_token)])

if __name__ == "__main__":
    cfg = get_settings()
    uvicorn.run(app, host=cfg.bind_host, port=cfg.port, reload=False)
