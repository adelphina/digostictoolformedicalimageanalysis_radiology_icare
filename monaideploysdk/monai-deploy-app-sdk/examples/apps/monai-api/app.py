from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import shutil
from pathlib import Path
import uuid
import os
import logging
import time

from matplotlib import pyplot as plt

from gaussian_operator import GaussianOperator
from median_operator import MedianOperator
from sobel_operator import SobelOperator

from monai.deploy.conditions import CountCondition
from monai.deploy.core import AppContext, Application

# Create FastAPI instance
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Directory to save uploaded files
UPLOAD_DIR = "/home/edna/MONAI/monaideploysdk/monai-deploy-app-sdk/examples/apps/monai-api/uploads"
PROCESSED_DIR = "/home/edna/MONAI/monaideploysdk/monai-deploy-app-sdk/examples/apps/monai-api/processed"
PROCESSED_FILENAME = "final_output.png"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Define the MONAI Application class
class App(Application   ): 
    """This is a very basic application."""

    name = "simple_imaging_app"
    description = "This is a very simple application."
    version = "0.1.0"

    def __init__(self):
        super().__init__()
        self.input_path = None
        self.output_path = None
        self.composed = False
    
    
    
    def compose(self):
        """Compose method defining application workflow."""

        sample_data_path = Path(self.input_path)
        output_data_path = Path(self.output_path)
        logging.info(f"sample_data_path: {sample_data_path}")
        logging.info("hello")

        sobel_op = SobelOperator(self, CountCondition(self, 1), input_path=sample_data_path, name="sobel_op")
        median_op = MedianOperator(self, name="median_op")
        gaussian_op = GaussianOperator(self, output_folder=output_data_path, name="gaussian_op")
        logging.info("hello world")
        
        self.add_flow(
            sobel_op,
            median_op,
            { ("out1", "in1"), },
        )
        self.add_flow(
            median_op,
            gaussian_op,
            { ("out1", "in1"), },
        )
        self.composed = True

    async def execute(self, input_file_path):
     
     if not self.composed:
            self.compose()

     self.input_path = str(input_file_path)
     self.output_path = str(Path(PROCESSED_DIR) / f"{input_file_path.stem}_processed.jpeg")
    
     # Reuse the existing nodes in the workflow graph
     #sobel_op = self.get_node("sobel_op")
    #  median_op = self.get_node("median_op")
    #  gaussian_op = self.get_node("gaussian_op")
    
     # Update the input and output paths of the nodes
    #  sobel_op.input_path = self.input_path
    #  gaussian_op.output_folder = self.output_path
    
     # Run the application workflow
     
     #self.run_async()
    
     # Wait for the processing to complete
    #  while not Path(self.output_path).exists():
    #     time.sleep(0.1)
    
     return Path(self.output_path)


# Instantiate the MONAI Application
app_instance = App()

# Lifespan events
def startup_event():
    try:
        # Configure paths directly
        app_instance.input_path = UPLOAD_DIR
        app_instance.output_path = PROCESSED_DIR
    except Exception as e:
        logging.error(f"Error running the application on startup: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def shutdown_event():
    # Clean up or shutdown tasks if needed
    pass

# Register lifespan event handlers
@app.on_event("startup")
async def startup_handler():
    startup_event()

@app.on_event("shutdown")
async def shutdown_handler():
    shutdown_event()

# API endpoint to proceSS
@app.post("/image/")
async def image(file: UploadFile = File(...)):
    logging.info(f"Received file upload request: {file.filename}")

    # Check if file is received
    if not file:
        logging.error("No file received in the request")
        raise HTTPException(status_code=400, detail="No file received")

    # Save the uploaded file
    upload_id = uuid.uuid4().hex
    input_file_path = Path(UPLOAD_DIR) / f"{upload_id}_{file.filename}"
    
    try:
        with input_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"File {file.filename} uploaded successfully")
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")
    
    # Process the image using the MONAI Application
    output_file_path = Path(PROCESSED_DIR) / PROCESSED_FILENAME 
    try:
        app_instance.run()
        # shutil.copyfile(input_file_path, output_file_path)
        logging.info(f"File processed successfully: {output_file_path}")
    except Exception as e:  
        logging.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail="Error processing file")
    logging.error("here iiiii") 
    # Construct the URL to access the processed image
    output_url = f"/processed/{PROCESSED_FILENAME}"
    
    return {"outputUrl": output_url}
    # return FileResponse(output_file_path, media_type="image/png")

@app.get("/processed/")
async def get_processed_image(filename: str):
    file_path = Path(PROCESSED_DIR) / PROCESSED_FILENAME
    logging.info(f"Attempting to serve file: {file_path}")

    if file_path.exists():
        print(file_path)
        return FileResponse(file_path, media_type='image/png')
    else:
        logging.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

# Main entry point to run FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7002)
