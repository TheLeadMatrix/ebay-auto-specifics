from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import vision
import openai
import requests
import os
import json
from google.oauth2 import service_account
import traceback
from datetime import datetime

app = Flask(__name__)
# Enable CORS for all routes with all origins
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

# Write Google Cloud credentials to a file and set up client
try:
    google_creds = os.getenv("GOOGLE_CREDENTIALS")
    if not google_creds:
        print("ERROR: GOOGLE_CREDENTIALS environment variable not found")
        vision_client = None
    else:
        print("Found Google credentials, attempting to initialize client...")
        print("Credentials length:", len(google_creds))
        print("First few characters:", google_creds[:50])
        
        try:
            creds_dict = json.loads(google_creds)
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [f for f in required_fields if f not in creds_dict]
            
            if missing_fields:
                print(f"ERROR: Missing required fields in credentials: {missing_fields}")
                vision_client = None
            else:
                # Write credentials to a temporary file
                creds_path = "google_credentials.json"
                with open(creds_path, "w") as f:
                    json.dump(creds_dict, f)
                
                # Create credentials object directly
                credentials = service_account.Credentials.from_service_account_file(creds_path)
                vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                print("✅ Successfully initialized Google Vision client")
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in credentials: {str(e)}")
            vision_client = None
except Exception as e:
    print("❌ Error setting up Google credentials:")
    print(traceback.format_exc())
    vision_client = None

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def check_credentials():
    status = {
        "google": False,
        "openai": False,
        "errors": []
    }
    
    # Check Google credentials
    if not os.getenv("GOOGLE_CREDENTIALS"):
        status["errors"].append("GOOGLE_CREDENTIALS not found in environment")
    else:
        try:
            creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing = [f for f in required_fields if f not in creds_dict]
            if missing:
                status["errors"].append(f"Missing fields in Google credentials: {missing}")
            else:
                status["google"] = True
        except json.JSONDecodeError as e:
            status["errors"].append(f"Invalid Google credentials JSON: {str(e)}")
    
    # Check OpenAI key
    if not os.getenv("OPENAI_API_KEY"):
        status["errors"].append("OPENAI_API_KEY not found in environment")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key.startswith('sk-') and len(api_key) > 20:
            status["openai"] = True
        else:
            status["errors"].append("Invalid OpenAI API key format")
    
    return status

@app.route('/')
def index():
    return "eBay Auto Specifics API is running!"

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Check credentials first
        cred_status = check_credentials()
        if not cred_status["google"] or not cred_status["openai"]:
            return jsonify({
                "error": "Credential issues",
                "details": cred_status["errors"]
            }), 500

        if vision_client is None:
            return jsonify({
                "error": "Google Vision client not initialized",
                "details": "Check server logs for initialization errors"
            }), 500

        data = request.get_json()
        print("📥 Received request data:", data)
        
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        image_url = data.get('imageUrl')
        if not image_url:
            return jsonify({"error": "No image URL provided"}), 400

        print(f"🌐 Processing image URL: {image_url}")

        # Step 1: Download the image
        print("⬇️ Downloading image...")
        img_response = requests.get(image_url)
        if not img_response.ok:
            return jsonify({"error": f"Failed to download image: {img_response.status_code}"}), 400
            
        image = vision.Image(content=img_response.content)
        print("✅ Image downloaded successfully")

        # Step 2: Detect labels
        print("🔍 Calling Vision API...")
        response = vision_client.label_detection(image=image)
        labels = [label.description for label in response.label_annotations]
        print(f"🏷️ Vision API labels:", labels)

        # Step 3: Generate specifics
        print("🤖 Calling OpenAI API...")
        prompt = f"""
        Based on these Vision AI labels for a clothing item: {labels}
        
        Generate a detailed JSON object describing the item. For each field, make an educated guess based on the labels and common clothing characteristics.
        
        Required fields:
        {{
          "color": "Describe the main color(s) of the item. If unclear, make a reasonable guess based on similar items",
          "collar_type": "Describe the collar style (e.g., crew neck, v-neck, polo, etc.). If not visible, use 'unknown'",
          "sleeve_type": "Describe the sleeve style (e.g., short sleeve, long sleeve, etc.)",
          "fit": "Describe how the item appears to fit (e.g., regular, loose, fitted)",
          "style": "Specify if the item is blank, graphic, or embellished",
          "pattern": "Describe any visible pattern or state 'solid' if none"
        }}

        The labels indicate this is an '{labels[4] if len(labels) > 4 else "clothing"}' item.
        Analyze these labels and provide specific, confident descriptions even if some details are implied rather than explicitly stated.
        
        Respond ONLY with the JSON object, no additional text.
        """
        
        try:
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in analyzing clothing items. Always provide detailed, specific responses based on available information and common clothing characteristics."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=150,
                response_format={ "type": "json_object" }
            )
            
            specifics = completion.choices[0].message.content
            print(f"✨ OpenAI response: {specifics}")
            
            # Verify it's valid JSON
            try:
                json.loads(specifics)
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON response from OpenAI"}), 500
                
        except openai.AuthenticationError as e:
            print("❌ OpenAI Authentication Error:", str(e))
            return jsonify({"error": "OpenAI API key is invalid"}), 500
        except openai.APIError as e:
            print("❌ OpenAI API Error:", str(e))
            return jsonify({"error": f"OpenAI API Error: {str(e)}"}), 500
        except Exception as e:
            print("❌ Unexpected error calling OpenAI:", str(e))
            return jsonify({"error": f"Error generating specifics: {str(e)}"}), 500

        result = {
            "success": True,
            "itemSpecifics": specifics,
            "labels": labels
        }
        print("📤 Sending response:", result)
        return jsonify(result)

    except Exception as e:
        print("❌ Error in /analyze:")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# Add this route to test the API
@app.route('/test', methods=['POST'])
def test():
    return jsonify({
        "success": True,
        "message": "Test successful",
        "received": request.get_json()
    })

@app.after_request
def after_request(response):
    print(f"📨 {request.method} {request.path} -> {response.status}")
    return response

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "ok",
        "time": datetime.now().isoformat()
    })

@app.route('/status')
def status():
    cred_status = check_credentials()
    return jsonify({
        "server": "running",
        "credentials": cred_status,
        "time": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True) 