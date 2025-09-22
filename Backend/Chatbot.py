import os
import datetime
from json import load, dump
from groq import Groq
from dotenv import dotenv_values
from rich.console import Console
from rich.prompt import Prompt

# Initialize rich console
console = Console()

# Load environment variables
env = dotenv_values(".env")
GroqAPIKey = env.get("GroqAPIKey")
Username = env.get("Username", "User")
Assistantname = env.get("Assistantname", "Assistant")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# Constants
CHAT_LOG_PATH = "Data/ChatLog.json"
MAX_TOKENS = 1024
MODEL = "llama-3.3-70b-versatile"

# System prompt
#here the llm model got train 
SystemPrompt = f"""
Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question. ***
*** Reply in only English, even if the question is in Hindi. ***
*** Do not provide notes or disclaimers. ***
*** Never mention your training data. ***
"""

SystemChatBot = [{"role": "system", "content": SystemPrompt.strip()}]

##it load chat from file ki agar json mai pehele se exist krta hai to yie wo response dega if not then ye directory banake hmko store krne ko dega 
def load_chat_log():
    if not os.path.exists("Data"):
        os.makedirs("Data")
    if not os.path.exists(CHAT_LOG_PATH):
        with open(CHAT_LOG_PATH, "w") as f:
            dump([], f)
        return []
    with open(CHAT_LOG_PATH, "r") as f:
        return load(f)


def save_chat_log(messages):
    with open(CHAT_LOG_PATH, "w") as f:
        dump(messages, f, indent=4)


def RealtimeInformation():
    now = datetime.datetime.now()
    return (
        f"Use this real-time info if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')}h:{now.strftime('%M')}m:{now.strftime('%S')}s\n"
    )

#yie answer ko modify krega like unusual things ko remove krega
def AnswerModifier(answer):
    return "\n".join(line.strip() for line in answer.splitlines() if line.strip())

#chatbot is format mai save krega files ko in json file
def ChatBot(user_query: str):
    messages = load_chat_log()
    messages.append({"role": "user", "content": user_query})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens=MAX_TOKENS,
            temperature=0.7,
            top_p=1,
            stream=True
        )

        answer = ""
        for chunk in response:
            delta = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
            if delta:
                print(delta, end="", flush=True)
                answer += delta

        print()  # Finish the line
        answer = answer.replace("</s>", "").strip()
        messages.append({"role": "assistant", "content": answer})
        save_chat_log(messages)

        return AnswerModifier(answer)

    except Exception as e:
        console.print(f"[red]Error occurred:[/red] {e}")
        save_chat_log([])  # Reset chat if corrupted
        return ChatBot(user_query)


# --------------------------
# CLI Interaction
# --------------------------
#yie  jo hai color provide krta hai and yie terminal ko access krne mai kaam aata hai and usme color ke sath likhne ke kaam aata hai 
if __name__ == "__main__":
    console.print("[bold cyan]Welcome to your Advanced Groq AI Chatbot![/bold cyan]")
    console.print(f"Logged in as: [green]{Username}[/green] · Assistant: [magenta]{Assistantname}[/magenta]")
    console.print("Type [bold yellow]exit[/bold yellow] to quit, or [bold yellow]clear[/bold yellow] to reset chat.\n")
### agar exit or quit pr click likhte hai tb yie exit le le ga 
    while True:
        try:
            query = Prompt.ask("[bold blue]You[/bold blue]")
            if query.lower() in ["exit", "quit"]:
                console.print("[bold red]Session Ended.[/bold red]")
                break
            elif query.lower() == "clear":
                save_chat_log([])
                console.print("[yellow]Chat history cleared.[/yellow]\n")
                continue

            ChatBot(query)

        except KeyboardInterrupt:
            console.print("\n[red]Interrupted by user.[/red]")
            break
