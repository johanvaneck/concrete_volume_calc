from flask import Flask, request, render_template, redirect, url_for
import os
import requests
import io # To handle in-memory file operations
from google import genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY is None:
    raise ValueError("GOOGLE_API_KEY environment variable is not set.")

client = genai.Client(api_key=GOOGLE_API_KEY)


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads' # Define a folder to save uploaded PDFs temporarily
# Ensure the UPLOAD_FOLDER exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    """
    Renders the index.html file, which contains the PDF prompt upload form.
    """
    # In a real application, ensure 'index.html' is in a 'templates' directory.
    # For this example, we'll assume it's set up to be rendered.
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles the POST request from the form submission.
    It processes the uploaded PDF file, extracts text, combines it with the user's prompt,
    sends it to the Gemini API, and returns the Gemini response.
    """
    pdf_file_path = None # Initialize to None for cleanup in finally block

    try:
        # Check if 'pdfFile' is in the request files
        if 'pdfFile' not in request.files:
            return 'No PDF file part in the request.', 400

        # Check if 'promptText' is in the request form data
        if 'promptText' not in request.form:
            return 'No prompt text part in the request.', 400

        pdf_file = request.files['pdfFile']
        user_prompt_text = request.form['promptText']

        # Check if a file was actually selected
        if pdf_file.filename == '' or pdf_file.filename is None:
            return 'No selected PDF file.', 400

        # Check if the file is a PDF
        if not pdf_file.filename.lower().endswith('.pdf'):
            return 'Invalid file type. Only PDF files are allowed.', 400

        # Temporarily save the PDF file to disk for extraction
        # This is a common approach, though in-memory processing is also possible with pdfminer
        pdf_file_path = os.path.join(UPLOAD_FOLDER, "test.pdf")
        pdf_file.save(pdf_file_path)

        context = """
        Analyze the structure in the attached PDF file.

        Write a report where you calculate the volume of concrete that would be needed to build the structure.

        Give a final result in cubic meters.

        Use the SANS codes for this problem.

        Format the response output as html.
        """

        myfile = client.files.upload(file=UPLOAD_FOLDER+"/test.pdf")


        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=["Describe this audio clip. " + context + "\n\nUser text:" + user_prompt_text, myfile]
        )

        gemini_response_text = response.text

        return f'<h3>Gemini API Response:</h3><p>{gemini_response_text}</p>'

    except requests.exceptions.RequestException as e:
        print(f"Network or API error: {e}")
        return f"Error connecting to Gemini API: {e}", 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"An internal server error occurred: {e}", 500
    finally:
        # Clean up: remove the temporarily saved PDF file
        if pdf_file_path and os.path.exists(pdf_file_path):
            os.remove(pdf_file_path)
            print(f"Cleaned up temporary PDF file: {pdf_file_path}")


if __name__ == '__main__':
    # Run the Flask application in debug mode for development.
    # In a production environment, set debug=False.
    app.run(debug=True)
