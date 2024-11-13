# Main Streamlit app
import streamlit as st
import re
import time
from models.session import SessionState
from utils.validators import get_valid_custom_topic
from utils.spinning_wheel import SpinningWheel
from services.audio_service import audio
from services.groq_service import check_answer, get_explanation


def main():
    st.set_page_config(page_title="Quiz Game")
    st.title("📚 Quiz Game")

    # Initialize session state variables
    SessionState.initialize()

    if not st.session_state.running:
        if st.session_state.custom_topic:
            st.session_state.topic = get_valid_custom_topic()
        if st.session_state.topic:
            st.success(f"The chosen topic is {st.session_state.topic}")
            if st.button("Start the quiz"):
                audio.play_sound('play')

                st.session_state.running = True
                st.rerun()
        elif not st.session_state.custom_topic:
            st.subheader("Spin the wheel to get a random topic for a quiz!")
            # Initialize the spinning wheel
            wheel = SpinningWheel()

            # Initialize the wheel and get the frames
            frames, final_angle = wheel.initialize_wheel(
                st.session_state.topics,
                st.session_state.num_topics
            )

            # Create three columns
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
                    audio.play_sound('spin')

                    # Simulate frame updates for animation
                    wheel.animate_spin(frames)

                    st.session_state.topic = st.session_state.topics[
                        st.session_state.num_topics
                        - 1
                        - (final_angle % 360) // (360 // st.session_state.num_topics)
                    ]
                    st.rerun()
    else:  # Quiz based on chosen topic
        SessionState.start_game()

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
                    audio.play_sound('submit')

                    # Record the user's answer
                    st.session_state.user_answers.append(selected_option)

                    # Check if the answer is correct
                    correct, correct_answer = check_answer(
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
                audio.play_sound('option')

        # After all questions are answered
        if st.session_state.current_question_idx == len(questions):
            st.session_state.running = False
            st.session_state.elapsed_time = time.time() - st.session_state.start_time
            audio.play_sound('end_game')
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
