import re
import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

slack_oath_token = os.environ.get("SLACK_BOT_OAUTH_TOKEN", None)
slack_app_level_token = os.environ.get("SLACK_APP_TOKEN", None)
VOTIRO_BASE_URL = os.environ.get("VOTIRO_BASE_URL", None)
VOTIRO_API_KEY = os.environ.get("VOTIRO_API_KEY", None)

audit_channel = os.environ.get("SLACK_AUDIT_CHANNEL", None)
audit_group = os.environ.get("SLACK_AUDIT_GROUP", None)
audit_group_name = os.environ.get("SLACK_AUDIT_GROUP_NAME", None)

VOTIRO_RELEASE_PATH = "release/api/v1/mail"
VOTIRO_REPORT_PATH = "disarmer/api/disarmer/v4/report"

correlation_id_format = re.compile(r"\w{8}-\w{4}-\w{4}-\w{4}-\w{12}")

app = App(token=slack_oath_token)

@app.command("/release_attachment")
def open_modal(ack, body, client):
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "release_attachment",
            "title": {"type": "plain_text", "text": "Votiro Self-service"},
            "submit": {"type": "plain_text", "text": "Release"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "correlation_id",
                    "element": {"type": "plain_text_input", "action_id": "id", "placeholder": {"type": "plain_text", "text": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}},
                    "label": {"type": "plain_text", "text": "Correlation ID"},
                    "optional": False,
                },
            ],
        }
    )

@app.view("release_attachment")
def handle_release(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    correlation_id = body["view"]["state"]["values"]["correlation_id"]["id"]["value"]
    user_info = client.users_info(user=user_id)
    user_email = user_info["user"]["profile"].get("email")
    user_name = user_info["user"]["name"]
    print(f"Release request by {user_name}")

    try:
        if not correlation_id_format.match(correlation_id):
            raise ValueError(f"{correlation_id} doesn't appear be to be a valid Correlation ID. Please try again with the Correlation ID provided in the Votiro attachment blocked notice.")
        resp = requests.get(
            f"{VOTIRO_BASE_URL}/{VOTIRO_REPORT_PATH}/{correlation_id}",
            headers={
                "Authorization": f"Bearer {VOTIRO_API_KEY}",
                "Content-Type": "application/json-patch+json",
            },
        ).json()
        if resp.get("code", None) == 404:
            raise ValueError(f"{correlation_id} doesn't appear to be a Correlation ID. Please double check that you did not use the Item ID instead.")
        print(f"Mail details: {resp}")
        files_to_release = [resp["children"][i]["originalFileName"] for i in range(len(resp["children"]))]
        released_extensions = set([os.path.splitext(f)[1] for f in files_to_release])
        release_candidates = resp["extendedInfo"]["email"]["releaseCandidates"]
        recipient_addresses = [candidate["address"] for recipient in release_candidates.keys() for candidate in release_candidates[recipient]]
        sender_address = resp["extendedInfo"]["contextIdentifiers"]["from"]

        # NOTE: The Votiro API wording suggests that one can have multiple release candidates (recipients), however, in testing
        # it has not been observed. The format the release request corresponding to multiple candidates is also unknown, so for
        # now we defer to manual release should we run into this
        if not len(recipient_addresses) == 1:
            print("Multiple recipients (release candidates) found. Unable to handle")
            raise ValueError("Multiple recipient address candidates found. Cannot automatically handle this release")

        print(f"Releasing {len(files_to_release)} extension(s)")
        resp = requests.post(
            f"{VOTIRO_BASE_URL}/{VOTIRO_RELEASE_PATH}",
            headers={
                "Authorization": f"Bearer {VOTIRO_API_KEY}",
                "Content-Type": "application/json-patch+json",
            },
            json={
                "itemId": f"{correlation_id}",
                "sendAttachment": True,
                "recipients": ",".join(recipient_addresses)
            }
        )
        print(f"Release request response: {resp}")
        release_message_single = f"a \"{', '.join(released_extensions)}\" attachment sent from {sender_address} to {''.join(recipient_addresses)} ({correlation_id}) "
        attachments = [f"\"{a}\"" for a in released_extensions]
        release_message_multi = f"{len(files_to_release)} attachments ({', '.join(attachments)}) sent from {sender_address} to {''.join(recipient_addresses)} ({correlation_id}) "
        if resp.status_code == 204:
            print(f"Notifying of success")
            if len(files_to_release) == 1:
                release_message = "Released " + release_message_single
            else:
                release_message = "Released " + release_message_multi
            client.chat_postMessage(channel=user_id, text=release_message)
            client.chat_postMessage(channel=audit_channel, text=f"<@{user_name}> {release_message}")
        else:
            print(f"Notifying of failure")
            if len(files_to_release) == 1:
                release_message = "Failed to release " + release_message_single
            else:
                release_message = "Failed to release " + release_message_multi
            client.chat_postMessage(channel=user_id, text=release_message)
            client.chat_postMessage(channel=audit_channel, text=f"<@{user_name}> {release_message}. {resp.text}")
    except Exception as e:
        print(f"An exception ocurred. Sounding the alarm.")
        client.chat_postMessage(channel=audit_channel, text=f"<!subteam^{audit_group}|{audit_group_name}> An exception ocurred while handling a release request from <@{user_name}>. Could not release {correlation_id} to {user_email}: {str(e)}")
        client.chat_postMessage(channel=user_id, text=f"An exception ocurred when trying to release {correlation_id} to {user_email}. The exception was {str(e)}. <!subteam^{audit_group}|{audit_group_name}> is on it!")

if __name__ == "__main__":
    handler = SocketModeHandler(app, slack_app_level_token)
    handler.start()
