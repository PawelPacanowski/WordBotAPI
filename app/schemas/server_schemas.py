from pydantic import BaseModel, Field


class ServerProfile(BaseModel):
    discord_server_id: int = Field(default=..., gt=0)
    total_words: int = Field(default=0, ge=0)
    total_flagged_words: int = Field(default=0, ge=0)
    words: dict = Field(default={})


class ServerExists(BaseModel):
    exists: bool = Field()


class ServerTotalWords(BaseModel):
    total_words: int = Field()


class ServerTotalFlaggedWords(BaseModel):
    total_flagged_words: int = Field()


class ServerFlaggedWords(BaseModel):
    words: dict = Field()


class ServerWordCount(BaseModel):
    words: dict = Field()


class ServerCreateResult(BaseModel):
    created: bool = Field()

    
class ServerFlagWordsResult(BaseModel):
    flagged_count: int = Field()
    conflicts_count: int = Field()
    flagged: list[str] = Field()
    conflicts: list[str] = Field()


class ServerUnflagWordsResult(BaseModel):
    unflagged_count: int = Field()
    ignored_count: int = Field()
    unflagged: list[str] = Field()
    ignored: list[str] = Field()


class ServerUpdateTotalWordsResult(BaseModel):
    success: bool = Field()


class ServerUpdateFlagsResult(BaseModel):
    success: bool = Field()


class ServerGetMembersIds(BaseModel):
    ids: list[str] = Field()
