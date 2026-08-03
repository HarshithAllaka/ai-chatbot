from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Welcome to AI Chatbot API"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-chatbot",
        "version": "0.1.0"
    }