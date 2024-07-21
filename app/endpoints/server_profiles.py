from fastapi import HTTPException, status, APIRouter
from app import database
from app.Exceptions.database_exceptions import DatabaseException
from app.crud import servers as server
from app.crud import users as users
from app.schemas import server_schemas as model
from app.utility import RESERVED_KEYS

router = APIRouter()


@router.get("/check_if_exists", response_model=model.ServerExists)
async def check_if_exists(dc_server_id: int):
    try:
        return await server.check_if_exists(database.users, dc_server_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_word_count", response_model=model.ServerWordCount)
async def get_word_count(dc_server_id: int, word: str):
    word.strip().lower()

    if word in RESERVED_KEYS:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Cannot get reserved keys. Use dedicated request instead")

    try:
        return await server.get_word_count(database.users, dc_server_id, word)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_profile", response_model=model.ServerProfile)
async def get_profile(dc_server_id: int):
    try:
        return await server.get_profile(database.users, dc_server_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_total_words", response_model=model.ServerTotalWords)
async def get_total_words(dc_server_id: int):
    try:
        return await server.get_total_words(database.users, dc_server_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_total_flagged_words", response_model=model.ServerTotalFlaggedWords)
async def get_total_flagged_words(dc_server_id: int):
    try:
        return await server.get_total_flagged_words(database.users, dc_server_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_flagged_words", response_model=model.ServerFlaggedWords)
async def get_flagged_words(dc_server_id: int):
    try:
        return await server.get_flagged_words(database.users, dc_server_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.post("/create_profile", response_model=model.ServerCreateResult)
async def create_profile(dc_server_id: int):
    try:
        return await server.create_profile(database.servers, dc_server_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.patch("/flag_words", response_model=model.ServerFlagWordsResult)
async def flag_words(dc_server_id: int, words: list[str]):
    try:
        res_server = await server.flag_words(database.servers, dc_server_id, words)
        res_users = await users.flag_words(database.servers, database.users, dc_server_id, words)

        if res_server and res_users:
            return res_server

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.patch("/unflag_words", response_model=model.ServerUnflagWordsResult)
async def unflag_words(dc_server_id: int, words: list[str]):
    try:
        res_server = await server.unflag_words(database.servers, dc_server_id, words)
        res_users = await users.unflag_words(database.users, dc_server_id, words)

        if res_server and res_users:
            return res_server

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")

