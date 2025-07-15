from pydantic import BaseModel

class VoiceQueryResponse(BaseModel):
    spoken_text: str
    kql: str
    summary: str
    audio_url: str = None
