from fastapi import APIRouter
from fastapi.responses import FileResponse
import os
from pathlib import Path

router = APIRouter(prefix="/extension", tags=["extension"])

@router.get("/download")
async def download_extension():
    # The vsix file should be at backend/static/codeguardian-vscode-1.0.0.vsix
    # or at the root of vscode-extension. Let's look for it.
    backend_dir = Path(__file__).parent.parent.parent.parent
    vscode_ext_dir = backend_dir.parent / "vscode-extension"
    vsix_path = vscode_ext_dir / "codeguardian-vscode-1.0.0.vsix"
    
    if vsix_path.exists():
        return FileResponse(
            path=vsix_path,
            filename="codeguardian-vscode-1.0.0.vsix",
            media_type="application/vsix"
        )
    return {"error": "VSIX file not found. Ensure it has been packaged."}
