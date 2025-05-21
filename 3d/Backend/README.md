# Backend for EHR File Processing

This backend uses Flask and the OpenAI API to process files uploaded from the frontend.

## Setup

1.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the `3d/Backend` directory with your OpenAI API key:
    ```
    OPENAI_API_KEY=your_openai_api_key_here
    ```

4.  **Run the Flask application:**
    ```bash
    flask run
    ```

    The backend will typically run on `http://127.0.0.1:5000`. You can change the port in `app.py` if needed (currently set to 5001). 