import subprocess, uuid, os, glob
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ihatepdfs Backend - Free PDF to Word")

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

    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "docx",
        input_path,
        "--outdir", output_dir
    ]

    try:
        run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("LibreOffice STDOUT:", run.stdout)
        print("LibreOffice STDERR:", run.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion command failed: {e}")

    # Match ANY docx output
    docx_files = glob.glob(f"/tmp/{file_id}*.docx")

    if not docx_files:
        raise HTTPException(status_code=500, detail=f"Converted file not found. LO stderr: {run.stderr}")

    output_path = docx_files[0]

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="converted.docx"
    )

