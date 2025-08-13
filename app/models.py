from pydantic import BaseModel

class ADGroupRoles(BaseModel):
    accountName: str
    readonly: str
    readwrite: str
    admin: str
