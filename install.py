import csv
import os

def create_csv_file(filename, headers):
    # Define the directory path
    dir_path = "Scripts"
    
    # Check if directory exists, if not create it
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    # Modify the filename to include the directory
    full_path = os.path.join(dir_path, filename)
    
    if not os.path.exists(full_path):
        with open(full_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

def main():
    create_csv_file("api_keys.csv", ["Title", "API Key"])
    create_csv_file("chatgpt_responses.csv", ["Date Generated", "User Message", "Response"])
    create_csv_file("prompts.csv", ["Title", "Prompt"])

if __name__ == "__main__":
    main()
