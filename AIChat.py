import streamlit as st
from groq import Groq

# Create Groq client
client = Groq(api_key="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")

def generate_questions(num_questions=5):
    questions = []
    for _ in range(num_questions):
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
    return questions

def check_answers(questions, user_answers):
    correct_answers = []
    explanations = []
    
    for idx, (question, user_answer) in enumerate(zip(questions, user_answers)):
        prompt_question = f"Question: {question}\nMy answer: {user_answer}\nIf the answer is correct, output 'Correct', else output 'Incorrect' and provide the correct answer."
        
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
        # Determine if the answer is correct
        if "Correct" in outcome:
            correct_answers.append("Correct")
            explanations.append("No explanation needed.")  # Placeholder for explanations
        else:
            correct_answer = "Unknown"
            explanation = ""

            try:
                # Attempt to parse the correct answer from the AI's response
                if "The correct answer is" in outcome:
                    correct_answer = outcome.split("The correct answer is ")[1].strip().split(".")[0]
                correct_answers.append(correct_answer.strip())
                explanations.append(outcome.strip())  # Store the full explanation
            except Exception as e:
                correct_answers.append(correct_answer)  # Append the default value
                explanations.append("No explanation available.")  # Default explanation
    
    return correct_answers, explanations

# Streamlit application
def main():
    st.title("Quiz Game")
    
    if 'questions' not in st.session_state:
        st.session_state.questions = generate_questions()
        st.session_state.user_answers = []
        st.session_state.current_question_idx = 0
        st.session_state.correct_answers = []
        st.session_state.explanations = []
    
    questions = st.session_state.questions

    # Show the current question
    if st.session_state.current_question_idx < len(questions):
        question = questions[st.session_state.current_question_idx]
        st.write(f"**Question {st.session_state.current_question_idx + 1}:** {question}")
        
        # Input for the answer
        answer = st.radio("Choose your answer:", options=["A", "B", "C", "D"])

        if st.button("Submit Answer"):
            if answer:
                st.session_state.user_answers.append(answer)
                correct_answers, explanations = check_answers(questions, st.session_state.user_answers)

                # Update state
                st.session_state.correct_answers = correct_answers
                st.session_state.explanations = explanations

                # Move to the next question
                st.session_state.current_question_idx += 1

    # When all questions are answered
    if st.session_state.current_question_idx == len(questions):
        st.write("### Game Over!")
        for idx, (user_answer, correct_answer) in enumerate(zip(st.session_state.user_answers, st.session_state.correct_answers)):
            st.write(f"**Question {idx + 1}:** Your answer: {user_answer}, Correct answer: {correct_answer}")

        # Calculate accuracy
        correct_count = sum(1 for answer in st.session_state.correct_answers if answer == "Correct")
        total_questions = len(questions)
        accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        st.write(f"Your accuracy: {correct_count}/{total_questions} ({accuracy:.2f}%)")

        # Option to see explanations for incorrect answers
        if st.button("See Explanations for Incorrect Answers"):
            for idx, (user_answer, correct_answer) in enumerate(zip(st.session_state.user_answers, st.session_state.correct_answers)):
                if user_answer != correct_answer:
                    st.write(f"**Explanation for Question {idx + 1}:** {st.session_state.explanations[idx]}")

if __name__ == "__main__":
    main()
