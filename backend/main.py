from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
from models import VoiceQueryResponse
from azure_services import transcribe_audio, generate_kql, run_kql, summarize_result, synthesize_text_to_audio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/api/voice-query", response_model=VoiceQueryResponse)
async def voice_query(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    spoken_text = transcribe_audio(temp_path)
    if not spoken_text:
        return {"spoken_text": "", "kql": "", "summary": "Speech not recognized.", "audio_url": ""}

    kql = generate_kql(spoken_text)
    value = run_kql(kql)
    summary = summarize_result(spoken_text, value)
    audio_filename = synthesize_text_to_audio(summary)

    return VoiceQueryResponse(
        spoken_text=spoken_text,
        kql=kql,
        summary=summary,
        audio_url=f"/static/audio/{audio_filename}"
    )


@app.get("/api/audio/{filename}")
def get_audio(filename: str):
    return FileResponse(f"static/audio/{filename}", media_type="audio/wav")
