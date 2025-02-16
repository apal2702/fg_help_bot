Streamlit App with Ollama

This guide will help you set up and run a Streamlit app that utilizes Ollama for LLM-based tasks. Follow the steps below to install dependencies and launch the app.

Prerequisites

Ensure you have the following installed:

Python 3.8 or later

pip (Python package manager)

Installation Steps

1. Install Ollama

Ollama is required to run large language models. Install it using the following command:

curl -fsSL https://ollama.com/install.sh | sh

Alternatively, you can visit Ollama's official website for installation instructions based on your operating system.

2. Pull Required Ollama Models

Pull the necessary LLM models like Llama 3.1 and Mistral:

ollama pull llama3
ollama pull mistral

This ensures that the models are downloaded and ready for use in the application.

3. Install Python Dependencies

Navigate to the project directory and install the required Python packages:

pip install -r requirements.txt

4. Run the Streamlit App

Once the dependencies are installed, start the Streamlit app using:

python3 -m streamlit run app/fg_bot_app.py

This will launch the web app, which can be accessed in your browser at http://localhost:8501/.

Troubleshooting

If you encounter missing dependencies, try running:

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

Ensure that Ollama is running by executing:

ollama list

If no models appear, try re-pulling them.

If the app fails to launch, check the Streamlit logs for errors and verify that all dependencies are correctly installed.

Contributing

Feel free to submit issues or pull requests if you improve or extend the app.

License

This project is licensed under the MIT License.

