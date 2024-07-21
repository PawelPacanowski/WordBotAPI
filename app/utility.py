from pydantic import BaseModel


class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message

RESERVED_KEYS = ["_id", "discord_server_id", "discord_user_id", "total_words", "total_flagged_words"]


# def converter(document, exclude_keys: tuple[str] = None, exclude_base: type[BaseModel] = None) -> dict:
#     if document:
#         document_id = str(document["_id"])
#         document.pop("_id")
#         document = {"_id": document_id, **document}
#
#         if exclude_base and issubclass(exclude_base, BaseModel):
#             document.pop("_id")
#             fields = exclude_base.model_fields
#             for field in fields.keys():
#                 if field in document:
#                     document.pop(field)
#
#         if exclude_keys:
#             for key in exclude_keys:
#                 if key in document:
#                     document.pop(key)
#
#         return document
#
#     else:
#         raise TypeError("Document must not be null")


def conv(document, include_id=False) -> dict:
    if document:
        if include_id:
            document_id = str(document["_id"])
            document.pop("_id")
            document = {"_id": document_id, **document}
            return document

        else:
            document.pop("_id")
            return document

    else:
        raise TypeError("Document must not be null")


def validate_and_transform(string: str) -> str:
    if 0 < len(string) < 255:
        return string.strip().lower()
    else:
        raise ValidationError(f"String parameter length must be between 1 and 255 characters: '{string}'")
