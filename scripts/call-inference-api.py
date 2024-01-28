import requests


def main():

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()

    apiToken="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"
    headers = {
        "Authorization": "Bearer " + apiToken
    }

    API_URL = "https://api-inference.huggingface.co/models/bert-base-uncased"

    data = query({
        "inputs": "Opposite of black is [MASK].",
        "options": {
            "use_cache": False
        }
        })

    # API_URL = "https://api-inference.huggingface.co/models/gpt2"
    # data = query("Can you please let us know more details about your ")

    print(data)


if __name__=="__main__": 
    main() 
