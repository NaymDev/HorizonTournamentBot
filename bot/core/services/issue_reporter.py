import requests
import datetime
import traceback
import hashlib
from bot.config import CONFIG

import time
import jwt
from cryptography.hazmat.primitives import serialization

def get_github_app_token(app_id: str, installation_id: str, private_key_path: str) -> str:
    """
    Generate a GitHub App Installation Access Token.

    :param app_id: GitHub App ID (as string or int)
    :param installation_id: Installation ID for the app on a specific repo/org
    :param private_key_path: Path to the .pem file downloaded from GitHub
    :return: Installation access token (string)
    :raises: RuntimeError if the token cannot be fetched
    """

    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + (10 * 60),
        "iss": app_id
    }

    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    response = requests.post(url, headers=headers)

    if response.status_code != 201:
        raise RuntimeError(f"Failed to get access token: {response.status_code} {response.text}")

    return response.json()["token"]


_recent_errors = set()


def generate_signature(error_text: str) -> str:
    return hashlib.md5(error_text.encode()).hexdigest()


def format_exception(ctx=None, interaction=None, error=None, source="unknown"):
    if isinstance(error, str):
        tb_str = error
    else:
        tb_str = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

    signature = generate_signature(tb_str)
    if signature in _recent_errors:
        return None, None, None

    _recent_errors.add(signature)

    title = f"[Unhandled Exception] {source} - {type(error).__name__ if not isinstance(error, str) else 'Exception'}"

    if ctx:
        user = ctx.author
        message_content = f"`{ctx.message.content}`"
        channel = str(ctx.channel)
        guild = ctx.guild.name if ctx.guild else "DM or N/A"
    elif interaction:
        user = interaction.user
        message_content = f"`/{interaction.command.name}`"
        channel = str(interaction.channel)
        guild = interaction.guild.name if interaction.guild else "DM or N/A"
    else:
        user = "Unknown"
        message_content = "N/A"
        channel = "N/A"
        guild = "N/A"

    user_info = f"{user} (ID: {getattr(user, 'id', 'N/A')})"


    body = f"""
**Time**: {datetime.datetime.utcnow().isoformat()} UTC  
**User**: {user_info}  
**Command/Event**: {message_content}  
**Channel**: {channel}  
**Guild**: {guild}  
**Source**: `{source}`

<details>
<summary>Traceback</summary>

```
{tb_str}
```

</details>
"""

    return title, body, signature


def create_github_issue(title, body):
    url = f"https://api.github.com/repos/{CONFIG.issues.github_repository}/issues"
    headers = {
        "Authorization": f"token {get_github_app_token(
            CONFIG.issues.github_app_id,
            CONFIG.issues.github_installation_id,
            CONFIG.issues.github_private_key_path
        )}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"title": title, "body": body, "labels": CONFIG.issues.github_labels}
    response = requests.post(url, headers=headers, json=payload)
    return response.ok


async def report_unhandled_exception(
    ctx=None, interaction=None, error=None, source="unknown"
):
    title, body, signature = format_exception(ctx, interaction, error, source)
    if title and body:
        success = create_github_issue(title, body)
        if not success:
            print("Failed to submit issue to GitHub.")
