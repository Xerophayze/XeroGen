import modules.scripts as scripts
import gradio as gr
import os
import csv
import requests
import time
import uuid
from datetime import datetime
from modules.scripts import basedir
from modules.txt2img import txt2img
from modules import script_callbacks, sd_samplers
import modules.scripts
from modules import extensions
from modules import generation_parameters_copypaste as params_copypaste
from modules.paths_internal import extensions_dir

# Global variable to store chat sessions
chat_sessions = {}

# Define the directory where you want to save the CSV files
CSV_DIR = os.path.join("extensions", "XeroGen", "Scripts")

# Ensure the directory exists, if not, create it
if not os.path.exists(CSV_DIR):
    os.makedirs(CSV_DIR)

# Paths to the CSV files
CSV_FILE = os.path.join(CSV_DIR, "chatgpt_responses.csv")
PROMPT_CSV = os.path.join(CSV_DIR, "prompts.csv")
API_KEYS_CSV = os.path.join(CSV_DIR, "api_keys.csv")

recent_outputs = {}
chat_sessions = {}  # Dictionary to store ongoing chat sessions by prompt title

def get_self_extension():
    if '__file__' in globals():
        filepath = __file__
    else:
        import inspect
        filepath = inspect.getfile(lambda: None)
    for ext in extensions.active():
        if ext.path in filepath:
            return ext

def check_and_create_csv_files():
    # List of CSV files and their headers
    csv_files = {
        CSV_FILE: ["Date Generated", "User Message", "Response"],
        PROMPT_CSV: ["Title", "Prompt"],
        API_KEYS_CSV: ["Title", "Key"]
    }
    
    print("Checking and creating CSV files...")  # Debug print statement
    
    for file, headers in csv_files.items():
        abs_file_path = os.path.abspath(file)  # Get absolute path
        if not os.path.exists(abs_file_path):
            try:
                with open(abs_file_path, 'w', newline='', encoding='utf-8') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(headers)
                print(f"Created {abs_file_path}")  # Debug print statement with absolute path
            except Exception as e:
                print(f"Error creating {abs_file_path}: {e}")  # Print any error that occurs
        else:
            print(f"{abs_file_path} already exists.")  # Debug print statement with absolute path

def read_prompts_from_csv():
    prompts = {}
    with open(PROMPT_CSV, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            title, prompt = row
            prompts[title] = prompt
    return prompts

check_and_create_csv_files()
PROMPTS_DICT = read_prompts_from_csv()

def read_api_keys_from_csv():
    api_keys = {}
    with open(API_KEYS_CSV, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            title, key = row
            api_keys[title] = key
    return api_keys

def save_new_api_key_to_csv(title, api_key):
    with open(API_KEYS_CSV, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([title, api_key])

def fetch_models(api_key):
    response = requests.get(
        "https://api.openai.com/v1/engines",
        headers={
            "Authorization": f"Bearer {api_key}"
        }
    )
    data = response.json()
    if 'data' in data:
        models = [engine['id'] for engine in data['data']]
        return models
    else:
        return []

def save_to_csv(user_message):
    global recent_outputs
    if recent_outputs:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mode = 'a' if os.path.exists(CSV_FILE) else 'w'
        with open(CSV_FILE, mode, newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if mode == 'w':
                writer.writerow(["Date Generated", "User Message", "Response"])
            for output in recent_outputs:
                writer.writerow([timestamp, user_message, output])
        recent_outputs.clear()

def chat_with_gpt(api_key_title, title, message, model="gpt-3.5-turbo", num_requests=1, save_responses=False, label=False, style=False, trend=False):
    global recent_outputs
 
    API_KEYS = read_api_keys_from_csv()
    api_key = API_KEYS[api_key_title]

    # Start a new chat session
    user_prompt = PROMPTS_DICT[title]
    formatted_history = [{"role": "system", "content": user_prompt}]

    # Send the user-selected prompt to ChatGPT and print the response to the console
    prompt_response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": formatted_history
        }
    )
    print(prompt_response.json())  # Printing the response to the console

    # Introduce a 2-second delay
    time.sleep(2)
    
    # Now, send the user's message
    modified_message = message
    if style:
        modified_message = "$style, " + modified_message
    if num_requests > 1:
        modified_message = f"{num_requests} prompts, " + modified_message
    if label:
        modified_message = "$label, " + modified_message
    if trend:
        modified_message += ", $trend"
    
    formatted_history.append({"role": "user", "content": modified_message})

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": formatted_history
        }
    )

    response_data = response.json()
    if 'choices' in response_data:
        all_responses = [response_data['choices'][0]['message']['content'].strip()]
    else:
        return f"Error: {response_data.get('error', 'Unknown error.')}"
    
    recent_outputs = all_responses.copy()
    if save_responses:
        save_to_csv(modified_message)
    return "\n---\n".join(all_responses)

def on_ui_tabs():
    ext = get_self_extension()
    if ext is None:
        return []
    js_ = [f'{x.path}?{os.path.getmtime(x.path)}' for x in ext.list_files('js', '.js')]
    js_.insert(0, ext.path)

    api_keys = read_api_keys_from_csv().values()
    if not api_keys:
        models = []  
    else:
        first_api_key = next(iter(api_keys))
        models = fetch_models(first_api_key)

    with gr.Blocks(analytics_enabled=False) as XeroGen_interface:
        # Program Information at the top
        with gr.Row():
            # New column for 'Title', 'Content', and checkboxes
            with gr.Column(variant='panel'):
                title_input = gr.components.Textbox(label="Title")
                content_input = gr.components.Textbox(label="Content")
                new_api_key_checkbox = gr.components.Checkbox(label="New API Key")
                new_seed_prompt_checkbox = gr.components.Checkbox(label="New Seed Prompt")
                add_button = gr.Button(value='Add', variant='primary')

                # Function to handle the add button's logic
                def handle_add(title, content, new_api_key, new_seed_prompt):
                    if new_api_key:
                        # Save to API_KEYS_CSV and update the in-memory dictionary
                        save_new_api_key_to_csv(title, content)
                        API_KEY_TITLES.append(title)
                    if new_seed_prompt:
                        # Save to PROMPT_CSV and update the in-memory dictionary
                        with open(PROMPT_CSV, 'a', newline='', encoding='utf-8') as file:
                            writer = csv.writer(file)
                            writer.writerow([title, content])
                        PROMPTS_DICT[title] = content

                add_button.click(fn=handle_add, 
                                 inputs=[title_input, content_input, new_api_key_checkbox, new_seed_prompt_checkbox])

            # Column for the Text Content
            with gr.Column():
                gr.Markdown("""
                <left>
                <h3>XeroGen Interface</h3>
                <p>Thank you for using my Extension.  To get started you will need to enter a title and api key and select the check box for New API key, then click Add.  Then go to extensions or settings and reload the UI.  This will give this extension a chance to get a list of the available models to select from.</p>
                <p>While this interface should work with other GPT prompt generators, it has been primarially designed with my prompt generator I've meticulously crafted over the last several months.</p>
                <p>You can purchase my Prompt Generator at my shop along with other tools. <a href="https://shop.xerophayze.com" target="_blank">Archane Shadows</a>.</p>
                <p>For tutorials, updates, and more, visit my Youtube channel <a href="https://video.xerophayze.com" target="_blank">Alchemy with Xerophayze</a>.</p>
                </center>
                """)

        # Divide the remaining space into two columns
        with gr.Row().style(equal_height=False):
            # Left column for inputs (removed the 'New API Key' fields)
            with gr.Column(variant='panel'):
                API_KEY_TITLES = list(read_api_keys_from_csv().keys())
                api_key_title_input = gr.components.Dropdown(choices=API_KEY_TITLES, label="API Key Selection")
                prompt_title_input = gr.components.Dropdown(choices=list(PROMPTS_DICT.keys()), label="Your Prompt")
                message_input = gr.components.Textbox(label="Your Message")
                model_input = gr.components.Dropdown(choices=models, label="Model Selection - Use gpt-3.5-turbo for 5 or less prompts. Use gpt-3.5-turbo-16k for requests of more than 5 prompts.")
                num_requests_input = gr.components.Slider(minimum=1, maximum=10, step=1, label="Number of Prompts -")
                save_responses_input = gr.components.Checkbox(label="Save Responses")
                label_input = gr.components.Checkbox(label="Label")
                style_input = gr.components.Checkbox(label="Style")
                trend_input = gr.components.Checkbox(label="Trend")
                
            # Right column to display the submit button and the output window
            with gr.Column(variant='panel'):
                submit_button = gr.Button(value='Submit', elem_id="xerogen_submit", variant='primary')
                
                chat_response_output = gr.components.Textbox(label="ChatGPT Responses", type="text")
                
                # Link the Submit button to the chat_with_gpt function
                submit_button.click(fn=chat_with_gpt,
                                    inputs=[api_key_title_input, prompt_title_input, 
                                            message_input, model_input, num_requests_input, save_responses_input, label_input, 
                                            style_input, trend_input],
                                    outputs=chat_response_output)

    return [(XeroGen_interface, 'XeroGen', 'XeroGen_interface')]



script_callbacks.on_ui_tabs(on_ui_tabs)
