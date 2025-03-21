# Standard library imports
import os
import sys
import threading
from datetime import datetime
from typing import Dict, Any
import json

# Special sqlite3 hack (must be before other imports)
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Third-party imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn
import requests
from filelock import FileLock
from multiprocessing import Process

# Add the src directory to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))


#from gifted_children_helper.utils.secrets import load_secrets
#load_secrets()

# Local application imports
from backend_fastapi.auth_store import AuthStore
from utils.reports import log_system_usage
from src.crew_factory import run_wrapper


# if exists file ./db/chroma.sqlite3, delete it
if os.path.exists("./db/chroma.sqlite3"):
    os.remove("./db/chroma.sqlite3")

# Create an instance of the FastAPI class
app = FastAPI()

# Add CORS middleware to allow specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
skip_authorization = os.getenv("SKIP_AUTHORIZATION", "true").lower() == "true"

# Initialize AuthStore
auth_store = AuthStore()

def verify_google_token(token: str) -> dict:
    """
    Verify the Google ID token.

    Args:
        token (str): The Google ID token.

    Returns:
        dict: The token information if valid, raises HTTPException otherwise.
    """
    skip_authorization = os.getenv("SKIP_AUTHORIZATION", "true").lower() == "true"
    if skip_authorization:
        return {"sub": "test_user"}
    try:
        response = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.json()
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")

def websocket_callback( *args, **kwargs):
    """
    Callback function to send progress updates via WebSocket.

    Args:
        uuid (str): The unique identifier for the report generation job.
        args: Additional positional arguments.
        kwargs: Additional keyword arguments to send as part of the update.
    """
    logger.info(f"Sending update to WebSocket for UUID : args={args}, kwargs={kwargs}")

@app.get("/health")
@app.get("/healthz")
@app.get("/status")
async def health_check():
    """
    Health check endpoint that responds to multiple paths (/health, /healthz, /status)
    following common REST API conventions.
    
    Returns:
        dict: Health status information including timestamp and service name
    """
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "gifted-children-helper-api"
    }

# Define a route to handle form submissions
@app.post("/generate-report")
async def submit_form(request: Request, form_data: Dict[str, Any]):
    """
    Endpoint to handle dynamic form submission.
    
    Args:
        request (Request): The request object containing headers.
        form_data (Dict[str, Any]): Dynamic form data submitted by the user.
    
    Returns:
        dict: A dictionary containing the job identifier.
    """
    # Extract the token from the Authorization header
    try :
        auth_header = request.headers.get("Authorization")
        if (not auth_header or not auth_header.startswith("Bearer ")) and not skip_authorization :
            raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
        
        token = auth_header.split(" ")[1]
        token_info = verify_google_token(token)
        user_id = token_info['sub']
        logger.info(f"Token info: {token_info}")

    except Exception as e: 
        user_id = "unknown" 
        pass 

    # Ensure uuid is provided in the form data
    if 'uuid' not in form_data:
        raise HTTPException(status_code=400, detail="UUID field is required")
    
    uuid = form_data['uuid']
    
    # Store the authorization
    auth_store.add_auth(uuid, user_id)
    
    # Log the received form data and jobId
    logger.info(f"Received form data: {form_data}")
    logger.info(f"Job ID: {uuid}")
    
    # Build the case dynamically from form data
    case = ""
    for key, value in form_data.items():
        if key == "crew_name":
            crew_name = value
        elif key != 'uuid' and value:  # Skip uuid and empty values
            # Convert snake_case or camelCase to Title Case with spaces
            formatted_key = ' '.join(word.capitalize() for word in key.replace('_', ' ').split())
            case += f"**{formatted_key}:** {value}\n"
    

    # Run the report generation in a separate thread
    
    # thread = threading.Thread(target=run_wrapper, args=(crew_name, case, websocket_callback, uuid))
    # thread.start()
    process = Process(target=run_wrapper, args=(crew_name, case, websocket_callback, uuid))
    process.start()
    log_system_usage()

    # Return the UUID to the frontend immediately
    return {"uuid": uuid}

@app.get("/report_download/{uuid}")
async def report_download(uuid: str):
    """
    HTTP endpoint to download the generated report.
    Returns the PDF with a fixed filename regardless of the UUID.

    Args:
        uuid (str): The unique identifier for the report generation job.

    Returns:
        FileResponse: The generated report file with fixed filename 'final_report.pdf'
    """
    # Check if the report file exists
    pdf_file = f"logs/{uuid}.pdf"
      
    if os.path.exists(pdf_file):
        return FileResponse(
            path=pdf_file, 
            media_type="application/pdf", 
            filename="final_report.pdf"  # Nombre fijo para el archivo descargado
        )
    markdown_file = f"logs/{uuid}.md"
    if os.path.exists(markdown_file):
        return FileResponse(
            path=markdown_file, 
            media_type="text/markdown", 
            filename="final_report.md"  # Nombre fijo para el archivo descargado
        )
    raise HTTPException(status_code=404, detail="Report file not found")

# HTTP endpoint to send report status updates
@app.get("/report_status/{uuid}")
async def report_status(request: Request, uuid: str):
    """
    HTTP endpoint to send report status updates.

    Args:
        uuid (str): The unique identifier for the report generation job.

    Returns:
        dict: The progress status of the report generation.
    """
    # Extract and verify token
    try :
        auth_header = request.headers.get("Authorization")
        if (not auth_header or not auth_header.startswith("Bearer ")) and not skip_authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
        
        token = auth_header.split(" ")[1]
        token_info = verify_google_token(token)
        user_id = token_info['sub']
        
        report_belongs_user = auth_store.verify_auth(uuid, user_id) # Verify authorization
        if not report_belongs_user:
            raise HTTPException(status_code=403, detail="Unauthorized access to report")
    except Exception as e: 
        pass
    progress_file = f"tmp/{uuid}_progress.json"
    lock = FileLock(f"{progress_file}.lock")  # Create a lock for the progress file
    if os.path.exists(progress_file):
        try:
            with lock:  # Use the lock when accessing the file
                with open(progress_file) as f:
                    progress = json.load(f)  # Convert the string to a JSON object
                    logger.info(f"Sending progress update for UUID {uuid}: {progress}")
                    return progress
        except Exception as e:
            logger.error(f"An error occurred while reading progress file: {e}")
            raise HTTPException(status_code=500, detail="An error occurred while reading progress file")
    raise HTTPException(status_code=404, detail="Progress file not found")

# Add cleanup task
@app.on_event("startup")
async def startup_event():
    """Clean up expired entries on startup"""
    auth_store.cleanup()

# Run the application on port 8080
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)


