from groq import Groq
client = Groq(api_key="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")
prompt_question_with_context = "Ask a multiple choice question about history, science or pop culture"

for q in range(5):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_question_with_context,
            }
        ],
        model="llama3-8b-8192",
    )

    prev_question = chat_completion.choices[0].message.content
    print(chat_completion.choices[0].message.content)

    ans = input()

    prompt_question = f"Question: {prev_question}\n My answer: {ans}\n If the answer is correct, output Correct, else output Incorrect and nothing else"

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_question,
            }
        ],
        model="llama3-8b-8192",
    )

    outcome = chat_completion.choices[0].message.content
    print(outcome)

    if "incorrect" in outcome.lower():
        print("Game over")
        exit()

print("You won!!!!!!!!")
