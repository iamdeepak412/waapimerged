from flask import Flask, jsonify, request
from flasgger import Swagger
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
swagger = Swagger(app)

# WhatsApp Cloud API endpoint and authentication details
WHATSAPP_API_URL = 'https://graph.facebook.com/v17.0/139913512540275/messages'
API_KEY = os.getenv("API_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Function to convert ISO timestamp to UNIX timestamp
def iso_to_unix(iso_timestamp):
    return int(datetime.fromisoformat(iso_timestamp).timestamp())

# Function to make API requests
def make_request(url, headers, params=None):
    try:
        # Make the GET request
        response = requests.get(url, headers=headers, params=params)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Return JSON response
            return response.json()
        else:
            return {"error": f"Request failed with status code: {response.status_code}"}

    except requests.RequestException as e:
        return {"error": f"Request Exception: {e}"}

@app.route('/send', methods=['POST'])
def send_message():
    """
    Send a WhatsApp message to multiple recipients.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: SendMessage
          required:
            - recipients
            - template_name
          properties:
            recipients:
              type: array
              items:
                type: string
              example: ["recipient1", "recipient2"]
              description: The list of recipient phone numbers.
            template_name:
              type: string
              example: "YourTemplateName"
              description: The name of the WhatsApp template to use.
            template_variables:
              type: object
              example: {"variable1": "John,Doe", "variable2": "Value2", "variable3": "Value3"}
              description: Optional variables to be included in the template.
    responses:
      200:
        description: Messages sent successfully.
      400:
        description: Missing required parameters or invalid request format.
    """
    message_data = request.get_json()
    recipients = message_data.get('recipients')
    template_name = message_data.get('template_name')
    template_variables = message_data.get('template_variables', {})

    if not recipients or not template_name:
        return jsonify({"error": "Missing required parameters"}), 400

    variable_names = template_variables.get('variable1', '').split(',')
    for i, recipient in enumerate(recipients):
        if i < len(variable_names):
            template_variables[f'user{i+1}'] = variable_names[i]

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "en_US"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {
                                "type": "text",
                                "text": template_variables.get(f'user{i+1}', '')
                            },
                            {
                                "type": "text",
                                "text": template_variables.get('variable2', '')
                            },
                            {
                                "type": "text",
                                "text": template_variables.get('variable3', '')
                            }
                        ]
                    }
                ]
            }
        }

        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }

        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)

        response_data = response.json()

        print(f"WhatsApp API Response for {recipient}:")
        print(response_data)

    return jsonify({"message": "Messages sent successfully!"}), 200

@app.route('/conversation_analytics', methods=['POST'])
def get_conversation_analytics():
    """
    Get conversation analytics data.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: ConversationAnalytics
          required:
            - start_date
            - end_date
            - granularity
          properties:
            start_date:
              type: string
              example: "2023-12-01T00:00:00"
              description: The start date in ISO format.
            end_date:
              type: string
              example: "2023-12-01T00:00:00"
              description: The end date in ISO format.
            granularity:
              type: string
              example: "DAILY"
              description: The granularity of the data (HALF_HOUR, DAILY, MONTHLY).
    responses:
      200:
        description: Conversation analytics data retrieved successfully.
      400:
        description: Missing required parameters or invalid request format.
    """
    data = request.json

    if 'start_date' in data and 'end_date' in data:
        start_unix = iso_to_unix(data['start_date'])
        end_unix = iso_to_unix(data['end_date'])
        granularity = data.get('granularity', 'MONTHLY')
        endpoint = f"https://graph.facebook.com/v18.0/118254494612532"
        params = {
            'fields': f"conversation_analytics.start({start_unix}).end({end_unix}).granularity({granularity}).phone_numbers([]).dimensions(['CONVERSATION_CATEGORY','CONVERSATION_TYPE','COUNTRY','PHONE'])",
            'access_token': ACCESS_TOKEN
        }
        response = requests.get(endpoint, params=params)
        if response.ok:
            return jsonify(response.json())
        else:
            return jsonify({"error": response.text}), response.status_code
    else:
        return jsonify({"error": "Start date and end date are required in ISO format in the request body."}), 400

@app.route('/template_analytics', methods=['POST'])
def get_template_analytics():
    """
    Get template analytics data.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: TemplateAnalytics
          required:
            - start_date
            - end_date
            - template_ids
          properties:
            start_date:
              type: string
              example: "2023-12-01T00:00:00"
              description: The start date in ISO format.
            end_date:
              type: string
              example: "2023-12-01T00:00:00"
              description: The end date in ISO format.
            granularity:
              type: string
              example: "DAILY"
              description: The granularity of the data (only  DAILY is supported).
            template_ids:
              type: array
              items:
                type: string
              example: ["template_id_1", "template_id_2"]
              description: The IDs of the templates to retrieve analytics for.
    responses:
      200:
        description: Template analytics data retrieved successfully.
      400:
        description: Missing required parameters or invalid request format.
    """
    data = request.json
    access_token = ACCESS_TOKEN  # Replace with your Facebook access token

    if 'start_date' in data and 'end_date' in data and 'template_ids' in data:
        start_unix = iso_to_unix(data['start_date'])
        end_unix = iso_to_unix(data['end_date'])
        granularity = data.get('granularity')
        template_ids = data['template_ids']

        api_url = 'https://graph.facebook.com/v18.0/118254494612532/template_analytics'
        params = {
            'start': start_unix,
            'end': end_unix,
            'granularity': granularity,
            'metric_types': "['SENT','DELIVERED','READ','CLICKED']",
            'template_ids': template_ids
        }
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(api_url, params=params, headers=headers)
        if response.ok:
            return jsonify(response.json())
        else:
            return jsonify({"error": response.text}), response.status_code
    else:
        return jsonify({"error": "Start date, end date, and template IDs are required in the request body."}), 400

# Define the rest of the endpoints...

@app.route('/messaging_analytics', methods=['POST'])
def get_messaging_analytics():
    """
    Get messaging analytics data.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: MessagingAnalytics
          required:
            - start_date
            - end_date
            - template_ids
          properties:
            start_date:
              type: string
              example: "2023-12-01T00:00:00"
              description: The start date in ISO format.
            end_date:
              type: string
              example: "2023-12-01T00:00:00"
              description: The end date in ISO format.
            granularity:
              type: string
              example: "DAILY"
              description: The granularity of the data (DAILY, WEEKLY, MONTHLY).
    responses:
      200:
        description: Messaging analytics data retrieved successfully.
      400:
        description: Missing required parameters or invalid request format.
    """
    data = request.json
    access_token = ACCESS_TOKEN  # Replace with your Facebook access token

    if 'start_date' in data and 'end_date' in data:
        start_unix = iso_to_unix(data['start_date'])
        end_unix = iso_to_unix(data['end_date'])
        granularity = data.get('granularity')
        url = f"https://graph.facebook.com/v18.0/118254494612532"
        params = {
            "fields": f"analytics.start({start_unix}).end({end_unix}).granularity({granularity})",
            "access_token": access_token
        }
        response = requests.get(url, params=params)
        if response.ok:
            return jsonify(response.json())
        else:
            return jsonify({"error": response.text}), response.status_code
    else:
        return jsonify({"error": "Start date and end date are required in ISO format in the request body."}), 400

@app.route('/approved_templates')
def approved_template():
    """
    Get contents of approved WhatsApp templates.
    ---
    responses:
      200:
        description: Contents of approved templates.
      500:
        description: Internal server error.
    """
    whatsapp_url = "https://graph.facebook.com/v18.0/118254494612532/message_templates"
    whatsapp_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"  # Replace with your Facebook access token
    }
    whatsapp_params = {
        "fields": "name,status",
        "status": "APPROVED"
    }

    result = make_request(whatsapp_url, whatsapp_headers, whatsapp_params)
    return jsonify(result)

@app.route('/rejected_templates')
def rejected_templates():
    """
    Get rejected WhatsApp templates.
    ---
    responses:
      200:
        description: List of rejected templates.
      500:
        description: Internal server error.
    """
    whatsapp_url = "https://graph.facebook.com/v18.0/118254494612532/message_templates"
    whatsapp_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"  
    }
    whatsapp_params = {
        "fields": "name,status",
        "status": "REJECTED"
    }

    result = make_request(whatsapp_url, whatsapp_headers, whatsapp_params)
    return jsonify(result)

@app.route('/approved_template_contents')
def approved_template_contents():
    """
    Get contents of approved WhatsApp templates.
    ---
    responses:
      200:
        description: Contents of approved templates.
      500:
        description: Internal server error.
    """
    whatsapp_url = "https://graph.facebook.com/v18.0/118254494612532/message_templates"
    whatsapp_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"  # Replace with your Facebook access token
    }
    whatsapp_params = {
        "fields": "name,status,components",
        "status": "APPROVED"
    }

    result = make_request(whatsapp_url, whatsapp_headers, whatsapp_params)
    return jsonify(result)

@app.route('/rejected_template_contents')
def rejected_template_contents():
    """
    Get contents of rejected WhatsApp templates.
    ---
    responses:
      200:
        description: Contents of rejected templates.
      500:
        description: Internal server error.
    
    """
    whatsapp_url = "https://graph.facebook.com/v18.0/118254494612532/message_templates"
    whatsapp_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    whatsapp_params = {
        "fields": "name,status,components",
        "status": "REJECTED"
    }

    result = make_request(whatsapp_url, whatsapp_headers, whatsapp_params)
    return jsonify(result)

@app.route('/phone_number_status')
def phone_number_status():
    """
    Get WhatsApp phone number status.
    ---
    responses:
      200:
        description: Phone number status.
      500:
        description: Internal server error.
    """
    whatsapp_url = "https://graph.facebook.com/v18.0/139913512540275"  # Replace with your WhatsApp phone number ID
    whatsapp_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    result = make_request(whatsapp_url, whatsapp_headers)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)




