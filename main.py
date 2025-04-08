import gradio as gr
import os
import shutil
import time, concurrent.futures
from google import genai
from pdf2image import convert_from_path
from populateDatabase import ChromaDB, GooglePalmEmbeddings
from processDocument import load_file_and_split, createChunkID
from managePrompts import creatingQuery
from gradio.themes.utils.colors import Color


text_color = "#FFFFFF"
app_background = "#0A0A0A"
user_inputs_background = "#193C4C"
widget_bg = "#000100"
button_bg = "#141414"

dark = Color(
    name="dark",
    c50="#F4F3EE",  # not sure
    # all text color:
    c100=text_color, # Title color, input text color, and all chat text color.
    c200=text_color, # Widget name colors (system prompt and "chatbot")
    c300="#F4F3EE", # not sure
    c400="#F4F3EE", # Possibly gradio link color. Maybe other unlicked link colors.
    # suggestion text color...
    c500=text_color, # text suggestion text. Maybe other stuff.
    c600=button_bg,#"#444444", # button background color, also outline of user msg.
    # user msg/inputs color:
    c700=user_inputs_background, # text input background AND user message color. And bot reply outline.
    # widget bg.
    c800=widget_bg, # widget background (like, block background. Not whole bg), and bot-reply background.
    c900=app_background, # app/jpage background. (v light blue)
    c950="#F4F3EE", # not sure atm. 
)

def embedDocument():
    """Creates and stores document embeddings."""
    chunks = []
    doc_chunk = []
    for filename in file_state.value:
        splits = load_file_and_split(f"./assets/{filename}")
        doc_chunk = (createChunkID(splits))
        chunks.extend(doc_chunk)
    print(f"Number of chunks: {len(chunks)}")

    db = ChromaDB(GooglePalmEmbeddings())
    for i in range(0, len(chunks), 100):
        # print(f"Adding chunks {i} to {i+99}")
        db.addEmbeddings_to_Chroma(chunks[i:i+100])
    db.observeDB()
 
def pages_to_images(filename):
    """Converts PDF pages to images."""
    return convert_from_path(f'./assets/{filename}', dpi=500)

def saveDocument(pdf_files):
    """Saves uploaded PDF to assets folder."""
    global file_state
    names = []
    if pdf_files is not None:
        for pdf_file in pdf_files:
            os.makedirs('./assets', exist_ok=True)
            base_name = os.path.basename(pdf_file.name)
            shutil.copy(pdf_file.name, os.path.join('./assets', base_name))
            names.append(base_name)
        file_state.value = names
        print(f"Saved {len(names)} files.")
        print("File names: ", file_state.value)
        embedDocument()

'''def process_document(pdf_file):
    """Handles document processing."""
    filename = saveDocument(pdf_file)
    if filename is None:
        return None
    st = time.time()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_embed = executor.submit(embedDocument)
        future_images = executor.submit(pages_to_images, filename)
        # future_embed.result()  
        images = future_images.result() 
    et = time.time()
    print(f"Time taken: {(et-st):.4f} seconds")
    return images, filename'''

def chat(query, history): 
    history.append({"role": "user", "content": query})
    API_KEY = "your_api_key"
    client = genai.Client(api_key=API_KEY)
    prompt = creatingQuery(query)
    model_output = ""
    for next_text in client.models.generate_content_stream(model='gemini-2.0-flash-001', 
                                                           contents=prompt):
        model_output += next_text.text
        yield model_output
    return model_output

if __name__ == "__main__":
    with gr.Blocks(theme=gr.themes.Monochrome(
               font=[gr.themes.GoogleFont("Montserrat"), "Arial", "sans-serif"],
               primary_hue="sky",  # when loading
               secondary_hue="sky", # something with links
               neutral_hue="dark")) as demo:
        file_state = gr.State()
        file_state.value = []
        
        def show_images(images):
            return [image for image in images]
        
        gr.Markdown("# Document Summarizer")
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.ChatInterface(fn=chat, type='messages')

            with gr.Column(scale=1):
                docs_input = gr.Files(label="Upload Documents", file_types=[".pdf"],
                                      file_count="multiple", allow_reordering=True)
                docs_input.change(saveDocument, inputs=docs_input)

    demo.launch()
