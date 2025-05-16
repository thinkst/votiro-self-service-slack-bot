# What is this?

This is a simple self-service Slack bot that opens a modal on the /release_attachment slash command that requires a single input; the Correlation ID that Votiro provides for a blocked attachment.

# How do I use this?

Getting this up and running is pretty simple; since we're in socket mode, all you need is a machine with an internet connection (and access to python). Some other prerequisites are API key's that you'll need to make it all work

### Requirements:

- Slack Bot OATH Key
- Slack APP Key
- Votiro Service Token Secret

### Setup:

1. Get a server/machine that can run indefinitely
2. Install python and set up a folder to hold the bot and virtual environment
3. Create virtual environment and install the requirements with `pip -r requirements.txt` (with the virtual environment sourced)
4. Create a .env file inside the same directory to hold the 3 above-mentioned keys as well as your votiro address
5. Adjust the included service file to your needs
