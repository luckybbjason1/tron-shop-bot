"""
Railway.app 部署入口
"""
import os
from api.http_server import run

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting server on port {port}...")
    run(port)
