from unittest.mock import patch
from services.groq_service import (
    validate_topic,
    generate_topics,
    generate_questions,
    check_answer,
    get_explanation
)


class TestGroqService:
    def test_validate_topic_valid(self):
        """Test that valid topics are recognized"""
        test_cases = [
            "Python Programming",
            "World History",
            "Space Exploration"
        ]
        for topic in test_cases:
            is_valid, result = validate_topic(topic)
            assert is_valid == True
            assert result == ""

    def test_validate_topic_invalid(self):
        """Test that invalid topics are rejected"""
        test_cases = [
            "asdfghjk",
            "123456",
            "but"
        ]
        for topic in test_cases:
            is_valid, result = validate_topic(topic)
            assert is_valid == False
            assert result == "Please enter a real topic."

    def test_generate_topics(self):
        """Test if the program generates the correct amount of valid topics"""
        topics = generate_topics(12)
        assert len(topics) == 12

        for topic in topics:
            is_valid, result = validate_topic(topic)
            assert is_valid == True
            assert result == ""

    def test_generate_questions(self):
        """Test question generation with multiple API calls"""
        topic = "Python Programming"
        num_questions = 2

        # Prepare mock responses for multiple API calls
        mock_responses = [
            """1. What is Python? 
            A) A programming language
            B) A snake
            C) A type of fruit
            D) A movie""",

            """2. What does OOP stand for?
            A) Object Oriented Programming
            B) Out of Possibilities
            C) Open Operational Protocol
            D) Optimized Object Process"""
        ]

        # Mock the Groq API call with side_effect to simulate multiple calls
        with patch('services.groq_service.GROQ_CLIENT.chat.completions.create') as mock_create:
            # Create mock response objects
            mock_responses_objs = [
                type('MockResponse', (), {
                    'choices': [type('MockChoice', (), {
                        'message': type('MockMessage', (), {
                            'content': response
                        })
                    })()]
                }) for response in mock_responses
            ]

            # Use side_effect to return different responses for each call
            mock_create.side_effect = mock_responses_objs

            # Call the function
            questions = generate_questions(topic, num_questions)

            # Verify API was called correct number of times
            assert mock_create.call_count == num_questions

            # Verify questions
            assert len(questions) == num_questions
            assert "What is Python?" in questions[0]
            assert "What does OOP stand for?" in questions[1]

    def test_check_answer(self):
        """Test answer checking mechanism"""
        question = """
        What is Python? 
        A) A programming language
        B) A snake
        C) A type of fruit
        D) A movie
        """

        is_correct, result = check_answer(question, "A")
        assert is_correct == True
        assert result == "A"

        # Check if it works correctly when the answer is wrong
        is_correct, result = check_answer(question, "B")
        assert is_correct == False
        assert result == "A"

    def test_get_explanation(self):
        """Test explanation retrieval"""
        question = """
        What is Python? 
        A) A programming language
        B) A snake
        C) A type of fruit
        D) A movie
        """

        with patch('services.groq_service.GROQ_CLIENT.chat.completions.create') as mock_create:
            # Simulate explanation generation
            mock_create.return_value.choices[0].message.content = (
                "Python is a high-level, interpreted programming language known for "
                "its readability and versatility in software development."
            )

            explanation = get_explanation(question, "A")
            assert len(explanation) > 0
            assert "Python" in explanation