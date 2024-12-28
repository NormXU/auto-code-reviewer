import time

from loguru import logger
from openai import OpenAI

from auto_reviewer.prompt_lib import CODE_REVIEW_TEMPLATE


class ChatClient:

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    @classmethod
    def from_config(cls, chat_config):
        """Create ChatClient instance from a configuration object."""
        return cls(
            api_key=chat_config.api_key,
            base_url=chat_config.base_url,
            model_name=chat_config.model_name,
        )

    def chat(self,
             messages: list[dict],
             max_tokens: int = 8192,
             temperature: float = 0,
             **kwargs):
        """Sends chat messages to OpenAI API and returns the response."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content


def review_with_llm(mr, chat_client: ChatClient):
    """Generates a code review based on the changes in a merge request."""
    # Attempt to retrieve changes from the merge request with retries
    success = False
    for _ in range(10):
        changes = mr.get_changes()
        if changes:
            break
        time.sleep(30)
        logger.info('Retrying to fetch the changes of the merge request...')
    else:
        logger.error('Failed to retrieve changes after 10 retries.')
        return '', success

    logger.info(f'Changes fetched: {changes}')

    # Initialize strings to store added, changed, and deleted code
    added_code, changed_code, deleted_code = '', '', ''

    # Process the changes and categorize them
    for change in changes:
        if change['new_file']:
            added_code += f"- Added file {change['new_path']}\nContent:\n```\n{change['diff']}\n```\n\n"
        elif change['deleted_file']:
            deleted_code += f"- Deleted file {change['old_path']}\nContent:\n```\n{change['diff']}\n```\n\n"
        elif change['renamed_file']:
            logger.info(
                f"Renamed file {change['old_path']} -> {change['new_path']}. No review provided."
            )
        else:
            file_content = mr.get_file_content(change['new_path'])
            changed_code += (
                f"- Modified file {change['new_path']}\nChanges:\n```\n{change['diff']}\n```\n"
                f'Complete content after changes:\n```\n{file_content}\n```\n\n'
            )

    # Format the review content using the template
    content = CODE_REVIEW_TEMPLATE.format(
        title=mr.title,
        description=mr.description,
        added_code=added_code,
        changed_code=changed_code,
        deleted_code=deleted_code,
    )

    logger.info(f'Generated review content: {content}')

    # Send the review content to the LLM for feedback
    comment = chat_client.chat(messages=[{'role': 'user', 'content': content}])
    success = True

    return comment, success
