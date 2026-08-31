import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter(prefix="/download", tags=["Download"])

@router.get("/app")
async def download_android_app():
    # Check if a compiled APK exists in known locations
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
    
    # Otherwise, redirect to the GitHub repository release / releases page
    return RedirectResponse(
        url="https://github.com/najmul5524/Forex-Alert/releases/latest",
        status_code=307
    )
