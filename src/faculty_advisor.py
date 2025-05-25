import os
from tqdm import tqdm
from dotenv import load_dotenv
import chromadb
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings

# Initialize environment variables
load_dotenv(override=True)
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', 'your-key-if-not-using-env')

# Initialize OpenAI client
openai = OpenAI()

# Initialize vectorizer
vectorizer = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=os.getenv('OPENAI_API_KEY')
)


def find_similars(collection, description):
    """
    Find similar faculty members based on the given description.
    
    Args:
        collection: The ChromaDB collection to search in
        description (str): The description to search for similar faculty members
        
    Returns:
        tuple: (documents, names, links) containing the similar faculty members' information
    """
    results = collection.query(
        query_embeddings=vectorizer.embed_query(description),
        n_results=10
    )
    documents = results['documents'][0][:]
    name = [m['name'] for m in results['metadatas'][0][:]]
    link = [m['url'] for m in results['metadatas'][0][:]]
    return documents, name, link

def make_context(similars):
    """
    Create a context string from similar faculty members.
    
    Args:
        similars (tuple): The output from find_similars function
        
    Returns:
        str: Formatted context string
    """
    message = "To provide some context, here are some faculty members that might be relevant to your description.\n\n"
    documents, names, links = similars
    for similar, name, link in zip(documents, names, links):
        message += f'''Potentially related faculty:
{name}

        website: {link}

        {similar}\n\n'''
    return message

def messages_for(description, similars):
    """
    Create a message object for the OpenAI API.
    
    Args:
        description (str): The user's description
        similars (tuple): The output from find_similars function
        
    Returns:
        dict: Message object for OpenAI API
    """
    user_prompt = f"Here is my description: {description}\n\n"
    user_prompt += make_context(similars)
    return {"role": "user", "content": user_prompt}

def gpt_4o_mini_rag(description, history, collection):
    """
    Generate a response using GPT-4o-mini model with RAG.
    
    Args:
        description (str): The user's description
        history (list): Chat history as list of tuples (user_message, assistant_message)
        collection: The ChromaDB collection to search in
        
    Yields:
        str: Generated response chunks
    """
    system_message = {
        "role": "system",
        "content": "You are a academic advisor. You estimate the relevance of faculty members to a given description. Suggest relevant faculty members. Don't forget to include a link to the faculty member's profile. You should give explanation for your choice in markdown format."
    }
    
    # Format chat history into proper message format
    formatted_history = []
    for user_msg, assistant_msg in history:
        formatted_history.append({"role": "user", "content": user_msg})
        formatted_history.append({"role": "assistant", "content": assistant_msg})
    
    similars = find_similars(collection=collection, description=description)
    current_message = messages_for(description, similars)
    
    # Combine all messages in the correct order
    messages = [system_message] + formatted_history + [current_message]
    
    stream = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        seed=42,
        stream=True
    )
    
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        yield response
