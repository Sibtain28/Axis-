from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os
import requests  # Add this import for weather API

# Load environment variables
env_vars = dotenv_values(".env")  #able to access .env file

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
# Add OpenWeatherMap API key to your .env file as WeatherAPIKey=your_api_key
WeatherAPIKey = env_vars.get("WeatherAPIKey")

client = Groq(api_key=GroqAPIKey)

System = f"""  
Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***
"""#train llm modle

# Ensure ChatLog file exists i,e . command is store in json
chatlog_path = "Data/ChatLog.json"  
os.makedirs(os.path.dirname(chatlog_path), exist_ok=True)
if not os.path.isfile(chatlog_path):
    with open(chatlog_path, "w") as f:
        dump([], f)

# Google Search abstraction
def GoogleSearch(query):
    try:
        results = list(search(query, advanced=True, num_results=5))
        output = f"The search results for '{query}' are:\n[start]\n"
        for i in results:
            output += f"Title: {i.title}\nDescription: {i.description}\n\n"
        output += "[end]"
        return output
    except Exception as e:
        return f"[start]\nSearch failed for '{query}': {str(e)}\n[end]"

# Weather information function
def GetWeather(city_name=None):
    if not WeatherAPIKey:
        return "Weather API key not configured. Please add WeatherAPIKey to your .env file."
    
    try:
        if not city_name:
            # Try to get location from IP if no city specified
            ip_response = requests.get('https://ipinfo.io')
            if ip_response.status_code == 200:
                city_name = ip_response.json().get('city', 'London')  # Default to London if cannot detect
            else:
                city_name = 'London'
        
        # Get weather data
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WeatherAPIKey}&units=metric"
        response = requests.get(weather_url)
        
        if response.status_code == 200:
            data = response.json()
            weather_info = (
                f"Weather in {data['name']}, {data['sys']['country']}:\n"
                f"Temperature: {data['main']['temp']}°C (feels like {data['main']['feels_like']}°C)\n"
                f"Conditions: {data['weather'][0]['description'].capitalize()}\n"
                f"Humidity: {data['main']['humidity']}%\n"
                f"Wind: {data['wind']['speed']} m/s\n"
                f"Pressure: {data['main']['pressure']} hPa"
            )
            return weather_info
        else:
            return f"Could not fetch weather data for {city_name}. Please check the city name or try again later."
    except Exception as e:
        return f"Error fetching weather information: {str(e)}"

# Text cleanup
def AnswerModifier(Answer):
    return '\n'.join([line for line in Answer.split('\n') if line.strip()]) # it modify answer and question 

# Initial system messages i,e it store in form of that
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# Real-time system info
def Information():
    now = datetime.datetime.now()
    return (
        "Use This Real-time Information if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hours, {now.strftime('%M')} minutes, {now.strftime('%S')} seconds."
    )

# Primary processing logic
def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    # Load chat history
    with open(chatlog_path, "r") as f:
        messages = load(f)

    messages.append({"role": "user", "content": prompt})

    # Check if the prompt is asking for weather information
    weather_trigger_words = ['weather', 'temperature', 'forecast', 'humid', 'rain', 'sunny', 'cloudy']
    is_weather_query = any(word in prompt.lower() for word in weather_trigger_words)
    
    # Extract city name if mentioned
    city_name = None
    if is_weather_query:
        # Simple approach to extract city name - can be improved
        words = prompt.split()
        for i, word in enumerate(words):
            if word.lower() in ['in', 'at', 'for', 'of'] and i+1 < len(words):
                city_name = words[i+1].strip('.,!?')
                break
        
        # If no preposition found, try to find a proper noun (capitalized word)
        if not city_name:
            for word in words:
                if word.istitle() and word.lower() not in weather_trigger_words:
                    city_name = word
                    break

    # Inject appropriate data based on query type
    if is_weather_query:
        SystemChatBot.append({"role": "system", "content": GetWeather(city_name)})
    else:
        SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""
        
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        with open(chatlog_path, "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        return f"[ERROR] Failed to generate response: {str(e)}"

    finally:
        # Remove the last system message regardless of its content
        if SystemChatBot and len(SystemChatBot) > 3:  # Keep the initial 3 messages
            SystemChatBot.pop()

# CLI Entry point
if __name__ == "__main__":
    print("\n🤖 Real-time AI Assistant Ready. Type your query.")
    #here we use loop bcz jisse ki command continous run kre
    while True:  
        try:
            prompt = input("\nYou: ").strip()
            if not prompt:
                continue
            response = RealtimeSearchEngine(prompt)
            print(f"\n{Assistantname}: {response}")
        except KeyboardInterrupt:
            print("\nSession ended.")
            break