from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, HTMLResponse
import asyncio
from pydantic import BaseModel
import os
from markdown_it import MarkdownIt
from backend.configs import API_KEY
from google import genai
from backend.processDocument import load_file_and_split, createChunkID
from backend.managePrompts import creatingQuery
from backend.populateDatabase import ChromaDB, GooglePalmEmbeddings

app = FastAPI()
md = MarkdownIt()
origins = [
    "https://www.my-summarizer-app.com",
    "https://my-summarizer-app.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Must replace this later when pushing this application to public use by the websites's URL in Google Cloud
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

class ChatRequest(BaseModel):
    question: str
    # You might also include a session_id here

class DeleteRequest(BaseModel):
    filename: str
    
    
@app.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    if not os.path.exists('assets'):
        os.makedirs('assets')
    file_location = f"assets/{file.filename}"
    if not os.path.exists(file_location):  
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
            
        # Process the uploaded file: split into chunks, create embeddings, and store in ChromaDB
        doc_split = load_file_and_split(file_location)
        file_chunks = createChunkID(doc_split)
        db = ChromaDB(GooglePalmEmbeddings())

        for i in range(0, len(file_chunks), 100):
            db.addEmbeddings_to_Chroma(file_chunks[i:i+100])
        db.observeDB()
        return {"status": "success", "filename": file.filename}


async def stream_generator(response: str):
    for word in response.split():
        yield word + " "
        await asyncio.sleep(0.05)
        
@app.post("/chat")
async def handle_chat(request: ChatRequest):
    # This endpoint receives a JSON question creates a prompt and sends the it to the model for a response.
    prompt = creatingQuery(request.question)
    client = genai.Client(api_key=API_KEY)
    model_output = ""
    for next_text in client.models.generate_content_stream(model='gemini-2.0-flash-001', 
                                                            contents=prompt):
        model_output += next_text.text
    html_content = md.render(model_output)
    return HTMLResponse(content=html_content)

@app.delete("/delete_files")
async def delete_files(file: DeleteRequest):
    file_location = f"assets/{file.filename}"
    print(file_location)
    if os.path.exists(file_location):
        os.remove(file_location)
        db = ChromaDB(GooglePalmEmbeddings())
        db.deleteEmbeddings(file_location)
        return {"status": "success", "message": f"{file.filename} deleted."}
    else:
        return {"status": "error", "message": "File not found."}
    

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")