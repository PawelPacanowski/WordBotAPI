from motor.core import AgnosticCollection, AgnosticDatabase
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values
import os

client: AgnosticCollection = ...
database: AgnosticDatabase = ...
users: AgnosticCollection = ...
servers: AgnosticCollection = ...


async def connect():
    global client, database, users, servers

    client = AsyncIOMotorClient(os.environ.get('URI'))
    database = client[os.environ.get('NAME')]
    # client = AsyncIOMotorClient(dotenv_values(".env").get("URI"))
    # database = client[dotenv_values(".env").get("NAME")]
    users = database["user_profiles"]
    servers = database["server_profiles"]


async def close():
    client.close()
