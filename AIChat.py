import streamlit as st
from groq import Groq
from pygame import mixer
import os
import re
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import time
import random
from dotenv import load_dotenv

# Load environment variables from .env file if running locally
try:
    api_key = st.secrets["GROQ_API_KEY"]
    is_cloud = True  # Tagged as cloud environment
except KeyError:
    load_dotenv(dotenv_path=".env")
    api_key = os.environ["GROQ_API_KEY"]  # Get the API key from an environment variable
    is_cloud = False  # Mark as local environment

# Initialize the Groq client
client = Groq(api_key=api_key)

# Initialize audio mixer
audio_available = False
try:
    mixer.init()
    audio_available = True
except Exception as e:
    st.warning(
        "The audio device is unavailable and no sound can be played."
    )  # Audio playback is not supported on the cloud platform


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
            sort=False,
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
                        rotation=angle,
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
        try:
            if "The correct answer is" in outcome:
                correct_answer = (
                    outcome.split("The correct answer is ")[1].split(".")[0].strip()
                )
            elif "the correct answer is" in outcome:
                correct_answer = (
                    outcome.split("the correct answer is ")[1].split(".")[0].strip()
                )
            else:
                correct_answer = outcome.split(":")[1].split("\n")[0].strip()
        except IndexError:
            correct_answer = "Unknown"
        return False, correct_answer


def get_explanation(question, correct_answer):
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
    st.set_page_config(
        page_title="Quiz Game"
    )  # Ensure this is the first Streamlit command
    st.title("📚 Quiz Game")

    # Initialize session state variables
    if "running" not in st.session_state:
        st.session_state.user_answers = []
        st.session_state.correctness = []
        st.session_state.explanations = {}
        st.session_state.current_question_idx = 0
        st.session_state.is_sound_played = [False] * 5
        st.session_state.selected_options = [None] * 5
        st.session_state.running = False

    if "topics" not in st.session_state:
        # Wheel properties
        num_segments = [3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30]
        st.session_state.num_topics = random.choice(num_segments)
        st.session_state.topics = generate_topics(st.session_state.num_topics)
        st.session_state.topic = None

    if not st.session_state.running:
        if not st.session_state.topic:
            st.subheader("Spin the wheel to get a random topic for a quiz!")
            # Create the animated plot
            fig, frames, final_angle = create_frames_and_plot(
                st.session_state.topics, st.session_state.num_topics
            )

            # Display the plotly figure
            plot_placeholder = st.empty()
            plot_placeholder.plotly_chart(fig, config={"displayModeBar": False})

            # Streamlit button to trigger animation
            if st.button("Determine the quiz topic"):
                if audio_available:
                    sound = mixer.Sound("audio/spin.mp3")
                    sound.play()

                # Simulate frame updates for animation
                for frame in frames:
                    fig = go.Figure(data=frame.data)
                    fig.add_annotation(
                        x=0.5,
                        y=1.03,
                        showarrow=False,
                        text="▼",
                        font=dict(size=20, color="black"),
                        xref="paper",
                        yref="paper",
                    )
                    plot_placeholder.plotly_chart(fig, config={"displayModeBar": False})
                    time.sleep(0.03)  # Delay to simulate animation speed

                st.session_state.topic = st.session_state.topics[
                    st.session_state.num_topics
                    - 1
                    - (final_angle % 360) // (360 // st.session_state.num_topics)
                ]
                st.rerun()
        else:
            st.success(f"The chosen topic is {st.session_state.topic}")
            if st.button("Start the quiz"):
                if audio_available:
                    sound = mixer.Sound("audio/play.mp3")
                    sound.play()
                st.session_state.running = True
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
            explanation = st.session_state.explanations.get(question, "No explanation.")
            st.write(
                f"**Q{idx + 1}:** {question} (Your answer: {user_answer}) - {correctness}"
            )
            st.write(f"**Explanation:** {explanation}")

        # Handle the current question
        if st.session_state.current_question_idx < len(questions):
            question = questions[st.session_state.current_question_idx]
            answer_options = ["A", "B", "C", "D"]
            selected_option = st.radio(
                f"**Q{st.session_state.current_question_idx + 1}:** {question}",
                options=answer_options,
                index=(
                    st.session_state.selected_options[
                        st.session_state.current_question_idx
                    ]
                    if st.session_state.selected_options[
                        st.session_state.current_question_idx
                    ]
                    is not None
                    else -1
                ),
            )

            if st.button("Submit"):
                st.session_state.user_answers.append(selected_option)
                is_correct_flag, correct_answer = is_correct(question, selected_option)
                st.session_state.correctness.append(
                    "Correct" if is_correct_flag else "Incorrect"
                )
                if not is_correct_flag:
                    st.session_state.explanations[question] = get_explanation(
                        question, correct_answer
                    )
                st.session_state.current_question_idx += 1
                st.session_state.selected_options[
                    st.session_state.current_question_idx - 1
                ] = answer_options.index(selected_option)
                st.rerun()

        # Display a summary after answering all questions
        if st.session_state.current_question_idx >= len(questions):
            st.success("Quiz complete!")
            st.write("Your answers:")
            for idx, answer in enumerate(st.session_state.user_answers):
                st.write(f"Q{idx + 1}: {answer} - {st.session_state.correctness[idx]}")

            if st.button("Play Again"):
                st.session_state.running = False
                st.session_state.clear()  # Reset session state


if __name__ == "__main__":
    main()
