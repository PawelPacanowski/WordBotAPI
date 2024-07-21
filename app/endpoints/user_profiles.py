from fastapi import HTTPException, status, APIRouter
from app import database
from app.Exceptions.database_exceptions import DatabaseException
from app.crud import servers as server
from app.crud import users as user
from app.schemas import user_schemas as model
from app.utility import RESERVED_KEYS

router = APIRouter()


@router.get("/check_if_exists", response_model=model.UserExists)
async def check_if_exists(dc_server_id: int, dc_user_id: int):
    try:
        return await user.check_if_exists(database.users, dc_server_id, dc_user_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_word_count", response_model=model.UserWordCount)
async def get_word_count(dc_server_id: int, dc_user_id: int, word: str):
    word.strip().lower()

    if word in RESERVED_KEYS:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Cannot get reserved keys. Use dedicated request instead")

    try:
        return await user.get_word_count(database.users, dc_server_id, dc_user_id, word)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_profile", response_model=model.UserProfile)
async def get_profile(dc_server_id: int, dc_user_id: int):
    try:
        return await user.get_profile(database.users, dc_server_id, dc_user_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_total_words", response_model=model.UserTotalWords)
async def get_total_words(dc_server_id: int, dc_user_id: int):
    try:
        return await user.get_total_words(database.users, dc_server_id, dc_user_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_total_flagged_words", response_model=model.UserTotalFlaggedWords)
async def get_total_flagged_words(dc_server_id: int, dc_user_id: int):
    try:
        return await user.get_total_flagged_words(database.users, dc_server_id, dc_user_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.get("/get_flagged_words", response_model=model.UserFlaggedWords)
async def get_flagged_words(dc_server_id: int, dc_user_id: int):
    try:
        return await user.get_flagged_words(database.users, dc_server_id, dc_user_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.post("/create_profile", response_model=model.UserCreateResult)
async def create_profile(dc_server_id: int, dc_user_id: int):
    try:
        return await user.create_profile(database.users, database.servers, dc_server_id, dc_user_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.post("/create_multiple_profiles", response_model=model.UserCreateMultipleResult)
async def create_multiple_profiles(dc_server_id: int, dc_user_ids: list[int]):
    try:
        return await user.create_multiple_profiles(database.users, database.servers, dc_server_id, dc_user_ids)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.put("/update_user_flags", response_model=model.UserUpdateFlagsResult)
async def update_user_flags(dc_server_id: int, dc_user_id: int, data: dict[str, int]):
    try:
        res_server = await server.update_flags(database.servers, dc_server_id, data)
        res_user = await user.update_flags(database.users, dc_server_id, dc_user_id, data)
        if res_user and res_server:
            return model.UserUpdateFlagsResult(success=True)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.put("/update_user_total_words", response_model=model.UserUpdateTotalWordsResult)
async def update_user_total_words(dc_server_id: int, dc_user_id: int, count: int):
    try:
        res_server = await server.update_total_words_count(database.servers, dc_server_id, count)
        res_user = await user.update_total_words_count(database.users, dc_server_id, dc_user_id, count)
        if res_user and res_server:
            return model.UserUpdateTotalWordsResult(success=True)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")


@router.delete("/remove_profile", response_model=model.UserRemoveResult)
async def remove_profile(dc_server_id: int, dc_user_id: int):
    try:
        return await user.remove_user(database.servers, database.users, dc_server_id, dc_user_id)

    except DatabaseException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OverflowError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Over 8-byte ints are not allowed")
