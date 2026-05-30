"""Точка входу FastAPI-сервера."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="YouTube Viral Finder API",
    description="Бекенд для пошуку вірусних відео в обраній ніші.",
    version="1.0.0",
)

# CORS — дозволяємо звертатись до бекенду з нашого фронтенду.
# Зараз дозволено всім, потім обмежимо коли запустимо Vercel.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "YouTube Viral Finder API",
        "version": "1.0.0",
        "docs": "/docs",
    }