import requests
import json
import os
import sys
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
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
    # print(content)
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "remove useless information and translate this content to vietnamese: \n\n" + content
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
        
        # Debug: Save full response
        with open("api_response.json", "w") as f:
            json.dump(response_data, f, indent=2)
        
        # Extract and print the response content
        if 'choices' in response_data and len(response_data['choices']) > 0:
            message = response_data['choices'][0].get('message', {})
            if 'content' in message:
                print("Response:")
                # print(message['content'])
                # write to file txt
                open("content.txt", "w", encoding="utf-8").write(message['content'])                # 
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

if __name__ == "__main__":
    main()