# Here is a testing repo, playground repo

# C Code Scanner

This project provides a Python script to scan C source code for potential bugs and memory inefficiencies using AI models.

## 1. User Manual

To use the script, you need to have Python installed. You also need to set the `GOOGLE_API_KEY` or `OPENAI_API_KEY` environment variable with your API key.

1.  Install the required Python libraries:

    ```bash
    pip install google-generativeai openai
    ```

2.  Run the script:

    ```bash
    python c_code_scanner.py --model gemini|openai <c_code_file> <prompt_file> <output_csv_file>
    ```

    *   `<c_code_file>`: Path to the C source code file (default: defective.c).
    *   `<prompt_file>`: Path to the prompt file (default: prompt.txt).
    *   `<output_csv_file>`: Path to the output CSV file (default: output.csv).
    *   `--model`: Choose the AI model to use (gemini or openai). Default is gemini.

    Example:

    ```bash
    python c_code_scanner.py --model gemini defective.c prompt.txt output.csv
    ```

## 2. Code Architecture

The project consists of the following main components:

*   `c_code_scanner.py`: The main Python script that performs the C code scanning.
*   `AIModel`: Abstract base class for AI models.
*   `GeminiAIModel`: Concrete class for the Gemini AI model.
*   `OpenAIModel`: Concrete class for the OpenAI model.
*   `get_ai_response`: Function to get the AI response for a given C code line and prompt.
*   `scan_c_code`: Function to scan the C code and generate the CSV output.

## 3. File and Folder Description

*   `c_code_scanner.py`: Contains the main Python script.
*   `defective.c`: Contains example defective C code.
*   `prompt.txt`: Contains the prompt for the AI model.
*   `output.csv`: Contains the output of the C code scan in CSV format.
*   `README.md`: This file.

## 4. Copyright Apache 2

Copyright 2025 [Your Name]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
