import requests
import json
import re

ANTHROPIC_API_KEY = "" # enter your Anthropic API key here

#@title Run this to prep the main functions

def generate_candidate_prompts(task, prompt_example, response_example):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": 'claude-3-opus-20240229',
        "max_tokens": 4000,
        "temperature": .5,
        "system": """<task>Given an example training sample, create seven additional samples for the same task that are even better. Each example should contain a <prompt> and a <response>.</task>

<rules>
1. Ensure the new examples are diverse and unique from one another.
2. They should all be perfect. If you make a mistake, this system won't work.
</rules>

Respond in this format:
<response_format>
<example_one>
<prompt>
PUT_PROMPT_HERE
</prompt>
<response>
PUT_RESPONSE_HERE
</response>
</example_one>

<example_two>
<prompt>
PUT_PROMPT_HERE
</prompt>
<response>
PUT_RESPONSE_HERE
</response>
</example_two>

...
</response_format>""",
        "messages": [
            {"role": "user", "content": f"""<training_task>{task}</training_task>

<prompt_example>
{prompt_example}
</prompt_example>

<response_example>
{response_example}
</response_example>"""},
        ]
    }


    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    print("response:" , response)
    response_text = response.json()['content'][0]['text']

    # Parse out the prompts and responses
    prompts_and_responses = []
    examples = re.findall(r'<example_\w+>(.*?)</example_\w+>', response_text, re.DOTALL)
    for example in examples:
        prompt = re.findall(r'<prompt>(.*?)</prompt>', example, re.DOTALL)[0].strip()
        response = re.findall(r'<response>(.*?)</response>', example, re.DOTALL)[0].strip()
        prompts_and_responses.append({'prompt': prompt, 'response': response})

    return prompts_and_responses

def generate_system_prompt(task, prompt_examples):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": 'claude-3-opus-20240229',
        "max_tokens": 1000,
        "temperature": .5,
        "system": """<your_role>Given a user-description of their <task> a set of prompt / response pairs (it'll be in JSON for easy reading) for the types of outputs we want to generate given inputs, write a fantastic system prompt that describes the task to be done perfectly.</your_role>

<rules>
1. Do this perfectly.
2. Respond only with the system prompt, and nothing else. No other text will be allowed.
</rules>

Respond in this format:
<system_prompt>
WRITE_SYSTEM_PROMPT_HERE
</system_prompt>""",
        "messages": [
            {"role": "user", "content": f"""<task>{task}</task>

<prompt_response_examples>
{str(prompt_examples)}
</prompt_response_examples>"""},
        ]
    }


    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)

    response_text = response.json()['content'][0]['text']

    # Parse out the prompt
    system_prompt = response_text.split('<system_prompt>')[1].split('</system_prompt>')[0].strip()

    return system_prompt

def test_haiku(generated_examples, prompt_example, system_prompt):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    messages = []

    for example in generated_examples:
      messages.append({"role": "user", "content": example['prompt']})
      messages.append({"role": "assistant", "content": example['response']})

    messages.append({"role": "user", "content": prompt_example.strip()})

    data = {
        "model": 'claude-3-haiku-20240307',
        "max_tokens": 2000,
        "temperature": .5,
        "system": system_prompt,
        "messages": messages,
    }


    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)

    response_text = response.json()['content'][0]['text']

    return response_text

def run_haiku_conversion_process(task, prompt_example, response_example):

    print('Generating the prompts / responses...')
    # Generate candidate prompts
    generated_examples = generate_candidate_prompts(task, prompt_example, response_example)

    print('Prompts / responses generated. Now generating system prompt...')

    # Generate the system prompt
    system_prompt = generate_system_prompt(task, generated_examples)

    print('System prompt generated:', system_prompt)


    print('\n\nTesting the new prompt on Haiku, using your input example...')
    # Test the generated examples and system prompt with the Haiku model
    haiku_response = test_haiku(generated_examples, prompt_example, system_prompt)

    print('Haiku responded with:')
    print(haiku_response)

    print('\n\n!! CHECK THE FILE DIRECTORY, THE PROMPT IS NOW SAVED THERE !!')

    # Create a dictionary with all the relevant information
    result = {
        "task": task,
        "initial_prompt_example": prompt_example,
        "initial_response_example": response_example,
        "generated_examples": generated_examples,
        "system_prompt": system_prompt,
        "haiku_response": haiku_response
    }

    # Save the Haiku prompt to a Python file
    with open("haiku_prompt.py", "w") as file:
        file.write('system_prompt = """' + system_prompt + '"""\n\n')

        file.write('messages = [\n')
        for example in generated_examples:
            file.write('    {"role": "user", "content": """' + example['prompt'] + '"""},\n')
            file.write('    {"role": "assistant", "content": """' + example['response'] + '"""},\n')

        file.write('    {"role": "user", "content": """' + prompt_example.strip() + '"""}\n')
        file.write(']\n')

    return result

task = "refactoring complex code"

prompt_example = """def calculate_total(prices, tax, discount, shipping_fee, gift_wrap_fee, membership_discount):

    total = 0

    for i in range(len(prices)):

        total += prices[i]

    if membership_discount != 0:

        total = total - (total * (membership_discount / 100))

    if discount != 0:

        total = total - (total * (discount / 100))

    total = total + (total * (tax / 100))

    if total < 50:

        total += shipping_fee

    else:

        total += shipping_fee / 2

    if gift_wrap_fee != 0:

        total += gift_wrap_fee * len(prices)

    if total > 1000:

        total -= 50

    elif total > 500:

        total -= 25

    total = round(total, 2)

    if total < 0:

        total = 0

    return total"""

response_example = """def calculate_total(prices, tax_rate, discount_rate, shipping_fee, gift_wrap_fee, membership_discount_rate):

    def apply_percentage_discount(amount, percentage):

        return amount * (1 - percentage / 100)

    def calculate_shipping_fee(total):

        return shipping_fee if total < 50 else shipping_fee / 2

    def apply_tier_discount(total):

        if total > 1000:

            return total - 50

        elif total > 500:

            return total - 25

        return total

    subtotal = sum(prices)

    subtotal = apply_percentage_discount(subtotal, membership_discount_rate)

    subtotal = apply_percentage_discount(subtotal, discount_rate)



    total = subtotal * (1 + tax_rate / 100)

    total += calculate_shipping_fee(total)

    total += gift_wrap_fee * len(prices)



    total = apply_tier_discount(total)

    total = max(0, round(total, 2))



    return total"""

result = run_haiku_conversion_process(task, prompt_example, response_example)