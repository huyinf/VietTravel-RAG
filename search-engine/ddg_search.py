import os
import json

# read file api_response.json
with open("api_response.json", "r") as f:
    data = json.load(f)

# write the content to txt file
open("content.txt", "w", encoding="utf-8").write(data['choices'][0]['message']['content'])
