from typing import Any, List
from pydantic import BaseModel, StrictInt, StrictStr, ConfigDict


class VMSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: StrictStr
    uuid: StrictStr
    state: StrictStr
    vcpus: StrictInt
    memG: StrictInt
    host: StrictStr
    FQDN: StrictStr


class VMDetail(VMSummary):
    pass


class VMActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    state: StrictStr


#django habbits