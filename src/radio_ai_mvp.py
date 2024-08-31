import json
import requests
import tempfile
import os
import subprocess
import time
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

# Replace with your actual Vercel domain or localhost if running locally
BASE_URL = 'http://localhost:3000'

def load_credentials():
    print(Fore.CYAN + "Loading credentials...")
    try:
        with open('creds.json', 'r') as f:
            creds = json.load(f)
        print(Fore.GREEN + "Credentials loaded successfully.")
        return creds
    except FileNotFoundError:
        print(Fore.RED + "Error: creds.json file not found.")
        return None
    except json.JSONDecodeError:
        print(Fore.RED + "Error: creds.json file is not valid JSON.")
        return None

def fetch_nytimes_articles(api_key, num_articles=5):
    print(Fore.CYAN + f"Fetching {num_articles} articles from NYTimes API...")
    base_url = "https://api.nytimes.com/svc"
    endpoint = f"{base_url}/topstories/v2/world.json?api-key={api_key}"
    response = requests.get(endpoint)
    if response.status_code == 200:
        data = response.json()
        articles = []
        for article in data['results'][:num_articles]:
            articles.append({
                'title': article['title'],
                'abstract': article['abstract'],
                'url': article['url']
            })
        print(Fore.GREEN + f"Successfully fetched {len(articles)} articles.")
        return articles
    print(Fore.RED + f"Failed to fetch articles. Status code: {response.status_code}")
    return None

def display_articles(articles):
    print(Fore.CYAN + "Displaying fetched articles:")
    for i, article in enumerate(articles, 1):
        print(Fore.YELLOW + f"\n{i}. Title: {article['title']}")
        print(Fore.WHITE + f"   Abstract: {article['abstract']}")

def get_user_choice(max_choice):
    while True:
        try:
            choice = int(input(Fore.CYAN + f"\nChoose an article (1-{max_choice}): "))
            if 1 <= choice <= max_choice:
                return choice
            else:
                print(Fore.RED + f"Please enter a number between 1 and {max_choice}.")
        except ValueError:
            print(Fore.RED + "Please enter a valid number.")

def fetch_full_article(article):
    print(Fore.CYAN + "Fetching full article text...")
    try:
        response = requests.get(article['url'])
        response.raise_for_status()
        # This is a simple extraction and might not work for all articles
        # A more robust solution would use a library like newspaper3k or beautifulsoup4
        article_text = response.text.split('<p class="css-at9mc1 evys1bk0">')[1].split('</p>')[0]
        print(Fore.GREEN + "Full article text fetched successfully.")
        return article_text
    except Exception as e:
        print(Fore.YELLOW + f"Failed to fetch full article text: {str(e)}")
        print(Fore.YELLOW + "Using article abstract as fallback.")
        return article['abstract']

def create_request_template(article, full_text):
    print(Fore.CYAN + "Creating request template...")
    with open('request.txt', 'r') as f:
        template = f.read()
    
    article_content = f"Title: {article['title']}\n\nContent: {full_text}\n\nURL: {article['url']}"
    request = f"Selected Article:\n\n{article_content}\n\n{template}"
    print(Fore.GREEN + "Request template created successfully.")
    return request

def edit_request(request):
    editor = os.environ.get('EDITOR', 'nano')  # default to nano if no EDITOR is set
    print(Fore.CYAN + f"Opening request in {editor} for editing...")
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix=".tmp") as tf:
        tf.write(request)
        tf.flush()
        subprocess.call([editor, tf.name])
        
        tf.seek(0)
        edited_request = tf.read()
    
    print(Fore.GREEN + "Request editing completed.")
    return edited_request

def display_full_prompt(request):
    print(Fore.CYAN + "Full prompt to be sent to Anthropic API:")
    print(Fore.WHITE + "-" * 50)
    print(Fore.YELLOW + request)
    print(Fore.WHITE + "-" * 50)

def generate_lyrics(client, request):
    print(Fore.CYAN + "Generating lyrics using Anthropic API...")
    prompt = f"{HUMAN_PROMPT}{request}{AI_PROMPT}"
    
    response = client.completions.create(
        model="claude-2",
        max_tokens_to_sample=300,
        prompt=prompt,
    )
    print(Fore.GREEN + "Lyrics generated successfully.")
    return response.completion

def generate_audio_by_prompt(lyrics):
    print(Fore.CYAN + "Generating audio using Suno API...")
    url = f"{BASE_URL}/api/generate"
    payload = {
        "prompt": f"An 8bit chiptune style song with the following lyrics: {lyrics}. The music should have a retro video game feel, with characteristic electronic bleeps and bloops.",
        "make_instrumental": False,
        "wait_audio": False
    }
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        data = response.json()
        print(Fore.GREEN + "Audio generation initiated successfully.")
        return data
    else:
        print(Fore.RED + f"Failed to initiate audio generation. Status code: {response.status_code}")
        return None

def get_audio_information(audio_ids):
    url = f"{BASE_URL}/api/get?ids={audio_ids}"
    response = requests.get(url)
    return response.json()

def check_audio_status(audio_ids):
    print(Fore.CYAN + "Checking audio generation status...")
    for _ in range(60):  # Check for up to 5 minutes
        data = get_audio_information(audio_ids)
        if data[0]["status"] == 'streaming':
            print(Fore.GREEN + "Audio generation completed.")
            return data
        print(Fore.YELLOW + "Audio generation in progress. Waiting...")
        time.sleep(5)  # Wait for 5 seconds before checking again
    print(Fore.RED + "Audio generation timed out.")
    return None

def main():
    print(Fore.MAGENTA + Style.BRIGHT + "Welcome to RADIO.AI MVP!")
    creds = load_credentials()
    
    if not creds:
        print(Fore.RED + "Failed to load credentials. Exiting.")
        return

    # NYTimes API integration
    nytimes_key = creds['nytimes']['api_key']
    articles = fetch_nytimes_articles(nytimes_key)
    
    if articles:
        display_articles(articles)
        choice = get_user_choice(len(articles))
        selected_article = articles[choice - 1]
        
        print(Fore.CYAN + "\nSelected Article:")
        print(Fore.YELLOW + f"Title: {selected_article['title']}")
        print(Fore.WHITE + f"Abstract: {selected_article['abstract']}")
        print(Fore.BLUE + f"URL: {selected_article['url']}")
        
        full_text = fetch_full_article(selected_article)
        request = create_request_template(selected_article, full_text)
        edited_request = edit_request(request)
        
        while True:
            display_full_prompt(edited_request)
            edit_again = input(Fore.CYAN + "Would you like to edit the prompt again? (y/n): ").lower()
            if edit_again != 'y':
                break
            edited_request = edit_request(edited_request)
        
        print(Fore.CYAN + "\nGenerating lyrics based on the edited request...")
        
        # Anthropic API integration
        anthropic_key = creds['anthropic']['api_key']
        anthropic_client = Anthropic(api_key=anthropic_key)
        lyrics = generate_lyrics(anthropic_client, edited_request)
        
        print(Fore.GREEN + "\nGenerated Lyrics:")
        print(Fore.YELLOW + lyrics)
        
        print(Fore.CYAN + "\nGenerating 8bit chiptune style music...")
        
        # Suno API integration
        audio_data = generate_audio_by_prompt(lyrics)
        if audio_data:
            ids = f"{audio_data[0]['id']},{audio_data[1]['id']}"
            print(Fore.CYAN + f"Audio generation IDs: {ids}")
            
            final_audio_data = check_audio_status(ids)
            if final_audio_data:
                print(Fore.GREEN + "Audio URLs (8bit chiptune style):")
                print(Fore.YELLOW + f"1. {final_audio_data[0]['id']} ==> {final_audio_data[0]['audio_url']}")
                print(Fore.YELLOW + f"2. {final_audio_data[1]['id']} ==> {final_audio_data[1]['audio_url']}")
            else:
                print(Fore.RED + "Failed to generate audio.")
        else:
            print(Fore.RED + "Failed to initiate audio generation.")
    else:
        print(Fore.RED + "Failed to fetch news articles. Exiting.")

if __name__ == "__main__":
    main()
