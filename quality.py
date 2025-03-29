# Define quality dimensions with a minimal display and detailed explanation
qualities = [
    {
        "name": "Adequacy (Meaning Preservation)",
        "description": "Measures how accurately the translation preserves the meaning of the original text.",
        "range": (1, 10),
        "weight": 0.30,
        "direction": "Higher is better",
        "detailed_description": (
            "Adequacy measures how accurately the translation preserves the meaning of the original text. "
            "A high score (closer to 10) indicates that the translated text conveys nearly the exact meaning of the source. "
            "For example, if the English sentence is **'I am happy'** and the Hindi translation is **'मैं खुश हूँ'**, "
            "a score of 9 or 10 would suggest almost perfect meaning preservation, whereas a lower score (e.g., 3 or 4) "
            "would indicate significant loss or distortion of meaning."
        )
    },
    {
        "name": "Fluency",
        "description": "Evaluates how naturally and smoothly the translation reads.",
        "range": (1, 10),
        "weight": 0.30,
        "direction": "Higher is better",
        "detailed_description": (
            "Fluency evaluates the natural flow and readability of the translation. "
            "A higher score indicates that the translation reads smoothly and naturally without awkward phrasing. "
            "For example, if the English sentence **'The cat sat on the mat'** is translated into Hindi as "
            "**'बिल्ली चटाई पर आराम से बैठी'**, the translation is fluent and would receive a high score. "
            "An awkward or stilted translation would be rated lower."
        )
    },
    {
        "name": "Grammatical Correctness",
        "description": "Assesses proper grammar, punctuation, and sentence structure.",
        "range": (1, 10),
        "weight": 0.20,
        "direction": "Higher is better",
        "detailed_description": (
            "Grammatical Correctness checks whether the translation employs proper grammar, punctuation, and sentence structure. "
            "A higher score means the translation is essentially error-free. "
            "For instance, if the English sentence **'She goes to school'** is translated as **'वह स्कूल जाती है'** in Hindi, "
            "this demonstrates correct grammar. Any grammatical mistakes or punctuation errors would lower the score."
        )
    },
    {
        "name": "Style Consistency",
        "description": "Assesses whether the translation maintains the tone and style of the original text.",
        "range": (1, 10),
        "weight": 0.10,
        "direction": "Higher is better",
        "detailed_description": (
            "Style Consistency evaluates if the translation preserves the tone and stylistic nuances of the original text. "
            "A high score means that the translated text matches the formal or informal register of the source. "
            "For example, if a formal English document is translated into Hindi using a formal tone consistently, it would receive a high score."
        )
    },
    {
        "name": "Conciseness",
        "description": "Determines if the translation is succinct without unnecessary verbosity.",
        "range": (1, 10),
        "weight": 0.10,
        "direction": "Higher is better",
        "detailed_description": (
            "Conciseness evaluates whether the translation is brief yet complete, avoiding unnecessary verbosity while retaining full meaning. "
            "A higher score indicates an optimal balance of brevity and completeness. "
            "For example, if the English sentence **'Please turn off the light when you leave the room'** is translated into Hindi as "
            "**'कमरा छोड़ते समय लाइट बंद करें'**, it would be considered concise and score highly."
        )
    }
]