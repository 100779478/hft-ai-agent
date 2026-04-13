from app.codex_http import DEFAULT_PORT, app

# 这是一行注释
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=DEFAULT_PORT)
# 你好