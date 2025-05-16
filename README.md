# What is this?

A tiny Votiro Slackbot that lets users release blocked attachments.

# How do I use this?

There is a single command that can be invoked with `/release_attachment`. A modal will open, asking for the Correlation ID of a blocked attachment(s). The correlation ID can be found in the default block noticed provided by Votiro. Given a valid correlation ID, the bot will release the withheld attachments to the original recipient (assuming there is only 1 valid release candidate).

NOTE: In its curent iteration, there is a limitation that it can only release files if there is only one valid release candidate/recipient. If multiple are present, nothing will be released. Manual release will be required in such a case.

# How do I set it up

The bot uses socket mode, so no external access is necessary. Some other prerequisites are API key's that you'll need to make it all work

### Requirements:

- Slack Bot OATH Key
- Slack APP Key
- Votiro Service Token Secret
- An audit channel (where the bot will notify of releases)
- A slack group, including the name of the group, that needs to be notified of releases

### Setup:

1. Get a server/machine that can run indefinitely
2. Install python and set up a folder to hold the bot and virtual environment
3. Create virtual environment `python -m venv /path/to/venv` and source it `source /path/to/venv/bin/activate`
4. Install the requirements with `pip -r requirements.txt` (with the virtual environment sourced)
5. Create a .env file inside the same directory to hold the above-mentioned keys and variables, as well as your votiro address
6. Adjust the included service file to your needs
