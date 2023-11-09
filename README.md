# XeroGen
This project aims to bring a more stable and user friendly Chat GPT interface designed to allow others to implement their own GPT prompt generators if they want. It is primarily designed to work with the ultimate stable diffusion prompt generator created by Xerophayze.  You can purchase Xerophayze's prompt generator at https://shop.xerophayze.com and you can see it in action on my youtube channel https://youtu.be/NiGqp5FyXQY

XeroGen Interface README
Introduction
Welcome to the XeroGen Interface! Designed and programmed by Xerophayze, this tool was built with the assistance of the ChatGPT code interpreter. As this is the first version, please understand that it's a work in progress and will undergo refinements over time.

Initial Setup
After installing the extension and restarting the UI, you'll notice three new CSV files in the /XeroGen/scripts folder:

API_keys.csv: Contains API keys for OpenAI. Comprises two columns: 'Title' and 'API Key'. Though you can add API keys via the interface, you might find it easier to directly edit this CSV for now.

prompts.csv: Here, you'll add your seed prompts or prompt generators. This CSV has a 'Title' column and a 'Prompt' column. Like the API keys, add your prompts directly to this CSV, save, and then reload the interface to see them in the dropdown menu.

chatGPT_responses.csv: If you opt to save the generated prompts via the interface, they will be stored in this CSV.
Interface Layout

API Key Input: The first two fields let you enter a title and an API key.

API Key Dropdown: Here, you can select an existing API key.

Prompt Dropdown: Choose a key or seed prompt to precede your request.

Message Box: This is where you enter your request that'll be paired with the seed prompt for ChatGPT.

Model Dropdown: Once an API key is available, this dropdown allows you to choose the ChatGPT model.

For a successful request, ensure you've selected a prompt, entered a message, selected/entered an API key, and chosen a model. The rest of the fields are optional.

Token Limit Slider: Set a limit on the response tokens.
Prompt Multiplier Slider: Tied to Xerophayze's Ultimate Stable Diffusion Prompt Generator, but can also work with other generators. It simply prepends the user message with a format like '# prompts'.
The next fields are optional checkboxes:

Save Responses: Tick to save ChatGPT responses.
USDPG Specific Options: The next three checkboxes are specific to the Ultimate Stable Diffusion Prompt Generator by Xerophayze. They might not be applicable if you're using a different prompt generator or simply sending requests.
After configuring your settings, hit the 'Run' button to get the responses from ChatGPT. You can then copy and paste these responses into other sections of Automatic 1111.

Future Enhancements
Interface Improvements: Ability to add new API keys and seed prompts directly from the interface and refresh dropdown menus without reloading.
Request Enhancements: Separate GPT requests for the seed prompt and user message. On subsequent requests, the system will modify and resend the second request.
Integration: 'Send to' buttons to directly send the outputs to text-to-image, image-to-image, and other modules.
