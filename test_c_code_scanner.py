import unittest
import os
import csv
import google.generativeai as genai
from c_code_scanner import scan_c_code, generate_csv  # Import the functions from your script

class TestCCodeScanner(unittest.TestCase):

    def setUp(self):
        # Create a dummy C file for testing
        self.c_file_path = "test_example.c"
        with open(self.c_file_path, "w") as f:
            f.write("#include <stdio.h>\n")
            f.write("#include <stdlib.h>\n")
            f.write("#include <string.h>\n")
            f.write("\n")
            f.write("int main() {\n")
            f.write("    char *str = (char *)malloc(100);\n")
            f.write("    strcpy(str, \"This is a test string\");\n")
            f.write("    printf(\"%s\\n\", str);\n")
            f.write("    return 0;\n")
            f.write("}\n")

        self.api_key = "YOUR_GOOGLE_AI_API_KEY"  # Replace with your actual Google AI API key
        self.csv_file_path = "test_c_code_issues.csv"

    def tearDown(self):
        # Remove the dummy C file and CSV file after testing
        os.remove(self.c_file_path)
        if os.path.exists(self.csv_file_path):
            os.remove(self.csv_file_path)

    def test_scan_c_code(self):
        # Test the scan_c_code function
        issues = scan_c_code(self.c_file_path, self.api_key)
        self.assertIsInstance(issues, list)
        # Add more assertions based on the expected behavior of your scan_c_code function

    def test_generate_csv(self):
        # Test the generate_csv function
        issues = [
            {"line_number": 5, "code": "char *str = (char *)malloc(100);", "reason": "Potential memory leak: 'malloc' call without corresponding 'free'"},
            {"line_number": 6, "code": "strcpy(str, \"This is a test string\");", "reason": "Potential buffer overflow: Use 'strncpy' instead of 'strcpy'"}
        ]
        generate_csv(issues, self.csv_file_path)
        self.assertTrue(os.path.exists(self.csv_file_path))

        # Read the CSV file and check its contents
        with open(self.csv_file_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            header = next(csv_reader)
            self.assertEqual(header, ["Line Number", "Original Code", "Reason"])
            data = list(csv_reader)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0], ["5", "char *str = (char *)malloc(100);", "Potential memory leak: 'malloc' call without corresponding 'free'"])
            self.assertEqual(data[1], ["6", "strcpy(str, \"This is a test string\");", "Potential buffer overflow: Use 'strncpy' instead of 'strcpy'"])

if __name__ == '__main__':
    unittest.main()
