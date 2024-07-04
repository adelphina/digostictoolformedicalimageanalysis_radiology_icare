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

def execute_image_processing(input_file_path: Path):
    try:
        app_instance = Application()
        app_instance.argv = ['--input', str(input_file_path), '--output', PROCESSED_DIR]
        app_instance.run()
    except Exception as e:
        logging.error(f"Error processing the image: {e}")
        raise RuntimeError("Error processing the image")

def compose():
    """This function sets up and executes the image processing pipeline."""
    app_context: AppContext = Application.init_app_context(argv=None)  # Pass appropriate arguments if needed
    sample_data_path = Path(app_context.input_path)
    output_data_path = Path(app_context.output_path)
    logging.info(f"sample_data_path: {sample_data_path}")

    sobel_op = SobelOperator(None, CountCondition(None, 1), input_path=sample_data_path, name="sobel_op")
    median_op = MedianOperator(None, name="median_op")
    gaussian_op = GaussianOperator(None, output_folder=output_data_path, name="gaussian_op")
    
    # Assuming these are stored in some application state or context
    sobel_op.execute()
    median_op.execute()
    gaussian_op.execute()

@app.post("/process-image/")
async def process_image(file: UploadFile = File(...)):
    # Save the uploaded file
    upload_id = uuid.uuid4().hex
    input_file_path = Path(UPLOAD_DIR) / f"{upload_id}_{file.filename}"
    with input_file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Call function to process the image
    execute_image_processing(input_file_path)
    
    # Assuming the processed file has the same name in the output directory
    output_file_path = Path(PROCESSED_DIR) / f"{input_file_path.stem}_processed.png"
    
    if not output_file_path.exists():
        return {"error": "Processed image not found"}
    
    return FileResponse(output_file_path, media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7002)
