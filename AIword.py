from groq import Groq

# Create Groq client
client = Groq(api_key="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")

def play_game():
    # List to store questions, user answers, correct answers, and explanations
    questions = []
    user_answers = []
    correct_answers = []
    explanations = []

    # Generate 5 multiple-choice questions
    for q in range(5):
        prompt_question_with_context = "Ask a multiple choice question about history, science, or pop culture. Provide options A, B, C, D."

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt_question_with_context,
                }
            ],
            model="llama3-8b-8192",
        )

        # Get the question and options
        prev_question = chat_completion.choices[0].message.content
        questions.append(prev_question)

    # Ask the user questions
    for idx, question in enumerate(questions, 1):
        print(f"Question {idx}: {question}")

        # Get user answer
        ans = input("Please enter your answer (A, B, C, or D): ").strip().upper()
        user_answers.append(ans)  # Store user answer

        prompt_question = f"Question: {question}\nMy answer: {ans}\nIf the answer is correct, output 'Correct', else output 'Incorrect' and provide the correct answer."

        # Check the correctness of the answer
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
        
        # Log the raw outcome for debugging
        print(f"Debug: Raw outcome from AI for question {idx}: {outcome}")

        # Determine if the answer is correct
        if "Correct" in outcome:
            correct_answers.append("Correct")
            explanations.append("No explanation needed.")  # Placeholder for explanations
        else:
            # Initialize correct_answer variable
            correct_answer = "Unknown"
            explanation = ""
            
            try:
                # Attempt to parse the correct answer from the AI's response
                if "The correct answer is" in outcome:
                    correct_answer = outcome.split("The correct answer is ")[1].strip().split(".")[0]
                    explanation = outcome  # Capture the full outcome for later use
                elif "your answer is:" in outcome:
                    # Handle another unexpected phrasing
                    correct_answer = outcome.split("your answer is:")[1].strip().split("\n")[0]
                    explanation = outcome
                elif "your answer is" in outcome:
                    # Capture multiple variations of responses
                    parts = outcome.split("your answer is")
                    if len(parts) > 1:
                        correct_answer = parts[1].strip().split(".")[0]
                        explanation = outcome
                else:
                    raise ValueError("Unexpected format")
                
                correct_answers.append(correct_answer.strip())
                explanations.append(explanation.strip())  # Store the full explanation
            except (IndexError, ValueError) as e:
                print(f"Warning: Unable to parse the correct answer due to unexpected format: {e}")
                correct_answers.append(correct_answer)  # Append the default value
                explanations.append("No explanation available.")  # Default explanation

    # After all questions, print results
    print("\n--- Game Over ---")
    print("Your answers:")
    for idx, ans in enumerate(user_answers, 1):
        print(f"Question {idx}: Your answer: {ans}, Correct answer: {correct_answers[idx - 1]}")

    # Check the incorrect answers
    incorrect_indices = [idx + 1 for idx, answer in enumerate(correct_answers) if answer != "Correct"]
    correct_count = len(correct_answers) - len(incorrect_indices)
    total_questions = len(questions)
    accuracy = (correct_count / total_questions) * 100

    print(f"\nYour accuracy: {correct_count}/{total_questions} ({accuracy:.2f}%)")

    # Ask if the user wants explanations for incorrect answers
    if incorrect_indices:
        questions_str = ', '.join([f"Q{idx}" for idx in incorrect_indices])
        need_explanation = input(f"Would you like explanations for the incorrect answers? (Questions: {questions_str}) (yes/no): ").strip().lower()

        if need_explanation == 'yes':
            explained_indices = []  # Keep track of which questions have been explained
            while len(explained_indices) < len(incorrect_indices):
                question_to_explain = input(f"Which question do you want an explanation for? (e.g., {questions_str}): ").strip().upper()
                if question_to_explain.startswith("Q") and question_to_explain[1:].isdigit():
                    question_index = int(question_to_explain[1:]) - 1  # Convert to zero-based index
                    if question_index + 1 in incorrect_indices and (question_index + 1) not in explained_indices:
                        # Provide the explanation for the incorrect question
                        explanation = explanations[question_index]
                        print(f"Explanation for {question_to_explain}: {explanation}")

                        explained_indices.append(question_index + 1)  # Mark this question as explained
                    else:
                        print(f"You can only ask for explanations for: {questions_str}")
                else:
                    print("Please enter a valid question number (e.g., Q1, Q2, etc).")
    else:
        print("No incorrect answers, great job!")

    print("Thank you for playing!")

if __name__ == "__main__":
    play_game()
