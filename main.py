import gradio as gr
import os
import shutil
import config
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

def setAPIKey(api_key):
    config.API_KEY = api_key
    print(config.API_KEY)

def embedDocument(filenames):
    """Creates and stores document embeddings."""
    chunks = []
    doc_chunk = []
    for filename in filenames:
        splits = load_file_and_split(f"./assets/{filename}")
        doc_chunk = (createChunkID(splits))
        chunks.extend(doc_chunk)
    print(f"Number of chunks: {len(chunks)}")
    for i in range(0, len(chunks), 100):
        config.ChromaDB.addEmbeddings_to_Chroma(chunks[i:i+100])
    config.ChromaDB.observeDB()

def pages_to_images(filename):
    """Converts PDF pages to images."""
    return convert_from_path(f'./assets/{filename}', dpi=500)

def saveDocument(pdf_files):
    """Saves uploaded PDF to assets folder and manages embeddings."""
    global file_state
    names_to_process = []
    os.makedirs('./assets', exist_ok=True)
    config.ChromaDB = ChromaDB(GooglePalmEmbeddings())

    if pdf_files is None and len(config.filesinput) > 0:
        # DELETE previous document embeddings when all the documents are removed.
        files_to_delete = list(config.filesinput)  # Create a copy to avoid modifying during iteration
        for filename in files_to_delete:
            config.ChromaDB.deleteEmbeddings(filename)
            if os.path.exists(os.path.join('./assets', filename)):
                os.remove(os.path.join('./assets', filename))
            config.filesinput.remove(filename)
        print("Deleted all file embeddings and assets")

    elif pdf_files is not None:
        curr_files = set(os.path.basename(pdf_file.name) for pdf_file in pdf_files)

        # Identify files to delete
        files_to_delete = [f for f in config.filesinput if f not in curr_files]
        for filename in files_to_delete:
            config.ChromaDB.deleteEmbeddings(filename)
            if os.path.exists(os.path.join('./assets', filename)):
                os.remove(os.path.join('./assets', filename))
            config.filesinput.remove(filename)
        if files_to_delete:
            print(f"Deleted {len(files_to_delete)} files: {files_to_delete}")

        # Identify files to add
        files_to_add = []
        for pdf_file in pdf_files:
            base_name = os.path.basename(pdf_file.name)
            if base_name not in config.filesinput:
                shutil.copy(pdf_file.name, os.path.join('./assets', base_name))
                files_to_add.append(base_name)
                config.filesinput.add(base_name)
        if files_to_add:
            print(f"Saved {len(files_to_add)} new files: {files_to_add}")
            embedDocument(files_to_add)


def chat(query, history):
    history.append({"role": "user", "content": query})

    if config.API_KEY != "":
        client = genai.Client(api_key=config.API_KEY)
        prompt = creatingQuery(query)
        model_output = ""
        for next_text in client.models.generate_content_stream(model='gemini-2.0-flash-001',
                                                            contents=prompt):
            model_output += next_text.text
            history[-1]["content"] = query
            history.append({"role": "assistant", "content": model_output})
            yield history[-1]
        return history
    else:
        history.append({"role": "assistant", "content": "API Key is not set. Please enter your API key."})
        yield history[-1]
        return history


if __name__ == "__main__":
    config.filesinput = set() # Initialize config.filesinput as a set
    with gr.Blocks(theme=gr.themes.Monochrome(
               font=[gr.themes.GoogleFont("Montserrat"), "Arial", "sans-serif"],
               primary_hue="sky",  # when loading
               secondary_hue="sky", # something with links
               neutral_hue="dark")) as demo:
        file_state = gr.State()
        file_state.value = []

        '''def show_images(images):
            return [image for image in images]'''

        gr.Markdown("# Document Summarizer")
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.ChatInterface(fn=chat, type='messages')

            with gr.Column(scale=1):
                api_key_input = gr.Textbox(label="API Key", placeholder="Enter your API key here",
                                           max_lines=1, max_length=39, submit_btn=True)
                docs_input = gr.Files(label="Upload Documents", file_types=[".pdf"],
                                      file_count="multiple", allow_reordering=True)

                api_key_input.submit(setAPIKey, inputs=api_key_input)
                docs_input.change(saveDocument, inputs=docs_input)

    demo.launch()