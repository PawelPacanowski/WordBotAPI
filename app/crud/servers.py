from motor.core import AgnosticCollection
from pymongo.errors import PyMongoError
from app.Exceptions.database_exceptions import DatabaseException
from app.utility import conv, validate_and_transform, ValidationError
from app.schemas import server_schemas as schema


async def check_if_exists(server_profiles: AgnosticCollection, dc_server_id: int) -> schema.ServerExists:
    try:
        profile = await server_profiles.find_one({"discord_server_id": dc_server_id})
        if profile:
            return schema.ServerExists(exists=True)
        else:
            return schema.ServerExists(exists=False)

    except PyMongoError:
        raise DatabaseException("Failure processing the request")


async def get_word_count(server_profiles: AgnosticCollection, dc_server_id: int, word: str) -> schema.ServerWordCount:
    try:
        projection = {f"words.{word}": 1, "_id": 0}
        result = await server_profiles.find_one({"discord_server_id": dc_server_id}, projection)
        if result:
            if len(result["words"]) == 0:
                raise DatabaseException("Key not found in the profile")
            else:
                return schema.ServerWordCount(**result)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError:
        raise DatabaseException("Failure processing the request")


async def get_profile(server_profiles: AgnosticCollection, dc_server_id: int) -> schema.ServerProfile:
    try:
        projection = {f"_id": 0}
        result = await server_profiles.find_one({"discord_server_id": dc_server_id}, projection)
        if result:
            return schema.ServerProfile(**result)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError:
        raise DatabaseException("Failure processing the request")


async def get_total_words(server_profiles: AgnosticCollection, dc_server_id: int) -> schema.ServerTotalWords:
    try:
        projection = {f"total_words": 1, "_id": 0}
        result = await server_profiles.find_one({"discord_server_id": dc_server_id}, projection)
        if result:
            return schema.ServerTotalWords(**result)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError:
        raise DatabaseException("Failure processing the request")


async def get_total_flagged_words(server_profiles: AgnosticCollection,
                                  dc_server_id: int) -> schema.ServerTotalFlaggedWords:
    try:
        projection = {f"total_flagged_words": 1, "_id": 0}
        result = await server_profiles.find_one({"discord_server_id": dc_server_id}, projection)
        if result:
            return schema.ServerTotalFlaggedWords(**result)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError:
        raise DatabaseException("Failure processing the request")


async def get_flagged_words(server_profiles: AgnosticCollection, dc_server_id: int) -> schema.ServerFlaggedWords:
    try:
        projection = {"_id": 0, "words": 1}
        result = await server_profiles.find_one({"discord_server_id": dc_server_id}, projection)
        if result:
            return schema.ServerFlaggedWords(**result)
        else:
            raise DatabaseException("Profile not found")

    except PyMongoError:
        raise DatabaseException("Failure processing the request")


async def create_profile(server_profiles: AgnosticCollection,
                         dc_server_id: int) -> schema.ServerCreateResult:
    try:
        profile = schema.ServerProfile(discord_server_id=dc_server_id)
        server_result = await server_profiles.insert_one(profile.dict())

        if server_result:
            return schema.ServerCreateResult(created=True)

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def flag_words(server_profiles: AgnosticCollection,
                     dc_server_id: int,
                     words: list[str]) -> schema.ServerFlagWordsResult:
    if len(words) == 0:
        raise DatabaseException("List of words must not be empty")

    try:
        input_words = [validate_and_transform(word) for word in words]

        flagged = []
        conflicts = []

        query = {}
        server_flags = await get_flagged_words(server_profiles, dc_server_id)
        for new_word in input_words:
            if new_word not in server_flags.words.keys():
                query.update({f"words.{new_word}": 0})
                flagged.append(new_word)
            else:
                conflicts.append(new_word)

        if len(query) == 0:
            raise DatabaseException("Provided data already exists in the server profile")

        await server_profiles.update_one({"discord_server_id": dc_server_id}, {"$set": query})

        return schema.ServerFlagWordsResult(flagged_count=len(flagged),
                                            conflicts_count=len(conflicts),
                                            flagged=flagged,
                                            conflicts=conflicts)

    except ValidationError as e:
        raise DatabaseException(f"Error when processing input data: {e}")
    except PyMongoError as e:
        raise DatabaseException(f"Error when processing the request: {e}")


async def unflag_words(server_profiles: AgnosticCollection,
                       dc_server_id: int,
                       words: list[str]) -> schema.ServerUnflagWordsResult:
    if len(words) == 0:
        raise DatabaseException("List of words must not be empty")

    try:
        input_words = [validate_and_transform(word) for word in words]

        unflagged = []
        ignored = []

        unset_data = {}
        flagged_count_remove = 0
        server_flags = await get_flagged_words(server_profiles, dc_server_id)
        for del_word in input_words:
            if del_word in server_flags.words.keys():
                unset_data.update({f"words.{del_word}": 0})
                flagged_count_remove = flagged_count_remove + server_flags.words[del_word]
                unflagged.append(del_word)
            else:
                ignored.append(del_word)

        if len(unset_data) == 0:
            raise DatabaseException("No matching words in the server profile")

        inc_data = {"total_flagged_words": flagged_count_remove * -1}

        await server_profiles.update_one({"discord_server_id": dc_server_id}, {"$unset": unset_data, "$inc": inc_data})

        return schema.ServerUnflagWordsResult(unflagged_count=len(unflagged),
                                              ignored_count=len(ignored),
                                              unflagged=unflagged,
                                              ignored=ignored)

    except ValidationError as e:
        raise DatabaseException(f"Error when processing input data: {e}")
    except PyMongoError as e:
        raise DatabaseException(f"Error when processing the request: {e}")


async def update_total_words_count(server_profiles: AgnosticCollection,
                                   dc_server_id: int,
                                   difference: int) -> schema.ServerUpdateTotalWordsResult:
    try:
        query = {"$inc": {"total_words": difference}}
        result = server_profiles.update_one({"discord_server_id": dc_server_id}, update=query)
        if result:
            return schema.ServerUpdateTotalWordsResult(success=True)

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")


async def update_flags(server_profiles: AgnosticCollection,
                       dc_server_id: int,
                       data: dict[str, int]) -> schema.ServerUpdateFlagsResult:
    try:
        flags = await get_flagged_words(server_profiles, dc_server_id)

        inc_data = {}
        total_count = 0
        for key, val in data.items():
            if key in flags.words.keys():
                total_count = total_count + val
                inc_data.update({f"words.{key}": val})

        query = {"$inc": inc_data}
        inc_data.update({"total_flagged_words": total_count})
        result = server_profiles.update_one({"discord_server_id": dc_server_id}, update=query)
        if result:
            return schema.ServerUpdateFlagsResult(success=True)

    except PyMongoError as e:
        raise DatabaseException(f"Database error: {e}")
