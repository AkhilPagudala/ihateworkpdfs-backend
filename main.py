import subprocess, uuid, os, glob
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ihateworkpdfs Backend - Free PDF to Word")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/convert")
async def convert_pdf_to_word(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed.")

    file_id = str(uuid.uuid4())
    input_path = f"/tmp/{file_id}.pdf"
    output_dir = "/tmp"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Create LibreOffice profile directory
    os.makedirs("/root/.config/libreoffice", exist_ok=True)

    cmd = [
    "libreoffice",
    "--headless",
    "--convert-to",
    "docx:MS Word 2007 XML",
    input_path,
    "--outdir",
    output_dir
]

    run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    docx_files = glob.glob(f"/tmp/{file_id}*.docx")

    if not docx_files:
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed. LibreOffice error: {run.stderr}"
        )

    return FileResponse(docx_files[0], filename="converted.docx")


