CODE_REVIEW_TEMPLATE = """
## Task

You are an excellent algorithm engineer with strict standards for code quality. Your task is to carefully review the changes in the merge request, with a focus on identifying potential risks that the code may introduce.

## Review Content

### Merge Request Information

- Title of the merge request: {title}

- Description of the merge request: {description}

### Added Code

{added_code}

### Changed Code

{changed_code}

### Deleted Code

{deleted_code}

## Review Feedback

Please provide your review feedback based on the above content. Your feedback must be concise and clear, pointing out the issues and offering suggestions for improvement. If there are no issues, you can provide a positive evaluation directly.

Here are your review comments:
"""
