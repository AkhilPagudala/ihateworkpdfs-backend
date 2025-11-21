import subprocess
import uuid
import os
import glob
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
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file_id = str(uuid.uuid4())
    original_pdf = f"/tmp/{file_id}.pdf"
    repaired_pdf = f"/tmp/{file_id}_repaired.pdf"
    output_dir = "/tmp"

    # -----------------------------
    # 1. Save uploaded PDF
    # -----------------------------
    with open(original_pdf, "wb") as f:
        f.write(await file.read())

    # -----------------------------
    # 2. Repair PDF using Ghostscript
    # -----------------------------
    try:
        repair_cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/default",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={repaired_pdf}",
            original_pdf
        ]
        subprocess.run(repair_cmd, check=True)
        input_pdf = repaired_pdf
    except Exception as e:
        input_pdf = original_pdf  # fallback to original if repair fails

    # -----------------------------
    # 3. Convert to DOCX using LibreOffice
    # -----------------------------
    convert_cmd = [
        "libreoffice",
        "--headless",
        "--invisible",
        "--convert-to",
        "docx:MS Word 2007 XML",
        input_pdf,
        "--outdir",
        output_dir
    ]

    run = subprocess.run(convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if run.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"LibreOffice conversion failed. STDERR: {run.stderr}"
        )

    # -----------------------------
    # 4. Locate output DOCX file
    # -----------------------------
    docx_files = glob.glob(f"/tmp/{file_id}*.docx")

    if not docx_files:
        raise HTTPException(
            status_code=500,
            detail="Conversion failed: DOCX file was not generated."
        )

    output_path = docx_files[0]

    # -----------------------------
    # 5. Return file for download
    # -----------------------------
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="converted.docx"
    )
