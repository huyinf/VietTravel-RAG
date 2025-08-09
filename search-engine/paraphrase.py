import requests
import json
import os
import sys
from dotenv import load_dotenv
import glob

# from router.ai
models = [
    "google/gemini-2.0-flash-exp:free",
    "deepseek/deepseek-r1-0528:free",
    "microsoft/mai-ds-r1:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "deepseek/deepseek-r1:free",
    "openai/gpt-oss-20b:free",
    "z-ai/glm-4.5-air:free",
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "moonshotai/kimi-dev-72b:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
    "qwen/qwen3-235b-a22b:free",
    "moonshotai/kimi-vl-a3b-thinking:free",
    "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
    "nousresearch/deephermes-3-llama-3-8b-preview:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "mistralai/mistral-nemo:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.1-405b-instruct:free",
    "deepseek/deepseek-r1-distill-qwen-14b:free",
    "qwen/qwen3-4b:free",
    "qwen/qwen3-30b-a3b:free",
    "qwen/qwen3-8b:free",
    "qwen/qwen3-14b:free",
    "moonshotai/kimi-k2:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "tencent/hunyuan-a13b-instruct:free",
    "sarvamai/sarvam-m:free",
    "thudm/glm-z1-32b:free",
    "shisa-ai/shisa-v2-llama3.3-70b:free",
    "arliai/qwq-32b-arliai-rpr-v1:free",
    "featherless/qwerky-72b:free",
    "google/gemma-3-4b-it:free",
    "rekaai/reka-flash-3:free",
    "qwen/qwq-32b:free",
    "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
    "cognitivecomputations/dolphin3.0-mistral-24b:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-3n-e2b-it:free",
    "google/gemma-3n-e4b-it:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "google/gemma-2-9b-it:free"
]

raw_data = "C:/Users/Admin/Documents/NLP/text_mining/seminar/travel_rag/search-engine/data"

# txt_files = glob.glob(os.path.join(raw_data, "**", "*.txt"), recursive=True)

test_dir = "C:/Users/Admin/Documents/NLP/text_mining/seminar/travel_rag/search-engine/test"

os.makedirs(test_dir, exist_ok=True)


def main(provider="openrouter"):
    # Load environment variables
    load_dotenv()

    if provider == "openrouter":
        # Get API key from environment
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("Error: OPENROUTER_API_KEY not found in .env file")
            sys.exit(1)

        # Prepare the request
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        content = open("C:/Users/Admin/Documents/NLP/text_mining/seminar/travel_rag/search-engine/data/25/travel/1_tag.txt", "r", encoding="utf-8").read()
        # print(type(content))
        
        for model in models:
            print(f"processing with model: {model}")
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "remove useless text, unrelated to the content, remove icons, just preserve readable and renderable characters and translate this content to vietnamese: \n\n" + content
                            }
                        ]
                    }
                ]
            }


            try:
                # Make the API request
                response = requests.post(
                    url=url,
                    headers=headers,
                    json=payload,  # Use json parameter instead of data=json.dumps()
                    timeout=30  # 30 seconds timeout
                )
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Parse the response
                response_data = response.json()
                # print(response_data)

                # Debug: Save full response
                with open(f"{test_dir}/{model.split(":")[0].split("/")[-1]}.json", "w") as f:
                    json.dump(response_data, f, indent=2)
                
                # Extract and print the response content
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    message = response_data['choices'][0].get('message', {})
                    if 'content' in message:
                        # print("Response:")
                        # print(message['content'])
                        # write to file txt
                        open(f"{test_dir}/{model.split(":")[0].split("/")[-1]}.txt", "w", encoding="utf-8").write(message['content'])                # 
                    else:
                        print("No content in message:", message)
                else:
                    print("Unexpected response format. Check api_response.json for details.")
                    print("Response keys:", response_data.keys())
            
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_response = e.response.json()
                        print("Error details:", json.dumps(error_response, indent=2))
                    except ValueError:
                        print("Error response:", e.response.text)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {str(e)}")
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
    elif provider == "tinq":
        api_key = os.getenv("TINQ_API_KEY")
        if not api_key:
            print("Error: TINQ_API_KEY not found in .env file")
            sys.exit(1)
        
        url = "https://tinq.ai/api/v2/rewrite"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        content = open("C:/Users/Admin/Documents/NLP/text_mining/seminar/travel_rag/search-engine/data/25/travel/1_tag.txt", "r", encoding="utf-8").read()

        payload = {
            "text": "remove useless text, unrelated to the content, remove icons, just preserve readable and renderable characters and translate this content to vietnamese: \n\n" + content
        }
        
        try:
            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            print(response_data)
            
            with open(f"tinq.json", "w") as f:
                json.dump(response_data, f, indent=2)
            
            # if 'choices' in response_data and len(response_data['choices']) > 0:
            #     message = response_data['choices'][0].get('message', {})
            #     if 'content' in message:
            #         # print("Response:")
            #         # print(message['content'])
            #         # write to file txt
            #         open(f"{test_dir}/tinq.txt", "w", encoding="utf-8").write(message['content'])                # 
            #     else:
            #         print("No content in message:", message)
            # else:
            #     print("Unexpected response format. Check api_response.json for details.")
            #     print("Response keys:", response_data.keys())
        
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_response = e.response.json()
                    print("Error details:", json.dumps(error_response, indent=2))
                except ValueError:
                    print("Error response:", e.response.text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")        

if __name__ == "__main__":
    main("tinq")