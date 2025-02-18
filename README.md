
# Streamlit App with Ollama

This repository provides a guide to set up and run a Streamlit application that integrates **Ollama** for Large Language Model (LLM)-based tasks. The application leverages Ollama's models like Llama 3.1 and Mistral to perform various LLM tasks.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or later**
- **pip** (Python package manager)

## Installation Steps

Follow the steps below to get the app up and running:

### 1. Install Ollama

Ollama is required to run large language models. Install Ollama by running the following command:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Alternatively, visit the [Ollama website](https://ollama.com) for platform-specific installation instructions.

### 2. Pull the Required Ollama Models

Pull the necessary LLM models such as Llama 3.1 and Mistral:

```bash
ollama pull llama3.1
ollama pull mistral
ollama run deepseek-r1
```

This ensures that the models are downloaded and ready for use in the application.

### 3. Install Python Dependencies

Navigate to the project directory and install the required Python dependencies by running:

```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit App

After installing the dependencies, run the Streamlit app with the following command:

```bash
python3 -m streamlit run main_app.py
```

This will start the web app, which can be accessed in your browser at [http://localhost:8501/](http://localhost:8501/).

## Troubleshooting

If you encounter issues during setup, try the following steps:

- **Missing dependencies**: Upgrade your `pip`, `setuptools`, and `wheel`, and then reinstall the dependencies:

  ```bash
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  ```

- **Ollama not running**: Make sure Ollama is running by executing:

  ```bash
  ollama list
  ```

  If no models appear, try re-pulling them:

  ```bash
  ollama pull llama3
  ollama pull mistral
  ```

- **Streamlit app fails to launch**: Check the Streamlit logs for error details and ensure all dependencies are installed correctly.

## Contributing

We welcome contributions to improve or extend the app. If you have ideas for improvements, please feel free to submit an issue or a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.