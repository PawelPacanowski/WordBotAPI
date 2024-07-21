import pymongo
from motor.core import AgnosticCollection
from pymongo.errors import PyMongoError, BulkWriteError

from app.Exceptions.database_exceptions import DatabaseException
from app.crud import servers as crud_server
from app.utility import validate_and_transform, ValidationError
from app.schemas import user_schemas as schema


async def check_if_exists(user_profiles: AgnosticCollection, dc_server_id: int, dc_user_id: int) -> schema.UserExists:
    try:
        profile = await user_profiles.find_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id})
        if profile:
            return schema.UserExists(exists=True)
        else:
            return schema.UserExists(exists=False)

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def get_word_count(user_profiles: AgnosticCollection, dc_server_id: int, dc_user_id: int,
                         word: str) -> schema.UserWordCount:
    try:
        projection = {f"words.{word}": 1, "_id": 0}
        result = await user_profiles.find_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id},
                                              projection)
        if result:
            if len(result["words"]) == 0:
                raise DatabaseException("Key not found in the profile")
            else:
                return schema.UserWordCount(**result)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def get_profile(user_profiles: AgnosticCollection, dc_server_id: int, dc_user_id: int) -> schema.UserProfile:
    try:
        projection = {f"_id": 0}
        user = await user_profiles.find_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id},
                                            projection)
        if user:
            return schema.UserProfile(**user)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def get_total_words(user_profiles: AgnosticCollection, dc_server_id: int,
                          dc_user_id: int) -> schema.UserTotalWords:
    try:
        projection = {f"total_words": 1, "_id": 0}
        result = await user_profiles.find_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id},
                                              projection)
        if result:
            return schema.UserTotalWords(**result)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def get_total_flagged_words(user_profiles: AgnosticCollection, dc_server_id: int,
                                  dc_user_id: int) -> schema.UserTotalFlaggedWords:
    try:
        projection = {f"total_flagged_words": 1, "_id": 0}
        result = await user_profiles.find_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id},
                                              projection)
        if result:
            return schema.UserTotalFlaggedWords(**result)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def get_flagged_words(user_profiles: AgnosticCollection, dc_server_id: int,
                            dc_user_id: int) -> schema.UserFlaggedWords:
    try:
        projection = {"words": 1, "_id": 0}
        result = await user_profiles.find_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id},
                                              projection)
        if result:
            return schema.UserFlaggedWords(**result)

        else:
            raise DatabaseException("Profile not found")

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def create_profile(user_profiles: AgnosticCollection,
                         server_profiles: AgnosticCollection,
                         dc_server_id: int,
                         dc_user_id: int) -> schema.UserCreateResult:
    try:
        server = await server_profiles.find_one({"discord_server_id": dc_server_id})
        if server:
            flags = server.get("words")
            for key in flags.keys():
                flags[key] = 0

            profile = schema.UserProfile(discord_server_id=dc_server_id, discord_user_id=dc_user_id, words=flags)

            result = await user_profiles.insert_one(profile.dict())
            if result:
                return schema.UserCreateResult(success=True)
            else:
                raise DatabaseException("Could not insert the document")
        else:
            raise DatabaseException("Server profile does not exist")

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def create_multiple_profiles(user_profiles: AgnosticCollection,
                                   server_profiles: AgnosticCollection,
                                   dc_server_id: int,
                                   dc_user_ids: list[int]) -> schema.UserCreateMultipleResult:
    try:
        server = await server_profiles.find_one({"discord_server_id": dc_server_id})
        if server:
            flags = server.get("words")
            for key in flags.keys():
                flags[key] = 0

            bulk_ops = [
                pymongo.InsertOne(document=schema.UserProfile(discord_server_id=dc_server_id,
                                                              discord_user_id=user_id,
                                                              words=flags).dict())
                for user_id in dc_user_ids]

            cursor = await user_profiles.bulk_write(bulk_ops, ordered=False)

            if cursor.inserted_count == len(dc_user_ids):
                return schema.UserCreateMultipleResult(inserted_count=len(dc_user_ids),
                                                       inserted=dc_user_ids, )

        else:
            raise DatabaseException("Server profile does not exist")

    except BulkWriteError as bwe:
        inserted = dc_user_ids
        conflicts = []
        errors = []

        for err in bwe.details["writeErrors"]:
            inserted.remove(err["keyValue"]["discord_user_id"])
            if err["code"] == 11000:
                conflicts.append(err["keyValue"]["discord_user_id"])
            else:
                errors.append(err["errmsg"])

        return schema.UserCreateMultipleResult(inserted_count=len(inserted),
                                               conflicts_count=len(conflicts),
                                               unhandled_errors=len(errors),
                                               inserted=inserted,
                                               conflicts=conflicts,
                                               errors=errors)

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def flag_words(server_profiles: AgnosticCollection,
                     user_profiles: AgnosticCollection,
                     dc_server_id: int,
                     words: list[str]) -> schema.UserFlagWordsResult:
    if len(words) == 0:
        raise DatabaseException("List of words must not be empty")

    try:
        input_words = [validate_and_transform(word) for word in words]

        flagged = []
        conflicts = []

        query = {}
        server_flags = await crud_server.get_flagged_words(server_profiles, dc_server_id)
        for new_word in input_words:
            if new_word in server_flags.words.keys() and server_flags.words[new_word] == 0:
                query.update({f"words.{new_word}": 0})
                flagged.append(new_word)
            else:
                conflicts.append(new_word)

        if len(query) == 0:
            raise DatabaseException("Provided data already exists in the server profile")

        await user_profiles.update_many({"discord_server_id": dc_server_id}, {"$set": query})

        return schema.UserFlagWordsResult(flagged_count=len(flagged),
                                          conflicts_count=len(conflicts),
                                          flagged=flagged,
                                          conflicts=conflicts)

    except ValidationError as e:
        raise DatabaseException(f"Error when processing input data: {e}")
    except PyMongoError as e:
        raise DatabaseException(f"Error when processing the request: {e}")


async def unflag_words(user_profiles: AgnosticCollection,
                       dc_server_id: int,
                       words: list[str]) -> schema.UserUnflagWordsResult:
    if len(words) == 0:
        raise DatabaseException("List of words must not be empty")

    try:
        bulk_ops = []
        input_words = [validate_and_transform(word) for word in words]

        unflagged = []
        ignored = []

        async for user in user_profiles.find({"discord_server_id": dc_server_id}):
            flags = user.get("words")
            unset_data = {}
            flagged_count_remove = 0

            for del_word in input_words:
                if del_word in flags.keys():
                    unset_data.update({f"words.{del_word}": 0})
                    flagged_count_remove = flagged_count_remove + flags[del_word]
                    unflagged.append(del_word)
                else:
                    ignored.append(del_word)

            inc_data = {"total_flagged_words": flagged_count_remove * -1}

            bulk_ops.append(pymongo.UpdateOne(
                filter={"discord_server_id": dc_server_id, "discord_user_id": user["discord_user_id"]},
                update={"$unset": unset_data, "$inc": inc_data}
            ))

        result = await user_profiles.bulk_write(bulk_ops)
        if result:
            return schema.UserUnflagWordsResult(unflagged_count=len(unflagged),
                                                ignored_count=len(ignored),
                                                unflagged=unflagged,
                                                ignored=ignored)

    except ValidationError as e:
        raise DatabaseException(f"Error when processing input data: {e}")
    except PyMongoError as e:
        raise DatabaseException(f"Error when processing the request: {e}")


async def update_total_words_count(user_profiles: AgnosticCollection,
                                   dc_server_id: int,
                                   dc_user_id: int,
                                   difference: int) -> schema.UserUpdateTotalWordsResult:
    try:
        query = {"$inc": {"total_words": difference}}
        users_result = user_profiles.update_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id},
                                                update=query)
        if users_result:
            return schema.UserUpdateTotalWordsResult(success=True)

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def update_flags(user_profiles: AgnosticCollection,
                       dc_server_id: int,
                       dc_user_id: int,
                       data: dict[str, int]) -> schema.UserUpdateFlagsResult:
    try:
        flags = await get_flagged_words(user_profiles, dc_server_id, dc_user_id)

        inc_data = {}
        total_count = 0
        for key, val in data.items():
            if key in flags.words.keys():
                total_count = total_count + val
                inc_data.update({f"words.{key}": val})

        inc_data.update({"total_flagged_words": total_count})
        query = {"$inc": inc_data}
        users_result = user_profiles.update_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id},
                                                update=query)
        if users_result:
            return schema.UserUpdateFlagsResult(success=True)

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def remove_user(server_profiles: AgnosticCollection,
                      user_profiles: AgnosticCollection,
                      dc_server_id: int,
                      dc_user_id: int) -> schema.UserRemoveResult:
    try:
        user_profile = await get_profile(user_profiles, dc_server_id, dc_user_id)
        await user_profiles.delete_one({"discord_server_id": dc_server_id, "discord_user_id": dc_user_id})

        flags_update = user_profile.words.copy()
        for key, value in flags_update.items():
            flags_update[key] = value * -1

        await crud_server.update_total_words_count(server_profiles, dc_server_id, user_profile.total_words * -1)
        await crud_server.update_flags(server_profiles, dc_server_id, flags_update)

        return schema.UserRemoveResult(success=True)

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")
