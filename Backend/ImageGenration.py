import asyncio
import os 
import requests
from random import randint
from time import sleep
from PIL import Image
from dotenv import get_key
from datetime import datetime

# === Configuration ===
HF_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_API_KEY = get_key(".env", "HuggingFaceAPIKey") #env key access ho gya
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"} 

DATA_DIR = "Data" # folder jahan image save hoga
STATUS_FILE = os.path.join("Frontend", "Files", "ImageGeneration.data") # Ye file "Frontend/Files/" folder me hogi aur is file se prompt aur status read kiya jayega
IMAGE_COUNT = 4 

# === Ensure directories exist ===
os.makedirs(DATA_DIR, exist_ok=True)

#prompt ko safe filename mai convert krega spaces ko underscores mai,lowercase mai
def sanitize_filename(text: str) -> str:
    return "_".join(text.strip().split()).lower()


def open_images(prompt: str): # this opens and show images ek ek krke
    safe_prompt = sanitize_filename(prompt)
    for i in range(1, IMAGE_COUNT + 1):
        img_path = os.path.join(DATA_DIR, f"{safe_prompt}_{i}.jpg") #create image path
        try:
            img = Image.open(img_path) #it open image
            print(f"[INFO] Opening: {img_path}")
            img.show() #show image
            sleep(1) # delay 1 second ka 
        except IOError:
            print(f"[ERROR] Could not open image: {img_path}")


async def fetch_image(payload):
    try:
        response = await asyncio.to_thread(
            requests.post, HF_MODEL_URL, headers=HEADERS, json=payload
        )
        if response.status_code == 200:
            return response.content #if image successfully genrate hui  then it return binary content
        else:
            print(f"[ERROR] API Error ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"[EXCEPTION] During image fetch: {e}") # kisi ko bhi expect krke image return krega
        return None


async def generate_images(prompt: str):
    tasks = []
    safe_prompt = sanitize_filename(prompt)

    for i in range(IMAGE_COUNT):
        payload = {
            "inputs": f"{prompt}, ultra high definition, quality=4K, cinematic lighting, sharp, seed={randint(1, 1_000_000)}"  #hamne random no. isliye use kra hai bcz har aar image alag nikle hai
        }
        tasks.append(asyncio.create_task(fetch_image(payload)))

    results = await asyncio.gather(*tasks)# sab task comp. hone tk wait krega then  or result mai image dega

    for i, img_bytes in enumerate(results):
        if img_bytes:
            file_path = os.path.join(DATA_DIR, f"{safe_prompt}_{i + 1}.jpg")
            with open(file_path, "wb") as f:
                f.write(img_bytes)
            print(f"[SAVED] {file_path}")
        else:
            print(f"[SKIPPED] Image {i + 1} could not be fetched.")  #if image not found then it skip msg


def GenerateImages(prompt: str):
    print(f"\n[GENERATING] Prompt: {prompt}\n")
    asyncio.run(generate_images(prompt))
    open_images(prompt)


# === Main Loop ===
if __name__ == "__main__":
    while True:
        try:
            if not os.path.exists(STATUS_FILE):
                print("[WAITING] Status file not found. Retrying...")
                sleep(2) #file nhi mili to 2 second wait krega
                continue

            with open(STATUS_FILE, "r") as f:
                data = f.read().strip()

            if not data or "," not in data:
                sleep(1)
                continue

            prompt, status = map(str.strip, data.split(",", 1))

            if status.lower() == "true" and prompt:
                GenerateImages(prompt)

                # Reset status
                with open(STATUS_FILE, "w") as f:
                    f.write("false,false")

                print(f"[DONE] Completed image generation for: {prompt}")
                break

            sleep(1)

        except Exception as e:
            print(f"[CRITICAL ERROR] {e}")
            sleep(3)
