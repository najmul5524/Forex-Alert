import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter(prefix="/download", tags=["Download"])

@router.get("/app")
async def download_android_app():
    possible_paths = [
        "forex_alert_mobile/build/app/outputs/flutter-apk/app-release.apk",
        "forex_alert_mobile/build/app/outputs/flutter-apk/app-debug.apk",
        "app/static/downloads/ForexAlert.apk",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return FileResponse(
                path=p,
                filename="ForexAlert.apk",
                media_type="application/vnd.android.package-archive"
            )
    
    # Direct to GitHub Repository main repository
    return RedirectResponse(
        url="https://github.com/najmul5524/Forex-Alert",
        status_code=307
    )
