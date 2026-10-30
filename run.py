import uvicorn
import webbrowser
import time
import threading
from pathlib import Path
from backend.app.config import settings

def open_browser():
    time.sleep(1.5)
    url = f"http://{settings.HOST}:{settings.PORT}"
    print(f"\n🚀 TravelCraft AI is running at: {url}")
    print(f"📖 OpenAPI Swagger docs: {url}/docs\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
