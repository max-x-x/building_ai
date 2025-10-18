from pydantic import BaseModel

class GenerateRequest(BaseModel):
    prompt: str

class ExtractRequest(BaseModel):
    text: str

class ObjectQuestionRequest(BaseModel):
    object_id: str
    token: str
    question: str

class ObjectInfoRequest(BaseModel):
    object_id: int
    token: str
