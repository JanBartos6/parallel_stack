import requests
import json
import time
import os

# API endpoint to retrieve all Stack Exchange sites
sites_url = "https://api.stackexchange.com/2.3/sites"

keys = {
    "key": os.getenv("STACKEXCHANGE_KEY"),
    "client_id": os.getenv("STACKEXCHANGE_CLIENT_ID")
}

# Retrieve the list of Stack Exchange sites
params = {
    "pagesize": 1000,  # Fetch up to 500 sites at once
    "key": keys['key'],
    "client_id": keys['client_id']
}

response = requests.get(sites_url, params=params)
sites_data = response.json()

# Extract the 'api_site_parameter' values (Those are needed to access the sites through the API)
matches = [
    site['api_site_parameter']
    for site in sites_data['items']
    if 'meta' not in site['api_site_parameter']
]

with open('communities.txt', 'w') as f:
    for match in matches:
        f.write(f"{match}\n")

# Number of days to look back
number_of_days = 1

# API endpoints
url = "https://api.stackexchange.com/2.3/questions"
answers_url = "https://api.stackexchange.com/2.3/questions/{ids}/answers"

# Calculate the 'fromdate' parameter in Unix time
fromdate = int(time.time()) - number_of_days * 24 * 60 * 60

page = 1  # Start from the first page

# Load sites from communities.txt
with open('communities.txt', 'r') as f:
    sites = [line.strip() for line in f.readlines()]

for site in sites:
    has_more = True

    # Loop to paginate through the results
    while has_more:
        try:
            # Set parameters for the request
            params = {
                "order": "desc",
                "sort": "creation",
                "pagesize": 100,
                "page": page,  # Set the current page number
                "site": site,
                "key": keys['key'],
                "client_id": keys['client_id'],
                "filter": "withbody",
                "redirect_uri": "https://stackexchange.com/oauth/login_success"
            }

            # Make the API request
            response = requests.get(url, params=params)
            data = response.json()

            # Process the items and retrieve asnwers (if needed)
            for question in data['items']:
                filtered_question = {
                    "tags": question.get("tags"),
                    "reputation": question['owner'].get("reputation"),
                    "is_answered": question.get("is_answered"),
                    "score": question.get("score"),
                    "last_activity_date": question.get("last_activity_date"),
                    "question_id": question.get("question_id"),
                    "title": question.get("title"),
                    "body": question.get("body")
                }

                question_id = question['question_id']

                # Make a request to get answers
                answer_response = requests.get(answers_url.format(ids=question_id), params={
                    "order": "desc",
                    "sort": "creation",
                    "site": "linux",
                    "key": keys['key'],
                    "client_id": keys['client_id'],
                    "filter": "withbody"
                })

                with open(f'stackexchange_data.json', 'a') as f: # dump questions into the json file
                    json.dump(filtered_question, f)
                    f.write(',\n')

                for answer in answer_response.json()['items']:
                    filtered_answer = {
                    "reputation": question['owner'].get("reputation"),
                    "is_accepted": question.get("is_accepted"),
                    "score": question.get("score"),
                    "last_activity_date": question.get("last_activity_date"),
                    "question_id": question.get("question_id"),
                    "answer_id": answer.get("answer_id"),
                    "title": question.get("title"),
                    "body": question.get("body")
                    }
                    with open(f'stackexchange_data.json', 'a') as f: # dump answers into the json file
                        json.dump(filtered_answer, f)
                        f.write(',\n')

            # Continue looping if 'has_more' is True
            if data['items'][-1]['creation_date'] < fromdate: # Ensuring that only messages newer than specified will be retrieved
                has_more = False

            # Increment the page number for the next batch
            page += 1

            # Sleep between requests to avoid hitting the rate limit
            time.sleep(0.1)
            
        except:
            break
