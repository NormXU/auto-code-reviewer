
# Auto Code Reviewer
This repo let LLM review your Merge Requests.

## Workflow:
1. Receive a webhook from Gitlab Action.
2. Extract necessary information, such as project name, merge request ID, etc.
3. Send the information to a LLM provider and let it generate a review.
4. Submit the generated review on the merge request.

## Setup

### 1. **Configure API Key and Project Details**

Before running the Auto Code Reviewer, you need to set up the configuration file `reviewer-config.yaml` with your API keys and GitLab project details.

```yaml
llm:
  oai:
    model_name: gpt-4o-2024-05-13  # Specify the model you want to use, e.g., GPT-4
    api_key: <your-api-key>  # Replace with your OpenAI API key
    base_url: ~  # Optional, default is the OpenAI API endpoint

  claude:
    model: ~  # If using Claude, specify the model here
    api_key: ~  # Replace with your Claude API key
    base_url: ~  # Optional, specify Claude's API base URL
    
  ...

projects:
  test-project:
    url: https://dev.example.com  # The URL of your GitLab project
    private_token: <your-project-token>  # Replace with your GitLab project's private token
```

### 2. **Obtain API Keys and Tokens**

- **For GitLab Private Token:**
  - Log into your GitLab account.
  - Go to **Settings** > **Access Tokens**.
  - Create a new token with at least the **read_repository** scope.
  - Replace `<your-project-token>` in the config file with this private token.

### 3. **Start the Application**

Once your configuration is complete, you can run the Auto Code Reviewer application.

```bash
python main.py
```


## Usage

open an MR and @ the reviewer in the comments or MR overview:

```
@reviewer-bot
```

The default LLM provider is set to oai.

You can also specify a different LLM provider, like:

```
@reviewer-bot:claude
```
