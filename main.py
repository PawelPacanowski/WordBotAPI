import pymongo.errors
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values
import os

app = FastAPI()

# client = AsyncIOMotorClient(dotenv_values(".env").get("URI"))
# database = client[dotenv_values(".env").get("NAME")]

client = AsyncIOMotorClient(os.environ.get('URI'))
database = client[os.environ.get('NAME')]

user_profiles = database['user_profiles']
server_profiles = database['server_profiles']


class ServerProfile(BaseModel):
    discord_server_id: int = Field(gt=0)
    total_words: int = Field(default=0)
    total_flagged_words: int = Field(default=0)


class UserProfile(BaseModel):
    discord_user_id: int = Field(gt=0)
    discord_server_id: int = Field(gt=0)
    total_words: int = Field(default=0, ge=0)
    total_flagged_words: int = Field(default=0, ge=0)


RESERVED_KEYS = ["_id", "discord_server_id", "discord_user_id", "total_words", "total_flagged_words"]


def converter(document, exclude_keys: tuple[str] = None, exclude_base: type[BaseModel] = None) -> dict:
    if document:
        document_id = str(document["_id"])
        document.pop("_id")
        document = {"_id": document_id, **document}

        if exclude_base and issubclass(exclude_base, BaseModel):
            document.pop("_id")
            fields = exclude_base.model_fields
            for field in fields.keys():
                if field in document:
                    document.pop(field)

        if exclude_keys:
            for key in exclude_keys:
                if key in document:
                    document.pop(key)

        return document

    else:
        return {}


@app.get("/servers/check_if_exists/{discord_server_id}")
async def check_if_server_exists(discord_server_id: int):
    profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    if profile:
        return True
    else:
        return False


@app.get("/users/check_if_exists/{discord_server_id}/{discord_user_id}")
async def check_if_user_exists(discord_server_id: int, discord_user_id: int):
    profile = await user_profiles.find_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id})
    if profile:
        return True
    else:
        return False


@app.get("/users/get_word_count/{discord_server_id}/{discord_user_id}/{word}")
async def get_user_word_count(discord_server_id: int, discord_user_id: int, word: str):
    if word in RESERVED_KEYS:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Cannot get reserved keys. Use dedicated request instead.")

    else:
        response = await user_profiles.find_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id})

        if response:
            return response[word]


@app.get("/users/get_flagged_words_count/{discord_server_id}/{discord_user_id}")
async def get_user_flagged_words_count(discord_server_id: int, discord_user_id: int):
    response = await user_profiles.find_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id})
    if response:
        return converter(response, exclude_base=UserProfile)


@app.get("/users/get_total_words/{discord_server_id}/{discord_user_id}")
async def get_user_total_words(discord_server_id: int, discord_user_id: int):
    response = await user_profiles.find_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id})
    if response:
        return response["total_words"]


@app.get("/users/get_total_flagged_words/{discord_server_id}/{discord_user_id}")
async def get_user_total_flagged_words(discord_server_id: int, discord_user_id: int):
    response = await user_profiles.find_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id})
    if response:
        return response["total_flagged_words"]


@app.get("/servers/get_word_count/{discord_server_id}/{word}")
async def get_server_word_count(discord_server_id: int, word: str):
    if word in RESERVED_KEYS:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Cannot get reserved keys. Use dedicated request instead.")

    else:
        response = await server_profiles.find_one({"discord_server_id": discord_server_id})
        if response:
            return response[word]


@app.get("/servers/get_flagged_words_count/{discord_server_id}")
async def get_server_flagged_words_count(discord_server_id: int):
    response = await server_profiles.find_one({"discord_server_id": discord_server_id})
    if response:
        return converter(response, exclude_base=ServerProfile)


@app.get("/servers/get_total_words/{discord_server_id}")
async def get_server_total_words(discord_server_id: int):
    response = await server_profiles.find_one({"discord_server_id": discord_server_id})
    if response:
        return response["total_words"]


@app.get("/servers/get_total_flagged_words/{discord_server_id}")
async def get_server_total_flagged_words(discord_server_id: int):
    response = await server_profiles.find_one({"discord_server_id": discord_server_id})
    if response:
        return response["total_flagged_words"]


@app.get("/servers/get_flagged_words/{discord_server_id}/{dictionary}")
async def get_server_flagged_words(discord_server_id: int, dictionary: bool = False):
    profile = await server_profiles.find_one({"discord_server_id": discord_server_id})

    if not profile:
        return

    profile_words_dict = (converter(profile, exclude_base=ServerProfile))

    if dictionary:
        for key in profile_words_dict.keys():
            profile_words_dict[key] = 0

        return profile_words_dict
    else:
        return list(profile_words_dict.keys())


@app.post("/servers/add_profile/{discord_server_id}", description="Creates empty server profile")
async def create_server_profile(discord_server_id: int):
    try:
        profile = ServerProfile(discord_server_id=discord_server_id)
        result = await server_profiles.insert_one(profile.dict())
        return {"_id": str(result.inserted_id), **profile.dict()}
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicated entry. Server profile already exists.")


@app.post("/users/add_profile/{discord_server_id}/{discord_user_id}", description="Creates empty user profile. Does nothing if server profile does not exist. Should be used when new member joins")
async def create_user_profile(discord_server_id: int, discord_user_id: int):
    if await server_profiles.find_one({"discord_server_id": discord_server_id}):
        try:
            profile = UserProfile(discord_server_id=discord_server_id, discord_user_id=discord_user_id)
            result = await user_profiles.insert_one(profile.dict())
            return {"_id": str(result.inserted_id), **profile.dict()}
        except pymongo.errors.DuplicateKeyError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicated entry. User profile already exists.")

    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Server profile does not exist.")


@app.post("/users/add_multiple_profiles/{discord_server_id}", description="Creates empty user profiles. Does nothing if server profile does not exist")
async def create_multiple_user_profiles(discord_server_id: int, users: list[int]):
    if await server_profiles.find_one({"discord_server_id": discord_server_id}):
        try:
            bulk_ops = [
                pymongo.InsertOne(
                    document=UserProfile(discord_server_id=discord_server_id, discord_user_id=discord_user_id).dict()
                )
                for discord_user_id in users
            ]

            result = await user_profiles.bulk_write(bulk_ops)
            if result:
                return True

        except pymongo.errors.DuplicateKeyError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicated entry. User profile already exists.")

    else:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Server profile does not exist.")


# each dictionary represents a user
# each dictionary must have discord_user_id
@app.put("/users/update_all_users/{discord_server_id}", description="Updates every user of the server. Must provide list[dict], where every dict is a user. Every user must have 'discord_user_id' key. Order of keys does not matter. Keys that are not flagged on the server are ignored")
async def update_all_user_profiles(discord_server_id: int, users: list[dict]):
    # first must get schema from server_profile for data integrity
    server_profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    flagged_words = converter(server_profile, exclude_base=ServerProfile)
    bulk_ops = []
    for user in users:
        filtered_data = {"total_flagged_words": 0}
        for word in user.keys():
            if word in flagged_words.keys():
                filtered_data.update({word: user[word]})
                filtered_data["total_flagged_words"] += filtered_data[word]


        filtered_data.update({"total_words": user["total_words"]})

        print(filtered_data)

        bulk_ops.append(pymongo.UpdateOne(
            filter={"discord_server_id": discord_server_id, "discord_user_id": user["discord_user_id"]},
            update={"$set": filtered_data}
        ))

    result = await user_profiles.bulk_write(bulk_ops)

    if result:
        return True
    else:
        return False


@app.put("/users/update_total_words_count/{discord_server_id}/{discord_user_id}/{count}", description="Updates total words count of the user. Must be explicitly provided because API does not have access to every user message")
async def update_user_total_words_count(discord_server_id: int, discord_user_id: int, count: int):
    result = user_profiles.update_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id}, {"$set": {"total_words": count}})
    if result:
        return True


@app.put("/servers/update_total_words_count/{discord_server_id}/{count}", description="Updates total words count in the server. Must be explicitly provided because API does not have access to every server message")
async def update_server_total_words_count(discord_server_id: int, count: int):
    result = server_profiles.update_one({"discord_server_id": discord_server_id}, {"$set": {"total_words": count}})
    if result:
        return True


@app.put("/servers/update_profile/{discord_server_id}", description="Updates counts of every flagged word and total flagged word count, based on user profiles")
async def update_server_profile(discord_server_id: int):
    profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    server_words = converter(profile, exclude_keys=("_id", "discord_server_id"))

    for key in server_words.keys():
        server_words[key] = 0

    async for user in user_profiles.find({"discord_server_id": discord_server_id}):
        user = converter(user, exclude_keys=("_id", "discord_user_id", "discord_server_id"))
        for key in user:
            server_words[key] += user[key]

    await server_profiles.update_one({"discord_server_id": discord_server_id}, {"$set": server_words})
    result = await server_profiles.find_one({"discord_server_id": discord_server_id})
    return converter(result)


@app.put("/servers/add_flagged_words/{discord_server_id}", description="Adds flagged word to the server profile and every corresponding user profile")
async def add_flagged_words(discord_server_id: int, words: list[str]):
    profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    profile_dict = (converter(profile, exclude_base=ServerProfile))

    data = {}

    for word in words:
        _word = word.lower().strip()
        if _word not in profile_dict.keys():
            data.update({_word: 0})

    await server_profiles.update_one({"discord_server_id": discord_server_id}, {"$set": data})
    await user_profiles.update_many({"discord_server_id": discord_server_id}, {"$set": data})

    updated_profile = await server_profiles.find_one({"discord_server_id": discord_server_id})

    if updated_profile:
        return converter(updated_profile)


@app.put("/users/update_users_flagged_words/{discord_server_id}", description="Adds or removes flagged words of users, based on flagged words in the server profile.")
async def update_users_flagged_words(discord_server_id: int):
    server = await server_profiles.find_one({"discord_server_id": discord_server_id})
    server_words = converter(server, exclude_keys=("_id", "discord_server_id",))
    bulk_ops = []

    async for user in user_profiles.find({"discord_server_id": discord_server_id}):
        user_words = converter(user, exclude_keys=("_id", "discord_user_id", "discord_server_id"))

        keys_to_remove = {}
        for key in user_words.keys():
            if key not in server_words:
                keys_to_remove.update({key: 0})

        keys_to_add = {}
        for key in server_words.keys():
            if key not in user_words:
                keys_to_add.update({key: 0})

        bulk_ops.append(pymongo.UpdateOne(
            filter={"discord_server_id": discord_server_id, "discord_user_id": user["discord_user_id"]},
            update={"$unset": keys_to_remove}
        ))

        bulk_ops.append(pymongo.UpdateOne(
            filter={"discord_server_id": discord_server_id, "discord_user_id": user["discord_user_id"]},
            update={"$set": keys_to_add}
        ))

    result = await user_profiles.bulk_write(bulk_ops)

    if result:
        return True


@app.put("/users/add_flagged_words/{discord_server_id}/{discord_user_id}", description="Adds flagged words of the server, to the particular user. Should be used when new member joins")
async def add_user_flagged_words(discord_server_id: int, discord_user_id: int):
    server_profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    server_words = converter(server_profile, exclude_keys=("_id", "discord_server_id", "total_words"))
    user_profile = await user_profiles.find_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id})
    user_words = converter(user_profile, exclude_keys=("_id", "discord_server_id", "discord_user_id", "total_words"))

    keys_to_remove = {}
    for key in user_words.keys():
        if key not in server_words:
            keys_to_remove.update({key: 0})

    keys_to_add = {}
    for key in server_words.keys():
        if key not in user_words:
            keys_to_add.update({key: 0})

    bulk_ops = [
        pymongo.UpdateOne(filter={"discord_server_id": discord_server_id, "discord_user_id": discord_user_id},
                          update={"$unset": keys_to_remove}),
        pymongo.UpdateOne(filter={"discord_server_id": discord_server_id, "discord_user_id": discord_user_id},
                          update={"$set": keys_to_add})
    ]

    await user_profiles.bulk_write(bulk_ops)
    result = await user_profiles.find_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id})

    if result:
        return converter(result)


@app.put("/users/add_words_count/{discord_server_id}/{discord_user_id}")
async def add_user_words_count(discord_server_id: int, discord_user_id: int, words: dict):
    server_profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    schema = converter(server_profile, ("_id", "discord_server_id"))

    user_profile = await user_profiles.find_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id})
    user_data = converter(user_profile, exclude_keys=("_id", "discord_server_id", "discord_user_id"))

    for key in user_data.keys():
        if key == "total_flagged_words":
            continue

        if key == "total_words":
            user_data["total_words"] += words["total_words"]
            continue

        if key in schema and key in words:
            user_data[key] += words[key]
            user_data["total_flagged_words"] += 1

    result = await user_profiles.update_one({"discord_server_id": discord_server_id, "discord_user_id": discord_user_id},
                                            {"$set": user_data})
    if result:
        return True


@app.put("/servers/add_words_count/{discord_server_id}")
async def add_server_words_count(discord_server_id: int, words: dict):
    server_profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    server_data = converter(server_profile, ("_id", "discord_server_id"))

    for key in server_data.keys():
        if key == "total_flagged_words":
            continue

        if key == "total_words":
            server_data["total_words"] += words["total_words"]
            continue

        elif key in server_data and key in words:
            server_data[key] += words[key]
            server_data["total_flagged_words"] += 1

    result = await server_profiles.update_one({"discord_server_id": discord_server_id},
                                              {"$set": server_data})
    if result:
        return True




@app.delete("/servers/remove_flagged_words/{discord_server_id}", description="Removes flagged word from server profile and every user profile")
async def remove_flagged_words(discord_server_id: int, words: list[str]):
    data = {}

    for word in words:
        _word = word.lower().strip()
        data.update({_word: 0})

    await server_profiles.update_one({"discord_server_id": discord_server_id}, {"$unset": data})
    await user_profiles.update_many({"discord_server_id": discord_server_id}, {"$unset": data})

    # must update server flagged words, when any word is deleted
    # ---------- hotfix ---------- #
    profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    server_words = converter(profile, exclude_keys=("_id", "discord_server_id"))

    for key in server_words.keys():
        server_words[key] = 0

    async for user in user_profiles.find({"discord_server_id": discord_server_id}):
        user = converter(user, exclude_keys=("_id", "discord_user_id", "discord_server_id"))
        for key in user:
            server_words[key] += user[key]
    # ---------- hotfix ---------- #

    await server_profiles.update_one({"discord_server_id": discord_server_id}, {"$set": server_words})
    updated_profile = await server_profiles.find_one({"discord_server_id": discord_server_id})
    return converter(updated_profile)


