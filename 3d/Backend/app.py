import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv() 

app = Flask(__name__)

# Configure CORS to allow your frontend domains
if os.environ.get('FLASK_ENV') == 'production':
    # Production CORS - replace with your actual Vercel domain
    CORS(app, origins=[
        "https://demodemodemo-two.vercel.app",
        "https://demodemodemo-two.vercel.app/ehr"
    ])
else:
    # Development CORS - allow localhost
    CORS(app, origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001"
    ])

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# --- Helper to manage Assistant --- 
ASSISTANT_ID_FILE = "assistant_id.txt"
assistant_cache = None  # Cache the assistant to avoid recreating it

def get_or_create_assistant():
    global assistant_cache
    
    # Return cached assistant if we have one
    if assistant_cache is not None:
        return assistant_cache
    
    if os.path.exists(ASSISTANT_ID_FILE):
        with open(ASSISTANT_ID_FILE, "r") as f:
            assistant_id = f.read().strip()
            if assistant_id:
                try:
                    print(f"Attempting to retrieve assistant with ID: {assistant_id}")
                    assistant = client.beta.assistants.retrieve(assistant_id)
                    print(f"Successfully retrieved assistant: {assistant.id}")
                    assistant_cache = assistant  # Cache it
                    return assistant
                except Exception as e:
                    print(f"Failed to retrieve assistant {assistant_id}, creating a new one: {e}")
            else:
                print("Assistant ID file is empty, creating a new assistant.")
    else:
        print("Assistant ID file not found, creating a new assistant.")
    
    try:
        assistant = client.beta.assistants.create(
            name="EHR File Processor",
            instructions="You are an AI assistant that processes Electronic Health Record (EHR) files. Analyze the content and provide a summary or answer questions based on the file.",
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )
        with open(ASSISTANT_ID_FILE, "w") as f:
            f.write(assistant.id)
        print(f"Created new assistant with ID: {assistant.id} and saved to {ASSISTANT_ID_FILE}")
        assistant_cache = assistant  # Cache it
        return assistant
    except Exception as e:
        print(f"Error creating OpenAI assistant: {e}")
        raise e

# Don't create assistant on startup - wait until it's needed!

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "EHR File Processor API is running"})

@app.route("/api/process-file", methods=["POST"])
def process_file():
    try:
        assistant = get_or_create_assistant()  # Get assistant when needed
    except Exception as e:
        return jsonify({"error": f"Failed to initialize AI assistant: {str(e)}"}), 500
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        try:
            print(f"Processing file: {file.filename}")
            file_content = file.read() # Read file content
            file.seek(0) # Reset stream position if needed later, though not strictly for OpenAI upload here

            # Step 1: Create a Vector Store
            # Vector stores have a default expiration policy of 7 days if created via thread helpers.
            # Here, we create it explicitly and can manage its lifecycle.
            vector_store = client.vector_stores.create(
                name=f"EHR Upload - {file.filename} - {time.time()}", # Unique name
                # expires_after={"anchor": "last_active_at", "days": 1} # Optional: manage expiration
            )
            print(f"Created vector store: {vector_store.id} for file {file.filename}")

            # Step 2: Upload the file and add it to the Vector Store
            file_batch = client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=[(file.filename, file_content)] 
            )
            print(f"File batch status for vector store {vector_store.id}: {file_batch.status}")
            if file_batch.status != 'completed':
                error_message = "File processing batch failed."
                if hasattr(file_batch, 'last_error') and file_batch.last_error:
                    error_message = f"File processing failed: {file_batch.last_error.message if hasattr(file_batch.last_error, 'message') else file_batch.last_error}"
                client.vector_stores.delete(vector_store.id) # Clean up failed vector store
                print(f"Deleted vector store {vector_store.id} due to batch failure.")
                return jsonify({"error": error_message}), 500

            # Step 3: Update the assistant to use this new Vector Store
            # IMPORTANT: An assistant can only be linked to ONE vector store via tool_resources.file_search.vector_store_ids[0]
            # If you need to query multiple permanent stores, this strategy needs adjustment.
            # For this single-file-query use case, replacing it is fine.
            assistant = client.beta.assistants.update(
                assistant_id=assistant.id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
            print(f"Updated assistant {assistant.id} to use vector store {vector_store.id}")

            # Step 4: Create a Thread
            thread_message_content = "Please summarize the key information in the provided EHR document. Focus on diagnosis, medications, and chief complaints."
            thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": thread_message_content,
                    }
                ]
            )
            print(f"Created thread: {thread.id} with initial message: '{thread_message_content}'")

            # Step 5: Create a Run and poll for completion
            print(f"Creating run on thread {thread.id} with assistant {assistant.id}")
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )
            print(f"Run {run.id} status: {run.status}")

            if run.status == 'completed':
                messages = client.beta.threads.messages.list(
                    thread_id=thread.id, order="asc"
                )
                assistant_response = None
                for msg in reversed(messages.data):
                    if msg.role == "assistant":
                        # Ensure content is not empty and is of expected type
                        if msg.content and isinstance(msg.content, list) and len(msg.content) > 0:
                            content_item = msg.content[0]
                            if hasattr(content_item, 'text') and hasattr(content_item.text, 'value'):
                                assistant_response = content_item.text.value
                                break
                
                if assistant_response:
                    print(f"Assistant response: {assistant_response[:200]}...") # Log snippet
                    # Clean up the specific vector store created for this request
                    try:
                        client.vector_stores.delete(vector_store.id)
                        print(f"Successfully deleted vector store: {vector_store.id}")
                    except Exception as e_del_vs:
                        print(f"Error deleting vector store {vector_store.id}: {e_del_vs}")
                    return jsonify({"response": assistant_response})
                else:
                    print("Assistant did not provide a text response.")
                    return jsonify({"error": "Assistant did not provide a text response."}), 500
            else:
                print(f"Run did not complete successfully. Status: {run.status}, Error: {run.last_error}")
                error_detail = f"Run failed or was cancelled. Status: {run.status}"
                if run.last_error and hasattr(run.last_error, 'message'):
                    error_detail += f" - {run.last_error.message}"
                return jsonify({"error": error_detail}), 500

        except Exception as e:
            print(f"Unhandled error processing file: {e}")
            # Attempt to clean up vector store if it was created and an error occurred later
            if 'vector_store' in locals() and vector_store and vector_store.id:
                try:
                    client.vector_stores.delete(vector_store.id)
                    print(f"Cleaned up vector store {vector_store.id} due to error: {e}")
                except Exception as e_cleanup:
                    print(f"Error during cleanup of vector store {vector_store.id}: {e_cleanup}")
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "File processing failed due to an unknown issue"}), 500

if __name__ == "__main__":
    # Production ready configuration
    port = int(os.environ.get("PORT", 5001))  # Use PORT from environment if available
    app.run(host='0.0.0.0', debug=False, port=port) 