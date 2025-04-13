# Document-Summarizer v1.2

**Goal**: It is simple, upload your document in PDF format (will work on changing this later) and then query it. Get a summary of any number of words, or get detailed understanding of only a portion of the document.

**How does it work**: Well, the interface is built using Gradio, a really lightweight and customizable tool. The model that generates the answer to queries is Google's 'gemini-2.0-flash-001' model. Access repo here - [Google GenAI](https://github.com/googleapis/python-genai)

> **Note**: You would need an API key to run this successfully. This can be done from your Google Cloud account.

![Application page](interface.png "Application page")

# **Installation**  

1. Cloning the repository first.

```sh 
git clone https://github.com/AmishKakka/Document-Summarizer.git
```

2. Then, consider building a virtual environment so that there are no conflicts for the library versions.
```sh
python3 -m venv env_name
source env_name/bin/activate
pip install -r requirements.txt
```

3. Run main.py to access the application in your browser. 
```sh
python3 main.py
```

# **Pointers** 
1. The idea is to implement Retreival-Augmented Generation (RAG) and the power of LLMs to generate relevant text.
2. To store the embeddings of the documents, ChromaDB is used and accessed using the LangChain library.
3. You can upload only mutiple documents at a time and query any document.