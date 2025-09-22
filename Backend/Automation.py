import os
import asyncio
import subprocess
import requests
import keyboard
import webbrowser
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from pywhatkit import search, playonyt
from AppOpener import open as appopen, close as appclose
from rich import print
import openai

# Load API key
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

# OpenAI client (using Groq endpoint)
openai.api_key = GroqAPIKey
openai.api_base = "https://api.groq.com/openai/v1"

# System chat starter
messages = []
SystemChatBot = [{
    "role": "system",
    "content": f"Hello, I am {os.environ.get('Username', 'User')}, You're a content writer. You have to write content like a letter."
}]

# User-agent for web scraping
useragent = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/100.0.4896.75 Safari/537.36'
)

# -------------------------------
# Functional Actions
# -------------------------------

def GoogleSearch(topic: str) -> bool:
    search(topic)
    return True

def YouTubeSearch(topic: str) -> bool:
    url = f"https://www.youtube.com/results?search_query={topic}"
    webbrowser.open(url)
    return True

def PlayYoutube(query: str) -> bool:
    playonyt(query)
    return True

def OpenNotepad(file_path: str):
    try:
        subprocess.Popen(['notepad.exe', file_path])
    except Exception as e:
        print(f"[red]Failed to open Notepad:[/red] {e}")

def ContentWriterAI(prompt: str) -> str:
    messages.append({"role": "user", "content": prompt})
    try:
        response = openai.ChatCompletion.create(
            model="mixtral-8x7b-32768",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True
        )

        answer = ""
        for chunk in response:
            if "choices" in chunk:
                delta = chunk["choices"][0]["delta"].get("content")
                if delta:
                    print(delta, end="", flush=True)
                    answer += delta

        messages.append({"role": "assistant", "content": answer})
        return answer
    except Exception as e:
        print(f"[red]Error using Groq API:[/red] {e}")
        return "Error generating content."

def Content(topic: str) -> bool:
    topic_clean = topic.strip().replace("content ", "")
    result = ContentWriterAI(topic_clean)
    file_name = f"Data/{topic_clean.lower().replace(' ', '')}.txt"

    os.makedirs("Data", exist_ok=True)
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(result)

    OpenNotepad(file_name)
    return True

def OpenApp(app_name: str, session=requests.session()) -> bool:
    try:
        appopen(app_name, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        print(f"[yellow]Local app not found. Attempting web search...[/yellow]")

        def extract_links(html: str) -> list:
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=True)
            return [link.get('href') for link in links]

        def search_google(query: str) -> str:
            headers = {"User-Agent": useragent}
            response = session.get(f"https://www.google.com/search?q={query}", headers=headers)
            return response.text if response.status_code == 200 else None

        html = search_google(app_name)
        if html:
            links = extract_links(html)
            if links:
                webbrowser.open("https://www.google.com" + links[0])
        return True

def CloseApp(app_name: str) -> bool:
    try:
        appclose(app_name, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        return False

def System(command: str) -> bool:
    volume_actions = {
        "mute": "volume mute",
        "unmute": "volume mute",
        "volume up": "volume up",
        "volume down": "volume down"
    }
    action = volume_actions.get(command.lower())
    if action:
        keyboard.press_and_release(action)
        return True
    return False

# -------------------------------
# Command Dispatcher
# -------------------------------

async def TranslateAndExecute(commands: list[str]):
    tasks = []

    for command in commands:
        cmd = command.lower().strip()

        if cmd.startswith("open "):
            tasks.append(asyncio.to_thread(OpenApp, cmd[5:]))
        elif cmd.startswith("close "):
            tasks.append(asyncio.to_thread(CloseApp, cmd[6:]))
        elif cmd.startswith("play "):
            tasks.append(asyncio.to_thread(PlayYoutube, cmd[5:]))
        elif cmd.startswith("content "):
            tasks.append(asyncio.to_thread(Content, cmd))
        elif cmd.startswith("google search "):
            tasks.append(asyncio.to_thread(GoogleSearch, cmd[14:]))
        elif cmd.startswith("youtube search "):
            tasks.append(asyncio.to_thread(YouTubeSearch, cmd[15:]))
        elif cmd.startswith("system "):
            tasks.append(asyncio.to_thread(System, cmd[7:]))
        else:
            print(f"[yellow]Unknown command:[/yellow] {command}")
    
    results = await asyncio.gather(*tasks)
    for result in results:
        yield result

async def Automation(commands: list[str]):
    async for _ in TranslateAndExecute(commands):
        pass
    return True

# -------------------------------
# Main
# -------------------------------

if __name__ == "__main__":
    sample_commands = [
        "open facebook",
        "open instagram",
        "open telegram",
        "play afsanay",
        "content song for me",
        "open spotify",
        "google search Elon Musk",
        "youtube search python automation",
        "system volume down",
        "open bluetooth"
    ]
    asyncio.run(Automation(sample_commands))
