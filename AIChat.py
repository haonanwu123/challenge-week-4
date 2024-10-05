import streamlit as st
from groq import Groq
from pygame import mixer
import re
import os
from dotenv import load_dotenv
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import time
import random

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ['GROQ_API_KEY'])

mixer.init()

def generate_topics(num_words):
    response = client.chat.completions.create(
        messages=[{"role": "user",
                   "content": f"Your output MUST consist of EXACTLY {num_words} different topics for quiz, separated ONLY by a newline. Don't write something like Here is the output: before, just the words, not numerated"}],
        model="gemma2-9b-it",
    )
    array = response.choices[0].message.content.split('\n')
    return array[:num_words]

def create_frames_and_plot(values, num_segments):
    # Create the initial pie chart
    fig = go.Figure()
    colors = plt.cm.rainbow(np.linspace(0, 1, num_segments))
    colors = [tuple(c) for c in colors]

    # Add the initial pie chart
    fig.add_trace(go.Pie(
        labels=values,
        textinfo='label',
        hoverinfo='label',
        marker=dict(colors=colors, line=dict(width=0)),
        textfont=dict(size=5),
        showlegend=False,
        hole=0.05,
        sort=False,  # Disable sorting to keep fixed positions
        direction='clockwise',
    ))

    # Set the initial rotation angle
    max_rotation_angle = (lambda x: x + 1 if x % (360 // num_segments) == 0 else x)(random.randint(0, 1080) + 1080)

    # Create frames for the animation with a decelerating effect
    frames = []
    total_frames = 100
    for i in range(total_frames):
        t = i / total_frames  # Normalize the frame index to [0, 1]

        # Apply the easing function (deceleration) to the rotation angle
        angle = (1 - (1 - t) ** 3) * max_rotation_angle

        frames.append(go.Frame(data=[go.Pie(
            labels=values,
            textinfo='label',
            hoverinfo='label',
            marker=dict(colors=colors, line=dict(width=0)),
            sort=False,
            hole=0.05,
            direction='clockwise',
            textfont=dict(size=5),
            showlegend=False,
            rotation=angle  # Apply the new rotation angle
        )]))

    # Update the layout to support frames and add the play button
    fig.frames = frames

    # Add an annotation to simulate the pointer/arrow at the top
    fig.add_annotation(
        x=0.5, y=1.03, showarrow=False, text="▼",
        font=dict(size=20, color='black'), xref="paper", yref="paper"
    )

    return fig, frames, max_rotation_angle

def generate_questions(num_questions=5):
    """
    Generates a list of multiple-choice questions using the Groq API.
    """
    questions = []
    for _ in range(num_questions):
        prompt = f"Ask a multiple choice question about {st.session_state.topic}. Provide options A, B, C, D."
        
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
    st.set_page_config(page_title="Quiz Game")
    st.title("📚 Quiz Game")

    # Initialize session state variables
    if "running" not in st.session_state:
        st.session_state.user_answers = []
        st.session_state.correctness = []  # Stores "Correct" or the correct answer
        st.session_state.explanations = {}  # Stores explanations for incorrect answers
        st.session_state.current_question_idx = 0
        st.session_state.is_sound_played = [False]*5
        st.session_state.selected_options = [None]*5
        st.session_state.running = False

    if "topics" not in st.session_state:
        # Wheel properties
        num_segments = [3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30]

        st.session_state.num_topics = random.choice(num_segments)
        st.session_state.topics = generate_topics(st.session_state.num_topics)
        st.session_state.topic = None

    if not st.session_state.running: # Determine the topic first
        if not st.session_state.topic:
            st.subheader("Spin the wheel to get a random topic for a quiz!")
            # Create the animated plot
            fig, frames, final_angle = create_frames_and_plot(st.session_state.topics, st.session_state.num_topics)

            # Display the plotly figure
            plot_placeholder = st.empty()
            plot_placeholder.plotly_chart(fig, config={'displayModeBar': False})

            # Streamlit button to trigger animation
            if st.button('Determine the quiz topic'):
                sound = mixer.Sound("audio/spin.mp3")
                sound.play()

                # Simulate frame updates for animation
                for frame in frames:
                    fig = go.Figure(data=frame.data)  # Update figure with each frame's data
                    fig.add_annotation(
                        x=0.5, y=1.03, showarrow=False, text="▼",
                        font=dict(size=20, color='black'), xref="paper", yref="paper"
                    )
                    plot_placeholder.plotly_chart(fig, config={'displayModeBar': False})  # Render the updated figure
                    time.sleep(0.03)  # Delay to simulate animation speed

                st.session_state.topic = st.session_state.topics[st.session_state.num_topics - 1 - (final_angle % 360) // (360 // st.session_state.num_topics)]
                st.rerun()
        else:
            st.success(f"The chosen topic is {st.session_state.topic}")
            if st.button('Start the quiz'):
                sound = mixer.Sound("audio/play.mp3")
                sound.play()
                st.session_state.running = True
                st.rerun()
    else: # Quiz based on chosen topic
        if "questions" not in st.session_state:
            st.session_state.questions = generate_questions()
            st.session_state.start_time = time.time()
            st.session_state.elapsed_time = 0
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
                        if current_idx not in st.session_state.explanations:
                            # Fetch explanation
                            explanation = get_explanation(questions[current_idx], correct_answer)
                            st.session_state.explanations[current_idx] = explanation

                    # Move to the next question
                    st.session_state.current_question_idx += 1
                    st.rerun()

            if selected_option and (not st.session_state.is_sound_played[current_idx-1] or selected_option != st.session_state.selected_options):
                st.session_state.is_sound_played[current_idx-1] = True
                st.session_state.selected_options = selected_option
                sound = mixer.Sound("audio/option.mp3")
                sound.play()

        # After all questions are answered
        if st.session_state.current_question_idx == len(questions):
            st.session_state.running = False
            sound = mixer.Sound("audio/end-game.mp3")
            sound.play()
            st.markdown("### 🎉 Game Over!")
            correct_count = st.session_state.correctness.count("Correct")
            total_questions = len(questions)
            accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0

            st.markdown(f"**Your accuracy:** {correct_count}/{total_questions} ({accuracy:.2f}%)")
            st.markdown(f"**Total time: {st.session_state.elapsed_time:.1f} seconds**")
            st.markdown("**Thank you for playing!**")

        if st.session_state.running:
            st.session_state.elapsed_time = time.time() - st.session_state.start_time
            st.write(f"Elapsed time: {st.session_state.elapsed_time:.1f} seconds")
            time.sleep(0.1)
            st.rerun()

if __name__ == "__main__":
    main()
