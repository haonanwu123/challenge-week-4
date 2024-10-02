import streamlit as st
from groq import Groq
from pygame import mixer
mixer.init()
import re

# Initialize Groq client
client = Groq(api_key="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")  # Replace with your actual API key

def generate_questions(num_questions=5):
    """
    Generates a list of multiple-choice questions using the Groq API.
    """
    questions = []
    for _ in range(num_questions):
        prompt = "Ask a multiple choice question about history, science, or pop culture. Provide options A, B, C, D."
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        
        question = response.choices[0].message.content.strip()
        questions.append(question)
    return questions

def is_correct(question, user_answer):
    """
    Checks if the user's answer is correct.
    Returns a tuple (is_correct: bool, correct_answer: str).
    """
    prompt = (
        f"Question: {question}\n"
        f"My answer: {user_answer}\n"
        f"If the answer is correct, output 'Correct'. "
        f"If incorrect, output 'Incorrect' and provide the correct answer."
    )
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )
    
    outcome = response.choices[0].message.content.strip()
    
    if "Correct" in outcome:
        return True, "Correct"
    else:
        # Attempt to extract the correct answer
        correct_answer = "Unknown"
        try:
            if "The correct answer is" in outcome:
                correct_answer = outcome.split("The correct answer is ")[1].split(".")[0].strip()
            elif "the correct answer is" in outcome:
                correct_answer = outcome.split("the correct answer is ")[1].split(".")[0].strip()
            else:
                # Handle other possible formats
                correct_answer = outcome.split(":")[1].split("\n")[0].strip()
        except IndexError:
            correct_answer = "Unknown"
        
        return False, correct_answer

def get_explanation(question, correct_answer):
    """
    Retrieves a detailed explanation for the correct answer.
    """
    prompt = (
        f"Question: {question}\n"
        f"The correct answer is: {correct_answer}.\n"
        f"Please provide a detailed explanation for why this is the correct answer."
    )
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )
    
    explanation = response.choices[0].message.content.strip()
    return explanation

def main():
    st.title("📚 Quiz Game")

    # Initialize session state variables
    if "questions" not in st.session_state:
        st.session_state.questions = generate_questions()
        st.session_state.user_answers = []
        st.session_state.correctness = []  # Stores "Correct" or the correct answer
        st.session_state.explanations = {}  # Stores explanations for incorrect answers
        st.session_state.current_question_idx = 0

    questions = st.session_state.questions

    st.write("Welcome to the Quiz Game! Answer the following multiple-choice questions:")

    # Display all previously answered questions
    for idx in range(st.session_state.current_question_idx):
        question = questions[idx]
        user_answer = st.session_state.user_answers[idx]
        correctness = st.session_state.correctness[idx]

        st.markdown(f"**Question {idx + 1}:** {question}")
        st.markdown(f"Your answer: **{user_answer}**, Correct answer: **{correctness}**")

        if correctness != "Correct":
            # Use an expander to show explanations when available
            if idx in st.session_state.explanations:
                with st.expander(f"Explanation for Question {idx + 1}"):
                    st.write(st.session_state.explanations[idx])

    # Display the current question
    if st.session_state.current_question_idx < len(questions):
        current_idx = st.session_state.current_question_idx
        current_question = questions[current_idx]

        st.markdown(f"**Question {current_idx + 1}:** {current_question}")

        # Extract options from the question text
        options = re.findall(r"[A-D]\)\s.*", current_question)
        if not options:
            st.error("Error parsing the question options. Please check the question format.")
            st.stop()
        
        options = [opt.split(")", 1)[1].strip() for opt in options]
        options = [opt for opt in options if opt]  # Remove empty strings

        # Ensure there are exactly 4 options
        if len(options) != 4:
            st.error("Each question must have exactly four options (A, B, C, D).")
            st.stop()

        # Map options back to their labels
        option_labels = ["A", "B", "C", "D"]
        option_dict = dict(zip(option_labels, options))

        # Radio button for selecting an answer
        selected_option = st.radio(
            "Choose your answer:",
            options=option_labels,
            index= None,
            format_func=lambda x: f"{x}) {option_dict[x]}"
        )

        if st.button("Submit Answer"):
            if selected_option:
                sound = mixer.Sound("audio/submit.mp3")
                sound.play()
                
                # Record the user's answer
                st.session_state.user_answers.append(selected_option)

                # Check if the answer is correct
                correct, correct_answer = is_correct(current_question, selected_option)
                if correct:
                    st.session_state.correctness.append("Correct")
                else:
                    st.session_state.correctness.append(correct_answer)
                    idx = st.session_state.current_question_idx
                    if idx not in st.session_state.explanations:
                        # Fetch explanation
                        explanation = get_explanation(questions[idx], correct_answer)
                        st.session_state.explanations[idx] = explanation

                # Move to the next question
                st.session_state.current_question_idx += 1
                st.rerun()
                
        if selected_option:
            sound = mixer.Sound("audio/option.mp3")
            sound.play()

    # After all questions are answered
    if st.session_state.current_question_idx == len(questions):
        sound = mixer.Sound("audio/end-game.mp3")
        sound.play()
        st.markdown("### 🎉 Game Over!")
        correct_count = st.session_state.correctness.count("Correct")
        total_questions = len(questions)
        accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0

        st.markdown(f"**Your accuracy:** {correct_count}/{total_questions} ({accuracy:.2f}%)")

        st.markdown("**Thank you for playing!**")

if __name__ == "__main__":
    main()
