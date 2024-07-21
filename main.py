from fastapi import FastAPI
from app.database import connect, close
from app.endpoints import user_profiles, server_profiles

app = FastAPI()

app.add_event_handler("startup", connect)
app.add_event_handler("shutdown", close)

app.include_router(user_profiles.router, prefix='/users', tags=['Users'])
app.include_router(server_profiles.router, prefix='/servers', tags=['Servers'])
