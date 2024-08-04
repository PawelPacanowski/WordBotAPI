from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    discord_server_id: int = Field(default=..., gt=0)
    discord_user_id: int = Field(default=..., gt=0)
    total_words: int = Field(default=0, ge=0)
    total_flagged_words: int = Field(default=0, ge=0)
    words: dict = Field(default={})


class UserExists(BaseModel):
    exists: bool = Field()


class UserTotalWords(BaseModel):
    total_words: int = Field()


class UserTotalFlaggedWords(BaseModel):
    total_flagged_words: int = Field()


class UserFlaggedWords(BaseModel):
    words: dict = Field()


class UserWordCount(BaseModel):
    words: dict = Field()


class UserCreateResult(BaseModel):
    success: bool = Field()


class UserCreateMultipleResult(BaseModel):
    inserted_count: int = Field(default=0)
    conflicts_count: int = Field(default=0)
    unhandled_errors: int = Field(default=0)
    inserted: list[int] = Field(default=[])
    conflicts: list[int] = Field(default=[])
    errors: list = Field(default=[])


class UserFlagWordsResult(BaseModel):
    flagged_count: int = Field()
    conflicts_count: int = Field()
    flagged: list[str] = Field()
    conflicts: list[str] = Field()


class UserUnflagWordsResult(BaseModel):
    unflagged_count: int = Field()
    ignored_count: int = Field()
    unflagged: list[str] = Field()
    ignored: list[str] = Field()


class UserUpdateTotalWordsResult(BaseModel):
    success: bool = Field()


class UserUpdateFlagsResult(BaseModel):
    success: bool = Field()


class UserRemoveResult(BaseModel):
    success: bool = Field()


class UserSetDataResult(BaseModel):
    success: bool = Field()