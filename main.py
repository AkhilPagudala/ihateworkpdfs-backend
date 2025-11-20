import subprocess, uuid, os, glob
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ihatepdfs Backend - Free PDF to Word")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/convert")
async def convert_pdf_to_word(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

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
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if hasattr(e, "stderr") else str(e)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {stderr}")

    base = os.path.splitext(os.path.basename(input_path))[0]
    files = glob.glob(os.path.join(output_dir, f"{base}*.docx"))

    if not files:
        raise HTTPException(status_code=500, detail="Converted file not found")

    output_path = files[0]

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="converted.docx"
    )
