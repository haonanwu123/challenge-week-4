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
client = Groq(api_key=os.environ["GROQ_API_KEY"])

mixer.init()


def is_valid_topic(topic):
    """
    Validate if the topic is coherent using Groq API
    Returns: tuple (is_valid, message)
    """
    prompt = f"""
    Analyze if the following topic is a coherent subject for a quiz: "{topic}"
    Only respond with either "VALID" if it's a real topic (like "history", "python programming", "ancient egypt", etc.)
    or "INVALID" if it's gibberish, random characters, or not a real topic.
    Response:
    """

    try:
        completion = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=10
        )
        response = completion.choices[0].message.content.strip()
        return response == "VALID", "" if response == "VALID" else "Please enter a real topic."
    except Exception as e:
        return False, f"Error validating topic: {str(e)}"


def get_valid_custom_topic():
    """Get and validate topic input from user"""
    topic = st.text_input("Enter your quiz topic:")

    if topic:
        # Basic preprocessing
        topic = topic.strip()

        # Basic client-side validation
        if len(topic) < 2:
            st.error("Topic must be at least 2 characters long.")
            return None

        if re.match(r'^[0-9\W]+$', topic):  # Only numbers or special characters
            st.error("Topic cannot be just numbers or special characters.")
            return None

        is_valid, message = is_valid_topic(topic)

        if is_valid:
            return topic
        else:
            st.error(message)
            return None

def generate_topics(num_words):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Your output MUST consist of EXACTLY {num_words} different topics for quiz, separated ONLY by a newline. Don't write something like Here is the output: before, just the words, not numerated",
            }
        ],
        model="gemma2-9b-it",
    )
    array = response.choices[0].message.content.split("\n")
    return array[:num_words]


def create_frames_and_plot(values, num_segments):
    # Create the initial pie chart
    fig = go.Figure()
    colors = plt.cm.rainbow(np.linspace(0, 1, num_segments))
    colors = [tuple(c) for c in colors]

    # Add the initial pie chart
    fig.add_trace(
        go.Pie(
            labels=values,
            textinfo="label",
            hoverinfo="label",
            marker=dict(colors=colors, line=dict(width=0)),
            textfont=dict(size=5),
            showlegend=False,
            hole=0.05,
            sort=False,  # Disable sorting to keep fixed positions
            direction="clockwise",
        )
    )

    # Set the initial rotation angle
    max_rotation_angle = (lambda x: x + 1 if x % (360 // num_segments) == 0 else x)(
        random.randint(0, 1080) + 1080
    )

    # Create frames for the animation with a decelerating effect
    frames = []
    total_frames = 100
    for i in range(total_frames):
        t = i / total_frames  # Normalize the frame index to [0, 1]

        # Apply the easing function (deceleration) to the rotation angle
        angle = (1 - (1 - t) ** 3) * max_rotation_angle

        frames.append(
            go.Frame(
                data=[
                    go.Pie(
                        labels=values,
                        textinfo="label",
                        hoverinfo="label",
                        marker=dict(colors=colors, line=dict(width=0)),
                        sort=False,
                        hole=0.05,
                        direction="clockwise",
                        textfont=dict(size=5),
                        showlegend=False,
                        rotation=angle,  # Apply the new rotation angle
                    )
                ]
            )
        )

    # Update the layout to support frames and add the play button
    fig.frames = frames

    # Add an annotation to simulate the pointer/arrow at the top
    fig.add_annotation(
        x=0.5,
        y=1.03,
        showarrow=False,
        text="▼",
        font=dict(size=20, color="black"),
        xref="paper",
        yref="paper",
    )

    return fig, frames, max_rotation_angle


def generate_questions(num_questions=5):
    """
    Generates a list of multiple-choice questions using the Groq API.
    """
    questions = []
    for _ in range(num_questions):
        prompt = (
            f"Ask a multiple choice question about {st.session_state.topic}. "
            f"Provide options A, B, C, D. Make sure it's different from these "
            f"existing questions: {questions}"
        )

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )

        question = response.choices[0].message.content.strip()
        questions.append(question)
    return questions


def is_correct(question, user_answer):
    """
    Check if the user's answer is correct using Groq LLM.

    Args:
        question (str): The full question text including all answer options
        user_answer (str): User's answer (single uppercase letter A, B, C, or D)

    Returns:
        tuple (is_correct: bool, correct_answer: str)
    """

    # Create the prompt for the LLM
    prompt = f"""
    Question: {question}
    
    Please provide ONLY a single uppercase letter (A, B, C, or D) representing the correct answer. 
    Do not provide any explanation or additional text.
    """

    # Make API call to Groq
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
        temperature=0.5,
        max_tokens=1
    )

    # Extract the correct answer
    correct_answer = chat_completion.choices[0].message.content.strip()

    # Validate LLM response
    if correct_answer[0] not in ['A', 'B', 'C', 'D']:
        return False, 'Unknown'

    # Compare answers
    return user_answer == correct_answer, correct_answer


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
        st.session_state.is_sound_played = [False] * 5
        st.session_state.selected_options = [None] * 5
        st.session_state.running = False

        # Wheel properties
        num_segments = [3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30]

        st.session_state.num_topics = random.choice(num_segments)
        st.session_state.topics = generate_topics(st.session_state.num_topics)
        st.session_state.custom_topic = False
        st.session_state.topic = None

    if not st.session_state.running:
        if st.session_state.custom_topic:
            st.session_state.topic = get_valid_custom_topic()
        if st.session_state.topic:
            st.success(f"The chosen topic is {st.session_state.topic}")
            if st.button("Start the quiz"):
                sound = mixer.Sound("audio/play.mp3")
                sound.play()
                st.session_state.running = True
                st.rerun()
        elif not st.session_state.custom_topic:
            st.subheader("Spin the wheel to get a random topic for a quiz!")
            # Create the animated plot
            fig, frames, final_angle = create_frames_and_plot(
                st.session_state.topics, st.session_state.num_topics
            )

            # Display the plotly figure
            plot_placeholder = st.empty()
            plot_placeholder.plotly_chart(fig, config={"displayModeBar": False})

            # Create two columns
            col1, col2, col3 = st.columns([2, 1.2, 1])

            # Place the buttons in separate columns to align them in the same row
            with col2:
                st.write('or')
            with col3:
                if st.button("🔒 Custom topic"):
                    st.session_state.custom_topic = True
                    st.rerun()
            with col1:
                # Streamlit button to trigger animation
                if st.button("Determine the quiz topic"):
                    sound = mixer.Sound("audio/spin.mp3")
                    sound.play()

                    # Simulate frame updates for animation
                    for frame in frames:
                        fig = go.Figure(
                            data=frame.data
                        )  # Update figure with each frame's data
                        fig.add_annotation(
                            x=0.5,
                            y=1.03,
                            showarrow=False,
                            text="▼",
                            font=dict(size=20, color="black"),
                            xref="paper",
                            yref="paper",
                        )
                        plot_placeholder.plotly_chart(
                            fig, config={"displayModeBar": False}
                        )  # Render the updated figure
                        time.sleep(0.03)  # Delay to simulate animation speed

                    st.session_state.topic = st.session_state.topics[
                        st.session_state.num_topics
                        - 1
                        - (final_angle % 360) // (360 // st.session_state.num_topics)
                    ]
                    st.rerun()
    else:  # Quiz based on chosen topic
        if "questions" not in st.session_state:
            st.session_state.questions = generate_questions()
            st.session_state.start_time = time.time()
            st.session_state.elapsed_time = 0

        questions = st.session_state.questions

        st.write(
            "Welcome to the Quiz Game! Answer the following multiple-choice questions:"
        )

        # Display all previously answered questions
        for idx in range(st.session_state.current_question_idx):
            question = questions[idx]
            user_answer = st.session_state.user_answers[idx]
            correctness = st.session_state.correctness[idx]

            if correctness == "Correct":
                answer_text = f":green[{user_answer}]"
                correctness_text = f":green[{correctness}]"
            else:
                answer_text = f":red[{user_answer}]"
                correctness_text = f":orange[{correctness}]"

            st.markdown(f"**Question {idx + 1}:** {question}")
            st.markdown(
                f"Your answer: **{answer_text}**, Correct answer: **{correctness_text}**"
            )

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
                st.error(
                    "Error parsing the question options. Please check the question format."
                )
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
                index=None,
                format_func=lambda x: f"{x}) {option_dict[x]}",
            )

            if st.button("Submit Answer"):
                if not selected_option:
                    st.warning("Please select an answer before submitting.")
                else:
                    sound = mixer.Sound("audio/submit.mp3")
                    sound.play()

                    # Record the user's answer
                    st.session_state.user_answers.append(selected_option)

                    # Check if the answer is correct
                    correct, correct_answer = is_correct(
                        current_question, selected_option
                    )
                    if correct:
                        st.session_state.correctness.append("Correct")
                    else:
                        st.session_state.correctness.append(correct_answer)
                        if current_idx not in st.session_state.explanations:
                            # Fetch explanation
                            explanation = get_explanation(
                                questions[current_idx], correct_answer
                            )
                            st.session_state.explanations[current_idx] = explanation

                    # Move to the next question
                    st.session_state.current_question_idx += 1
                    st.rerun()

            if selected_option and (not st.session_state.is_sound_played[
                current_idx - 1] or selected_option != st.session_state.selected_options):
                st.session_state.is_sound_played[current_idx - 1] = True
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
            accuracy = (
                (correct_count / total_questions) * 100 if total_questions > 0 else 0
            )

            st.markdown(
                f"**Your accuracy:** {correct_count}/{total_questions} ({accuracy:.2f}%)"
            )
            st.markdown(f"**Total time: {st.session_state.elapsed_time:.1f} seconds**")
            st.markdown("**Thank you for playing!**")

        if st.session_state.running:
            st.session_state.elapsed_time = time.time() - st.session_state.start_time
            st.write(f"Elapsed time: {st.session_state.elapsed_time:.1f} seconds")
            time.sleep(0.1)
            st.rerun()


if __name__ == "__main__":
    main()
