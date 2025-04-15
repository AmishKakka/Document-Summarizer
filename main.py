import gradio as gr
import os, shutil, time, hashlib
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

# We will initialize these after the API key is set.
config.embedding_function = None
config.ChromaDB = None
config.chat_client = None


def initialize_clients(api_key):
    """Initializes API clients and DB connection after API key is confirmed."""
    if not api_key:
        print("Initialization skipped: API key is empty.")
        return False, "API Key is empty. Cannot initialize services."

    try:
        config.API_KEY = api_key
        print("API Key Set.")

        config.embedding_function = GooglePalmEmbeddings()
        print("Embedding Function Initialized.")

        if not os.path.exists(f'{str(config.session)}/vectorData'):
             os.makedirs(f'{str(config.session)}/vectorData', exist_ok=True)
        config.ChromaDB = ChromaDB(config.embedding_function)
        print("ChromaDB Initialized.")
        config.ChromaDB.observeDB() # See initial state

        config.chat_client = genai.Client(api_key=config.API_KEY)
        print("Chat Client Initialized.")

        return True, "API Key set and services initialized successfully."

    except Exception as e:
        print(f"Error during initialization: {e}")
        config.API_KEY = ""
        config.embedding_function = None
        config.ChromaDB = None
        config.chat_client = None
        return False, f"Error during initialization: {e}. Please check your API key and network connection."

def embedDocument(filenames):
    """Creates and stores document embeddings."""
    if config.ChromaDB is None:
        print("Cannot embed document: ChromaDB not initialized.")
        return

    chunks = []
    doc_chunk = []
    for filename in filenames:
        try:
            splits = load_file_and_split(f'{str(config.session)}/assets/{filename}')
            doc_chunk = (createChunkID(splits))
            chunks.extend(doc_chunk)
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            continue

    if not chunks:
        print("No chunks generated for embedding.")
        return

    print(f"Number of chunks to potentially add: {len(chunks)}")
    for i in range(0, len(chunks), 100):
        batch = chunks[i:i+100]
        try:
            config.ChromaDB.addEmbeddings_to_Chroma(batch)
        except Exception as e:
            print(f"Error adding batch {i//100 + 1} to ChromaDB: {e}")
    config.ChromaDB.observeDB()

# def pages_to_images(filename): # Keep if needed
#     """Converts PDF pages to images."""
#     return convert_from_path(f'{str(config.session)}/assets/{filename}', dpi=500)

def saveDocument(pdf_files, progress=gr.Progress()):
    """Saves uploaded PDF, manages assets, and triggers embeddings."""
    if config.ChromaDB is None or config.embedding_function is None:
        gr.Warning("Please set your API Key first using the 'Set API Key & Initialize' button before uploading documents.")
        return None

    print(f"Handling file changes in session: {config.session}")

    progress(0, desc="Starting file processing...")

    files_to_delete = []
    files_to_add = []
    current_filenames_on_upload = set()

    if pdf_files:
        current_filenames_on_upload = set(os.path.basename(pdf_file.name) for pdf_file in pdf_files)

    files_to_delete = list(config.filesinput - current_filenames_on_upload)
    if files_to_delete:
        progress(0.1, desc=f"Deleting {len(files_to_delete)} files...")
        for filename in files_to_delete:
            print(f"Processing deletion for: {filename}")
            try:
                config.ChromaDB.deleteEmbeddings(filename)
                asset_path = os.path.join(f'{str(config.session)}/assets', filename)
                if os.path.exists(asset_path):
                    os.remove(asset_path)
                    print(f"Deleted asset file: {asset_path}")
                config.filesinput.remove(filename)
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")
        config.ChromaDB.observeDB()
        print(f"Finished deleting {len(files_to_delete)} files: {files_to_delete}")

    if pdf_files:
        newly_uploaded_files = [f for f in pdf_files if os.path.basename(f.name) not in config.filesinput]
        if newly_uploaded_files:
            progress(0.5, desc=f"Adding {len(newly_uploaded_files)} new files...")
            for i, pdf_file in enumerate(newly_uploaded_files):
                base_name = os.path.basename(pdf_file.name)
                progress(0.5 + (0.4 * (i / len(newly_uploaded_files))), desc=f"Copying {base_name}...")
                print(f"Processing addition for: {base_name}")
                try:
                    dest_path = os.path.join(f'{str(config.session)}/assets', base_name)
                    shutil.copy(pdf_file.name, dest_path)
                    files_to_add.append(base_name) 
                    config.filesinput.add(base_name)
                except Exception as e:
                    print(f"Error copying file {base_name}: {e}")

    if files_to_add:
        print(f"Saved {len(files_to_add)} new files: {files_to_add}. Triggering embedding...")
        progress(0.9, desc=f"Embedding {len(files_to_add)} documents...")
        try:
            embedDocument(files_to_add)
            progress(1.0, desc="File processing complete.")
        except Exception as e:
            print(f"Error during embedding process: {e}")
            progress(1.0, desc="File processing completed with embedding errors.")
    elif files_to_delete:
        progress(1.0, desc="File deletion complete.")
    else:
        progress(1.0, desc="No file changes detected.")

    return pdf_files


def chat(query, history):
    history.append({"role": "user", "content": query})

    if config.chat_client is None:
        history.append({"role": "assistant", "content": "Error: Chat client not initialized. Please set your API Key first."})
        yield history[-1]
        return history

    prompt_input = creatingQuery(query)

    if "Error:" in prompt_input or "Document context is unavailable" in prompt_input:
         print(f"Warning/Error from creatingQuery: {prompt_input}. Proceeding without document context.")
         prompt_input = f"Please answer this question: {query}"


    model_output = ""
    try:
        stream = config.chat_client.models.generate_content_stream(
            model='gemini-2.0-flash-001', 
            contents=[prompt_input])
        for chunk in stream:
             if hasattr(chunk, 'text'):
                 model_output += chunk.text
                 if history[-1]["role"] == "assistant":
                      history[-1]["content"] = model_output
                 else:
                      history.append({"role": "assistant", "content": model_output})
                 yield history[-1]
             else:
                  print(f"Received non-text chunk: {chunk}")

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        error_message = f"Sorry, an error occurred while contacting the language model: {e}"
        if history[-1]["role"] == "assistant":
            history[-1]["content"] = error_message
        else:
            history.append({"role": "assistant", "content": error_message})
        yield history[-1]
    return history


if __name__ == "__main__":
    config.filesinput = set()
    current_time = str(time.time())
    hashed_time = hashlib.md5(current_time.encode()).hexdigest()
    config.session = str(hashed_time)
    os.makedirs(str(config.session), exist_ok=True)
    os.makedirs(f'{str(config.session)}/assets', exist_ok=True)
    os.makedirs(f'{str(config.session)}/vectorData/', exist_ok=True)
    print(f"Session started: {config.session}")

    with gr.Blocks(theme=dark) as demo:
        gr.Markdown("# Document Summarizer")
        init_status = gr.Markdown("")

        with gr.Row():
            with gr.Column(scale=2):
                 chatbot = gr.Chatbot(label="Chat", bubble_full_width=False)
                 msg = gr.Textbox(label="Your Question", placeholder="Ask about the documents or anything else...")
                 clear = gr.ClearButton([msg, chatbot])

            with gr.Column(scale=1):
                with gr.Row():
                    api_key_input = gr.Textbox(
                        label="Google AI API Key",
                        placeholder="Enter your API key here",
                        scale=3)
                    init_button = gr.Button("Set API Key", scale=1)

                docs_input = gr.Files(
                    label="Upload PDF Documents",
                    file_types=[".pdf"],
                    file_count="multiple")

        init_button.click(
            fn=initialize_clients,
            inputs=[api_key_input],
            outputs=[init_status]).then(lambda: None, None, None)

        docs_input.upload(
            fn=saveDocument,
            inputs=[docs_input],
            outputs=[docs_input]
        )
        # Handle file clearing/removal as well if needed (e.g., docs_input.change if behavior differs)
        docs_input.change( # 'change' might cover deletions better
             fn=saveDocument,
             inputs=[docs_input],
             outputs=[docs_input] # Update the displayed list
        )

        # Chat submission logic using Chatbot component style
        def user(user_message, history):
            return "", history + [[user_message, None]]

        def bot(history):
             user_query = history[-1][0]
             # Call the modified chat function which yields responses
             response_stream = chat(user_query, []) # Pass empty history to chat func internally? Or structure differently?
                                                    # Let's rethink how chat expects history.
                                                    # The `chat` function expects role dicts.

             # Convert Gradio history (list of lists) to role dict format for chat function
             role_history = []
             for human, ai in history[:-1]: # Exclude the latest user query already appended internally
                 if human: role_history.append({"role": "user", "content": human})
                 if ai: role_history.append({"role": "assistant", "content": ai})

             # Append the latest user query correctly
             role_history.append({"role": "user", "content": user_query})

             # Stream the response using the generator
             history[-1][1] = "" # Initialize assistant response in Gradio history
             for update in chat(user_query, role_history): # Call chat with correct history format
                 # Update the last element in the Gradio history
                 # The 'chat' function yields the full assistant message progressively
                 history[-1][1] = update['content']
                 yield history


        msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot, chatbot, chatbot
        )
        clear.click(lambda: None, None, chatbot, queue=False)

    demo.queue().launch(debug=True)