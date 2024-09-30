from groq import Groq
import streamlit as st

st.title("Trivia quiz")

client = Groq(api_key="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")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.question_num = 0
    st.session_state.wrong_answer = False
    prompt_question_with_context = "Ask a multiple choice question about history, science or pop culture"
    stream = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "user",
                "content": prompt_question_with_context,
            }
        ],
    )
    st.session_state.prev_question = stream.choices[0].message.content
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": st.session_state.prev_question})
if st.session_state.question_num == 5:
    st.subheader("You won!")
    st.stop()
elif st.session_state.wrong_answer:
    st.subheader("Game over")
    st.stop()
else:
    st.subheader("Answer 5 questions correctly to win")
    st.session_state.question_num += 1

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Enter your answer..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    prompt_question = f"Question: {st.session_state.prev_question}\n My answer: {prompt}\n If the answer is correct, output Correct, else output Incorrect and nothing else"

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "user",
                    "content": prompt_question,
                }
            ],
        )
        outcome = stream.choices[0].message.content
        st.markdown(outcome)
        if "incorrect" in outcome.lower():
            st.session_state.wrong_answer = True
            st.rerun()

    st.session_state.messages.append({"role": "assistant", "content": outcome})
        
    with st.chat_message("assistant"):
        prompt_question_with_context = "Ask a multiple choice question about history, science or pop culture"
        stream = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "user",
                    "content": prompt_question_with_context,
                }
            ],
        )
        st.session_state.prev_question = stream.choices[0].message.content
        st.markdown(st.session_state.prev_question)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": st.session_state.prev_question})