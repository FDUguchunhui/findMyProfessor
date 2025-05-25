from functools import partial
import chromadb
import gradio as gr
from huggingface_hub import snapshot_download
import os
from src.faculty_advisor import gpt_4o_mini_rag

# Step 1: Download Chroma DB from HF Hub
local_repo_path = snapshot_download(
    repo_id="dawnlaker/UTH_faculty",  # <- change this
    repo_type="dataset",
    local_dir="hf_repo", 
    token=os.getenv('HF_TOKEN'),
    allow_patterns="faculties_vectorstore/**"
)

# Step 2: Load the Chroma DB

persist_path = os.path.join(local_repo_path, "faculties_vectorstore")
client = chromadb.PersistentClient(path=persist_path)
collection = client.get_or_create_collection('faculties')# <- change this



import gradio as gr
MODEL = "gpt-4o-mini"

chat = partial(gpt_4o_mini_rag, collection=collection)

gr.ChatInterface(fn=chat, 
                  title="Faculty Advisor Chat",
                    description="Ask about faculty members and their expertise",
                    theme='soft',
                    examples=[
                        "I am looking for a faculty member who is an expert in epidemiology",
                        "Can you recommend someone who works on clinical trials?",
                        "Who specializes in machine learning?"
    ]).launch(share=True)
