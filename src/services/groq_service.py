# Groq API related functions
from config import GROQ_CLIENT


def validate_topic(topic):
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
        completion = GROQ_CLIENT.chat.completions.create(
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


def generate_topics(num_topics):
    """
    Generates a list of random topics
    that'll be displayed in the wheel
    using the Groq API.
    """
    response = GROQ_CLIENT.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Your output MUST consist of EXACTLY {num_topics} different topics for quiz, separated ONLY by a newline. Don't write something like Here is the output: before, just the words, not numerated",
            }
        ],
        model="gemma2-9b-it",
    )
    array = response.choices[0].message.content.split("\n")
    return array[:num_topics]


def generate_questions(topic, num_questions=5):
    """
    Generates a list of multiple-choice questions using the Groq API.
    """
    questions = []
    for _ in range(num_questions):
        prompt = (
            f"Ask a multiple choice question about {topic}. "
            f"Provide options A, B, C, D. Make sure it's different from these "
            f"existing questions: {questions}"
        )

        response = GROQ_CLIENT.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )

        question = response.choices[0].message.content.strip()
        questions.append(question)
    return questions


def check_answer(question, user_answer):
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
    chat_completion = GROQ_CLIENT.chat.completions.create(
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

    response = GROQ_CLIENT.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )

    explanation = response.choices[0].message.content.strip()
    return explanation