import streamlit as st
import json
import os
import time # For potential small delays if needed

# --- Configuration ---
# Assuming quality.py exists and defines 'qualities' list
# Example dummy 'qualities' if quality.py is not available:
try:
    from quality import qualities
except ImportError:
    print("Warning: quality.py not found. Using dummy data for 'qualities'.")
    qualities = [
        {"name": f"Quality {i+1}", "direction": "Higher is better", "detailed_description": f"Details about quality {i+1}.", "range": [1, 10], "weight": 1.0/5.0}
        for i in range(10) # Make it 10 to ensure scrolling is needed
    ]

DATA_FILE = "data.json"
OUTPUT_DIR = "output"
CONTAINER_HEIGHT = 600 # Pixels - Adjust this value as needed for the right column scroll height

# --- Helper Functions ---
def load_data(json_path=DATA_FILE):
    """Load translation examples from a local JSON file or raise an error if not found."""
    if os.path.exists(json_path):
        with open(json_path, "r", encoding='utf-8') as f: # Added encoding
            data = json.load(f)
        if not isinstance(data, list) or not data:
             raise ValueError(f"{json_path} should contain a non-empty list of examples.")
        return data
    else:
        # Generate dummy data if file not found
        st.warning(f"{json_path} not found. Generating dummy data.")
        dummy_data = [
            {
                "x": f"This is original sentence number {i+1}. It might be long to test wrapping.",
                "y1": f"This is translation one for sentence {i+1}, potentially also quite long.",
                "y2": f"This is translation two for sentence {i+1}, different from the first one."
            } for i in range(5) # Generate 5 dummy examples
        ]
        try:
            with open(json_path, "w", encoding='utf-8') as f:
                json.dump(dummy_data, f, indent=2)
            return dummy_data
        except Exception as e:
            st.error(f"Could not create dummy data file: {e}")
            return [] # Return empty list to avoid crashing later


def initialize_session_state(num_examples):
    """Initializes session state variables if they don't exist."""
    if "example_index" not in st.session_state:
        st.session_state.example_index = 0
    if "all_ratings" not in st.session_state:
        # Structure: {example_index: {quality_name: {"y1": score, "y2": score}}}
        st.session_state.all_ratings = {}
    if "username" not in st.session_state:
        st.session_state.username = ""
    # Ensure all_ratings has entries for all potential examples if needed,
    # or create them on demand as done later.

def save_all_ratings(username, ratings_data):
    """Saves the collected ratings to a JSON file."""
    if not username:
        st.warning("Please enter your name before submitting all ratings.")
        return False # Indicate failure

    username_underscored = username.strip().replace(" ", "_").lower()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{username_underscored}.json")

    # Filter out examples that were never rated (empty dicts)
    # Although the calculation part already handles this, it makes the output file cleaner.
    valid_ratings = {idx: r for idx, r in ratings_data.items() if r} # Check if dict is not empty

    if not valid_ratings:
        st.warning("No ratings have been submitted yet. Nothing to save.")
        return False # Indicate failure

    try:
        with open(out_path, "w", encoding='utf-8') as f:
            json.dump(valid_ratings, f, indent=2)
        return True # Indicate success
    except Exception as e:
        st.error(f"Failed to save ratings to {out_path}: {e}")
        return False # Indicate failure

def calculate_average_scores(ratings_data):
    """Calculates average weighted scores across rated examples."""
    sum_y1 = 0.0
    sum_y2 = 0.0
    num_examples_rated = 0

    for example_idx, rating_dict in ratings_data.items():
        if not rating_dict: # Skip if no ratings were recorded for this example index
            continue

        total_score_y1_example = 0.0
        total_score_y2_example = 0.0
        has_valid_rating = False

        for q in qualities:
            q_name = q["name"]
            if q_name in rating_dict:
                # Use .get with default 0 in case y1/y2 keys are missing (shouldn't happen with current logic)
                total_score_y1_example += q['weight'] * rating_dict[q_name].get("y1", 0)
                total_score_y2_example += q['weight'] * rating_dict[q_name].get("y2", 0)
                has_valid_rating = True

        if has_valid_rating: # Only count example if it had at least one quality rated
            sum_y1 += total_score_y1_example
            sum_y2 += total_score_y2_example
            num_examples_rated += 1

    if num_examples_rated > 0:
        avg_score_y1 = sum_y1 / num_examples_rated
        avg_score_y2 = sum_y2 / num_examples_rated
    else:
        avg_score_y1 = 0.0
        avg_score_y2 = 0.0

    return avg_score_y1, avg_score_y2, num_examples_rated


# --- Page Setup ---
st.set_page_config(page_title="Translation Quality Rating", layout="wide")
st.title("Translation Quality Rating App")

# --- Load Data ---
try:
    data = load_data()
    n_examples = len(data)
    if n_examples == 0:
        st.error("No translation examples found or generated. Please check your data file.")
        st.stop() # Stop execution if no data
except ValueError as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- Initialize State ---
initialize_session_state(n_examples)

# --- Username Input ---
# Use session state to preserve username across reruns
st.session_state.username = st.text_input(
    "Enter your name:",
    value=st.session_state.username,
    key="username_input" # Use a distinct key if 'username' is used elsewhere in state
)
username = st.session_state.username # Local variable for convenience

# --- Instructions ---
st.write(
    """
    Use the left column to see the **original text** and **two translations**.
    Use **Previous Example** / **Next Example** to navigate through examples.
    On the right, rate **all quality dimensions** using the sliders. The right panel will scroll if needed.
    Click **Submit Ratings for This Example** to record your ratings for the current item.
    Click **Submit All Ratings** at the bottom when finished with all examples.
    """
)

# --- Main Layout ---
col_left, col_right = st.columns([2, 3]) # Ratio: left=40%, right=60%

# --- LEFT COLUMN: Display & Navigation ---
with col_left:
    idx = st.session_state.example_index
    current_example = data[idx]

    st.write(f"### Example {idx + 1} of {n_examples}")
    st.markdown(f"**Original Text (x):**")
    st.markdown(f"> {current_example['x']}") # Use blockquote for better visual separation
    st.markdown(f"**Translation y1:**")
    st.markdown(f"> {current_example['y1']}")
    st.markdown(f"**Translation y2:**")
    st.markdown(f"> {current_example['y2']}")

    st.markdown("---") # Separator

    # Navigation Buttons
    nav_cols = st.columns(2)
    with nav_cols[0]:
        if st.button("⬅️ Previous Example", disabled=(idx <= 0), use_container_width=True):
            if st.session_state.example_index > 0:
                st.session_state.example_index -= 1
                st.rerun() # Force rerun to update display and form keys

    with nav_cols[1]:
        if st.button("Next Example ➡️", disabled=(idx >= n_examples - 1), use_container_width=True):
            if st.session_state.example_index < n_examples - 1:
                st.session_state.example_index += 1
                st.rerun() # Force rerun

# --- RIGHT COLUMN: Ratings Form (Scrollable) ---
with col_right:
    st.subheader("Provide Your Ratings (1-10)")

    # Use st.container with a fixed height to make this area scrollable
    # Adjust the height value as needed
    with st.container(height=CONTAINER_HEIGHT):
        current_idx = st.session_state.example_index

        # Use a unique key for the form based on the example index
        # This ensures the form state is reset or correctly loaded when navigating
        with st.form(key=f"rating_form_{current_idx}"):

            # Get current ratings for this example, initializing if necessary
            # Using .setdefault ensures the dictionary exists before accessing keys
            ratings_for_this_example = st.session_state.all_ratings.setdefault(current_idx, {})

            for quality in qualities:
                q_name = quality["name"]

                # Initialize ratings for this specific quality if not already set
                current_q_ratings = ratings_for_this_example.setdefault(q_name, {"y1": 5, "y2": 5})

                st.markdown(f"**{q_name}** - *{quality['direction']}*")
                with st.expander("Info", expanded=False): # Keep collapsed by default
                    st.markdown(quality["detailed_description"])

                # Sliders within columns
                slider_cols = st.columns(2)
                with slider_cols[0]:
                    # IMPORTANT: Key must be unique across the entire app session *for this specific slider*
                    # Include index and quality name and y1/y2 identifier
                    rating_y1 = st.slider(
                        f"Rating for y1", # Keep label short
                        min_value=quality['range'][0],
                        max_value=quality['range'][1],
                        value=current_q_ratings["y1"], # Read initial value from state
                        key=f"slider_{current_idx}_{q_name}_y1"
                    )
                with slider_cols[1]:
                    rating_y2 = st.slider(
                        f"Rating for y2", # Keep label short
                        min_value=quality['range'][0],
                        max_value=quality['range'][1],
                        value=current_q_ratings["y2"], # Read initial value from state
                        key=f"slider_{current_idx}_{q_name}_y2"
                    )

                # Temporarily store the current slider values within the form's scope.
                # These will be officially saved to session_state only on form submission.
                ratings_for_this_example[q_name] = {"y1": rating_y1, "y2": rating_y2}

                st.markdown("---") # Separator between qualities

            # Form submission button
            submitted = st.form_submit_button("Submit Ratings for This Example")

            if submitted:
                # --- IMPORTANT: Update the main session state ONLY after submission ---
                # The 'ratings_for_this_example' dict now holds the submitted values
                st.session_state.all_ratings[current_idx] = ratings_for_this_example

                # Optional: Calculate and show score for this example immediately
                current_avg_y1, current_avg_y2, _ = calculate_average_scores({current_idx: ratings_for_this_example})

                st.success(f"Ratings submitted for Example {current_idx + 1}! Weighted Scores: y1={current_avg_y1:.2f}, y2={current_avg_y2:.2f}")
                # No rerun here, message stays until next action

# --- Submit All Ratings Section (Outside Columns) ---
st.markdown("---") # Page separator

if st.button("⭐ Submit All Ratings and Save ⭐", use_container_width=True):
    if not username.strip():
        st.warning("Please enter your name above before submitting all ratings.")
    else:
        # Calculate final averages
        avg_score_y1, avg_score_y2, num_rated = calculate_average_scores(st.session_state.all_ratings)

        # Attempt to save
        save_successful = save_all_ratings(username, st.session_state.all_ratings)

        if save_successful:
            if num_rated > 0:
                 st.success(
                    f"All ratings ({num_rated} examples) have been saved for **{username}**!\n\n"
                    f"**Average Weighted Score (y1):** {avg_score_y1:.2f}\n\n"
                    f"**Average Weighted Score (y2):** {avg_score_y2:.2f}"
                )
            else:
                 st.warning("Ratings saved, but no examples appear to have been rated. Average scores are 0.")
        # else: Error message already shown by save_all_ratings