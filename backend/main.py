from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
import asyncio
from pydantic import BaseModel
import os
import tempfile
import firebase_admin
from firebase_admin import credentials, auth
from markdown_it import MarkdownIt
from google import genai
from google.cloud import storage, firestore
import uuid
from backend.populateDatabase import VectorDB, GooglePalmEmbeddings
from backend.processDocument import load_file_and_split, createChunkID
from backend.managePrompts import creatingQuery


# ------------------ Initialization of all variables and services ------------------ #
app = FastAPI()
md = MarkdownIt()

# This path should point to the mounted secret in the Cloud Run service
SECRET_MOUNT_PATH = "/path/to/service-account-key.json"  
storage_client = storage.Client()
#  Ensure this matches your Google Cloud project ID
project_id = "your-gcp-project-id" 
#  Ensure this matches your Firestore database name
firestore_db = firestore.Client(database="your-firestore-database-name")  
#  Ensure this matches your GCS bucket name
BUCKET_NAME = "your-gcs-bucket-name" 
VECTOR_DB = VectorDB(GooglePalmEmbeddings())

if os.path.exists(SECRET_MOUNT_PATH):
    print("Initializing Firebase with mounted secret...")
    cred = credentials.Certificate(SECRET_MOUNT_PATH)
else:
    print("Initializing Firebase with Application Default Credentials (local)...")
    cred = credentials.ApplicationDefault()

# Initialize the Firebase app with the determined credentials
firebase_admin.initialize_app(cred)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)


# ------------------ Pydantic Models ------------------ #
class ChatRequest(BaseModel):
    question: str

class DeleteRequest(BaseModel):
    fileId: str
    

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print("Error decoding token:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"})

    
# ------------------ File Upload Endpoint ------------------ #
@app.post("/upload")
async def handle_upload(user: dict = Depends(get_current_user), file: UploadFile = File(...)):
    # Handles the file upload, chunking document and creating embeddings process
    user_id = user['uid']
    bucket = storage_client.bucket(BUCKET_NAME)
    
    gcs_filename = f"{user_id}/{file.filename}"
    if bucket.blob(gcs_filename).exists():
        raise HTTPException(status_code=400, detail="File with the same name already exists.")
    else:
        blob = bucket.blob(gcs_filename)
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        try:
            #   Splitting the document into chunks and creating embeddings
            split_docs = load_file_and_split(temp_file_path)
            chunks = createChunkID(split_docs)
            VECTOR_DB.addEmbeddings(chunks, uid=user_id, file_id=file.filename)
            print(f"Created embeddings for {len(chunks)} chunks.")
            
            #   Upload the file to GCS
            blob.upload_from_string(content, content_type=file.content_type)
            print(f"File uploaded to GCS at: {gcs_filename}")
            
            unique_file_id = str(uuid.uuid4())
            #   Save metadata to Firestore
            doc_ref = firestore_db.collection("users").document(user_id).collection("files").document(unique_file_id)
            doc_ref.set({
                "userId": user_id,
                "filename": file.filename,
                "gcsPath": gcs_filename,
                "fileSize":len(content),
                "fileType": file.content_type,
                "uploadTime": firestore.SERVER_TIMESTAMP
            })
            print(f"Metadata saved for file: {file.filename}")
            return {"status": "success", "filename": file.filename, "fileId": unique_file_id}
        except Exception as e:
            print(f"Error processing file: {e}")
            raise HTTPException(status_code=500, detail="Internal server error during file processing.")
        finally:
            os.remove(temp_file_path)


# ------------------ Chat Endpoint ------------------ #
async def stream_generator(response: str):
    for word in response.split():
        yield word + " "
        await asyncio.sleep(0.05)

@app.post("/chat")
async def handle_chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    # This endpoint receives a JSON question creates a prompt and sends the it to the model for a response.
    similar_content = VECTOR_DB.query(request.question, uid=user['uid'])
    prompt = creatingQuery(request.question, similar_content)
    client = genai.Client(api_key="your-google-cloud-api-key")  # Replace with your actual API key from Google Cloud Credentials
    
    model_output = ""
    for next_text in client.models.generate_content_stream(model='gemini-2.5-flash-lite', 
                                                            contents=prompt):
        model_output += next_text.text
    html_content = md.render(model_output)
    return StreamingResponse(stream_generator(html_content), media_type="text/html")


# ------------------- Listing user's existing files ------------------ #
@app.get("/list-all-files")
async def list_all_files(user: dict = Depends(get_current_user)):
    user_id = user['uid']
    docs = firestore_db.collection("users").document(user_id).collection("files").stream()
    files = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return {"status": "success", "files": files}


# ------------------ Delete File Endpoint ------------------ #
@app.delete("/delete_files")
async def delete_files(file: DeleteRequest, user: dict = Depends(get_current_user)):
    # This endpoint deletes the file from GCS Bucket storage and its embeddings from Vector Store
    user_id = user['uid']
    file_id = file.fileId
    file_doc_ref = firestore_db.collection("users").document(user_id).collection("files").document(file_id)
    file_doc = file_doc_ref.get()

    if not file_doc.exists:
        raise HTTPException(status_code=404, detail="File metadata not found.")
        
    file_metadata = file_doc.to_dict()
    gcs_path = file_metadata.get("gcsPath")
    
    if gcs_path:
        try:
            # Delete file from GCS bucket
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(gcs_path)
            blob.delete()
            # Delete embeddings from Vector DB
            VECTOR_DB.deleteEmbeddings(uid=user_id, file_id=file_metadata.get("filename"))
            print(f"Deleted file from GCS: {gcs_path}")
        except Exception as e:
            print(f"Error deleting from GCS (might have been already deleted): {e}")
    
    file_doc_ref.delete()
    print(f"Deleted metadata for file ID: {file_id}")
    return {"status": "success", "message": f"File with ID {file_id} deleted."}


# =================== Serve Frontend ================== #
if os.path.exists("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
@app.get("/{full_path:path}")
async def serve_vue_app(full_path: str):
    file_path = f"frontend/dist/{full_path}"
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
        
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {"error": "Frontend not built. Run 'npm run build'"}