# api.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
from pathlib import Path
import uuid
import os
import logging

from gaussian_operator import GaussianOperator
from median_operator import MedianOperator
from sobel_operator import SobelOperator

from monai.deploy.conditions import CountCondition
from monai.deploy.core import AppContext, Application


app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)


# Directory to save uploaded files
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    # Save the uploaded file
    upload_id = uuid.uuid4().hex
    input_file_path = Path(UPLOAD_DIR) / f"{upload_id}_{file.filename}"
    with input_file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Run the MONAI App to process the image
    try:
        app_instance = App()
        app_instance.argv = ['--input', str(input_file_path), '--output', PROCESSED_DIR]
        app_instance.run()
    except Exception as e:
        logging.error(f"Error processing the image: {e}")
        return {"error": "Error processing the image"}

    # Assuming the processed file has the same name in the output directory
    output_file_path = Path(PROCESSED_DIR) / f"{input_file_path.stem}_processed.png"
    
    if not output_file_path.exists():
        return {"error": "Processed image not found"}

    return FileResponse(output_file_path, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=002        )
    