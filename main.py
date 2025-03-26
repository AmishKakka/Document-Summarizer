import gradio as gr
import os
import shutil
import time, concurrent.futures
from pdf2image import convert_from_path
from populateDatabase import ChromaDB, GooglePalmEmbeddings
from processDocument import load_file_and_split, createChunkID
from managePrompts import creatingQuery


def embedDocument(filename):
    """Creates and stores document embeddings."""
    splits = load_file_and_split(f"./assets/{filename}")
    chunks = createChunkID(splits)

    db = ChromaDB(filename, GooglePalmEmbeddings())
    db.addEmbeddings_to_Chroma(chunks)
    db.observeDB()
 
def pages_to_images(filename):
    """Converts PDF pages to images."""
    return convert_from_path(f'./assets/{filename}', dpi=500)

def saveDocument(pdf_file):
    global file_state
    """Saves uploaded PDF to assets folder."""
    if pdf_file is None:
        return None
    os.makedirs('./assets', exist_ok=True)
    base_name = os.path.basename(pdf_file.name)
    shutil.copy(pdf_file.name, os.path.join('./assets', base_name))
    file_state = base_name
    return base_name

def process_document(pdf_file):
    """Handles document processing in parallel."""
    filename = saveDocument(pdf_file)
    if filename is None:
        return None
    
    st = time.time()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_embed = executor.submit(embedDocument, filename)
        future_images = executor.submit(pages_to_images, filename)
        future_embed.result()  
        images = future_images.result() 
    et = time.time()
    print(f"Time taken: {(et-st):.4f} seconds")
    return images, filename

if __name__ == "__main__":
    with gr.Blocks() as demo:
        file_state = gr.State("")
        gr.Markdown("# Document Summarizer")
        with gr.Row():
            with gr.Column(scale=2):
                default = [{"role": "assistant", "content": "Upload a document to generate its summary."}]
                gr.Chatbot(default, type="messages", height=400)
                query = gr.Textbox(type="text", submit_btn=True, label="Query")
                query.submit(creatingQuery, inputs=[query,file_state], outputs=None)

            with gr.Column(scale=1):
                doc_input = gr.File(label="Upload Document", file_types=[".pdf"])
                gallery_output = gr.Gallery(label="Pages")
                doc_input.change(process_document, inputs=doc_input, outputs=[gallery_output, file_state])

    demo.launch()
