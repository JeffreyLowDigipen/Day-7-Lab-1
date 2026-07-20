from llm import ask_json
result = ask_json('Return {"status": "ok"} and nothing else.', 'go')
print(result)