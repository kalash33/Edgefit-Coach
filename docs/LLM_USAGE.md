# LLM Handler Usage Instructions

## Simple Usage

This is the easiest way to use the LLM handler anywhere in your project:

```python
from llm_handler import ask_llm, is_error_response

# Ask the LLM anything
response = ask_llm("Your prompt here")
print(f"{response}")
```

## Examples

### Basic Usage
```python
from llm_handler import ask_llm

response = ask_llm("What is good posture?")
print(f"{response}")
```

### With Error Checking
```python
from llm_handler import ask_llm, is_error_response

response = ask_llm("Give me a health tip")

if is_error_response(response):
    print(f"Error: {response}")
else:
    print(f"LLM says: {response}")
```

### Store in Variable (No Prints)
```python
from llm_handler import ask_llm, is_error_response

# Get response silently
answer = ask_llm("What should I eat for breakfast?")

# Use the response in your code
if not is_error_response(answer):
    breakfast_suggestion = answer
    # Process breakfast_suggestion as needed
```

### Multiple Questions
```python
from llm_handler import ask_llm, is_error_response

questions = [
    "What is good posture?",
    "How much water should I drink?",
    "What's a simple desk exercise?"
]

for question in questions:
    response = ask_llm(question)
    if not is_error_response(response):
        print(f"Q: {question}")
        print(f"A: {response}\n")
```

## Requirements

- Make sure `config.yaml` is in your project directory
- Install required packages: `pip install requests pyyaml`

## Error Handling

Responses starting with ❌ indicate errors. Use `is_error_response()` to check:

```python
response = ask_llm("Your question")
if is_error_response(response):
    # Handle error
    print("Something went wrong!")
else:
    # Use the response
    print(response)
```

That's it! Just import and use `ask_llm("your prompt")` anywhere in your code. 