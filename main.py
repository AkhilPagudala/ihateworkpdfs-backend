import subprocess
import uuid
import os
import glob
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ihateworkpdfs Backend - Robust PDF to Word")

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

    # 1. Save PDF
    with open(original_pdf, "wb") as f:
        f.write(await file.read())

    # 2. Repair PDF using Ghostscript
    try:
        repair_cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/prepress",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={repaired_pdf}",
            original_pdf
        ]
        subprocess.run(repair_cmd, check=True)
        input_pdf = repaired_pdf
    except Exception:
        input_pdf = original_pdf

    # 3. Force LibreOffice PDF Import Engine
    convert_cmd = [
        "libreoffice",
        "--headless",
        "--infilter=writer_pdf_import",
        "--convert-to", "docx:MS Word 2007 XML",
        input_pdf,
        "--outdir", output_dir
    ]

    process = subprocess.run(
        convert_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if process.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"LibreOffice command failed.\nSTDERR:\n{process.stderr}"
        )

    # 4. Find DOCX Output
    pattern = f"/tmp/{file_id}*.docx"
    docx_files = glob.glob(pattern)

    if not docx_files:
        raise HTTPException(
            status_code=500,
            detail=f"No DOCX created. LibreOffice output:\n{process.stderr}"
        )

    output_path = docx_files[0]

    # 5. Return DOCX
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="converted.docx"
    )
