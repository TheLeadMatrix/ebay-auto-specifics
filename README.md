# eBay Auto Specifics

A Chrome extension that automatically fills eBay item specifics using AI vision and language models.

## Features

- Automatically detects product images on eBay listing pages
- Uses Google Cloud Vision API to analyze images
- Uses OpenAI GPT to generate item specifics
- Automatically fills eBay form fields
- Supports multiple item categories

## Setup

### Server Setup

1. Clone this repository
2. Set up your environment variables in Replit:
   - `GOOGLE_CREDENTIALS`: Your Google Cloud service account JSON
   - `OPENAI_API_KEY`: Your OpenAI API key
3. Install requirements: `pip install -r server/requirements.txt`
4. Run the server: `python server/main.py`

### Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` folder from this repository

## Usage

1. Go to an eBay listing page
2. Click the extension icon
3. The extension will automatically:
   - Find the main product image
   - Analyze it using AI
   - Fill in the item specifics fields

## Development

- Server code is in `server/`
- Extension code is in `extension/`
- Development roadmap in `docs/roadmap.md`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License