import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import requests
import tempfile
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

load_dotenv()

# ENV VARS
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")
ADX_CLUSTER = os.getenv("ADX_CLUSTER")
ADX_DATABASE = os.getenv("ADX_DATABASE")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")


def transcribe_audio(file_path):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_input = speechsdk.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config, audio_input)
    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return None


def generate_kql(spoken_text: str) -> str:
    prompt = f"""
You are a Kusto Query Language (KQL) expert for Azure Data Explorer. Return only a valid KQL query for the table `newtablwithmoredays`.

🗂️ The table columns:
Timestamp, Gen_RPM, Gen_Bear_Temp, Gen_Phase1_Temp, Gen_Phase2_Temp, Gen_Phase3_Temp, Gear_Oil_Temp, Gear_Bear_Temp, Nac_Temp, Rtr_RPM, Amb_WindDir, Amb_Temp, Prod_TotActPwr, Prod_TotReactPwr, Gen_SlipRing_Temp, Blds_PitchAngle, Grid_Prod_Pwr, Grid_CosPhi, Grid_Prod_Freq, Grid_Prod_VoltPhse1, Grid_Prod_VoltPhse2, Grid_Prod_VoltPhse3, Grid_Busbar_Temp, Gen_Bear2_Temp, Nac_Direction, Predicted_TotActPwr.

🧠 INSTRUCTIONS:
- If the user asks for **average, sum, or count**, use `print` and `toscalar(...)`.
- Wind speed corresponds to Gen_RPM.
- For the **latest or current value**, use:
    `newtablwithmoredays | top 1 by Timestamp desc | project column = ColumnName`
- For a **specific absolute date**, use:
    `newtablwithmoredays | where Timestamp == datetime(YYYY-MM-DD HH:mm:ss) | project ...`
- If the user asks for **"yesterday"**, interpret it as the latest available date minus 1 day, using:
    `let latestDate = toscalar(newtablwithmoredays | summarize max(Timestamp)); newtablwithmoredays | where Timestamp between (startofday(latestDate - 1d) .. endofday(latestDate - 1d)) | summarize ...`
- If the user asks for **"two days ago"**, use:
    `let latestDate = toscalar(newtablwithmoredays | summarize max(Timestamp)); newtablwithmoredays | where Timestamp between (startofday(latestDate - 2d) .. endofday(latestDate - 2d)) | summarize ...`
- For **date ranges like "last 3 days"**, use:
    `let latestDate = toscalar(newtablwithmoredays | summarize max(Timestamp)); newtablwithmoredays | where Timestamp between (latestDate - 3d) .. latestDate | summarize ...`
- Do **not** use SQL keywords like SELECT, FROM, or GROUP BY.
- Use only the provided column names.
- Always return **only the KQL query without explanation or extra text**.

✅ Examples:
print avg_temp = toscalar(newtablwithmoredays | summarize avg(Amb_Temp))
newtablwithmoredays | top 1 by Timestamp desc | project GenRPM = Gen_RPM
let latestDate = toscalar(newtablwithmoredays | summarize max(Timestamp)); newtablwithmoredays | where Timestamp between (startofday(latestDate - 1d) .. endofday(latestDate - 1d)) | summarize avgTemp = avg(Amb_Temp)

User input: "{spoken_text}"
"""
    headers = {"Content-Type": "application/json", "api-key": OPENAI_API_KEY}
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    url = f"{OPENAI_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={OPENAI_API_VERSION}"
    response = requests.post(url, headers=headers, json=payload, verify=False)
    kql = response.json()["choices"][0]["message"]["content"].strip()

    if "select" in kql.lower() or "from" in kql.lower():
        kql = "// Invalid SQL keywords replaced\nprint result = 0"
    return kql


def run_kql(kql_query: str):
    kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
        ADX_CLUSTER, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
    )
    client = KustoClient(kcsb)
    result = client.execute(ADX_DATABASE, kql_query)
    rows = list(result.primary_results[0])
    return rows[0][0] if rows else None


def summarize_result(spoken_text, value) -> str:
    prompt = f"""The user asked: "{spoken_text}"\nThe result is: "{value}"\nGenerate a short, voice assistant-style reply."""
    headers = {"Content-Type": "application/json", "api-key": OPENAI_API_KEY}
    payload = {"messages": [{"role": "user", "content": prompt}], "temperature": 0.5}
    url = f"{OPENAI_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={OPENAI_API_VERSION}"
    response = requests.post(url, headers=headers, json=payload, verify=False)
    return response.json()["choices"][0]["message"]["content"].strip()


import uuid

def synthesize_text_to_audio(text: str) -> str:
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)

    filename = f"{uuid.uuid4().hex}.wav"
    file_path = os.path.join("static", "audio", filename)

    audio_config = speechsdk.audio.AudioOutputConfig(filename=file_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config, audio_config)
    synthesizer.speak_text_async(text).get()

    return filename  # Return just the filename
