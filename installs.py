# installs.py

import csv
import os

def create_csv_file(filename, headers):
    if not os.path.exists(filename):
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

def main():
    create_csv_file("api_keys.csv", ["Title", "API Key"])
    create_csv_file("chatgpt_responses.csv", ["Date Generated", "User Message", "Response"])
    create_csv_file("prompts.csv", ["Title", "Prompt"])

if __name__ == "__main__":
    main()
