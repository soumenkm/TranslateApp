import streamlit as st
import json
import os
import time
# --- Add Firestore Imports ---
import google.cloud.firestore
from google.oauth2 import service_account
# ---------------------------

# --- Configuration ---
# (Keep your existing quality loading, DATA_FILE, CONTAINER_HEIGHT)
# Remove OUTPUT_DIR if not needed anymore
# DATA_FILE = "data.json" # Keep this if you still load initial examples from it
CONTAINER_HEIGHT = 600

# --- Firestore Collection Name ---
FIRESTORE_COLLECTION = "translation_ratings" # Choose a name for your collection

# --- Helper Functions ---
# (Keep load_data, initialize_session_state, calculate_average_scores)
def load_data(json_path="data.json"): # Assuming you still load examples this way
    """Load translation examples from a local JSON file or raise an error if not found."""
    # ...(Keep existing load_data logic)...
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
        # Optionally save dummy data locally if needed for first run
        # try:
        #     with open(json_path, "w", encoding='utf-8') as f:
        #         json.dump(dummy_data, f, indent=2)
        # except Exception as e:
        #     st.warning(f"Could not create dummy data file: {e}")
        return dummy_data


def initialize_session_state(num_examples):
    """Initializes session state variables if they don't exist."""
    # ...(Keep existing initialize_session_state logic)...
    if "example_index" not in st.session_state:
        st.session_state.example_index = 0
    if "all_ratings" not in st.session_state:
        st.session_state.all_ratings = {}
    if "username" not in st.session_state:
        st.session_state.username = ""

def calculate_average_scores(ratings_data):
    """Calculates average weighted scores across rated examples."""
    # ...(Keep existing calculate_average_scores logic)...
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
                total_score_y1_example += q['weight'] * rating_dict[q_name].get("y1", 0)
                total_score_y2_example += q['weight'] * rating_dict[q_name].get("y2", 0)
                has_valid_rating = True

        if has_valid_rating:
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


# --- Firestore Saving Function ---
def save_to_firestore(username, ratings_data):
    """Saves the collected ratings data to Google Cloud Firestore."""
    if not username:
        st.warning("Username is required to save ratings.")
        return False

    # Filter out examples that were never rated (empty dicts)
    valid_ratings = {str(idx): r for idx, r in ratings_data.items() if r} # Ensure keys are strings

    if not valid_ratings:
        st.warning("No ratings have been submitted yet. Nothing to save.")
        return False

    try:
        # --- Authenticate to Firestore using Streamlit Secrets ---
        # The structure in secrets.toml must match the keys in the JSON file
        creds_dict = st.secrets["firestore"]
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        db = google.cloud.firestore.Client(credentials=credentials)
        # ---------------------------------------------------------

        # --- Prepare data for Firestore Document ---
        # We'll create one document per submission
        username_underscored = username.strip().replace(" ", "_").lower()
        doc_id = f"{username_underscored}_{int(time.time())}" # Unique ID for the submission

        data_to_save = {
            "username": username.strip(),
            "submission_timestamp": google.cloud.firestore.SERVER_TIMESTAMP, # Use server time
            "ratings": valid_ratings, # Embed the ratings dictionary
            # Add other metadata if needed
            # "app_version": "1.0",
        }
        # ------------------------------------------

        # --- Save to Firestore ---
        doc_ref = db.collection(FIRESTORE_COLLECTION).document(doc_id)
        doc_ref.set(data_to_save)
        # -------------------------
        return True

    except KeyError as e:
        st.error(f"Firestore secrets configuration error. Missing key: {e}. Please check .streamlit/secrets.toml.")
        print(f"SECRETS ERROR: Missing key {e}") # Log for debugging
        return False
    except Exception as e:
        st.error(f"Failed to save ratings to Firestore: {e}")
        print(f"FIRESTORE SAVE ERROR: {e}") # Log for debugging
        return False

# --- Delete the old save_all_ratings function ---
# def save_all_ratings(username, ratings_data):
#    ... (DELETE THIS FUNCTION) ...

# --- Page Setup ---
st.set_page_config(page_title="Translation Quality Rating", layout="wide")
st.title("Translation Quality Rating App")

# --- Load Data ---
try:
    data = load_data()
    n_examples = len(data)
    if n_examples == 0:
        st.error("No translation examples found or generated. Please check your data file.")
        st.stop()
except ValueError as e:
    st.error(f"Error loading data: {e}")
    st.stop()
except Exception as e: # Catch broader exceptions during initial load
    st.error(f"An unexpected error occurred during data loading: {e}")
    st.stop()


# --- Initialize State ---
initialize_session_state(n_examples)

# --- Username Input ---
st.session_state.username = st.text_input(
    "Enter your name:",
    value=st.session_state.username,
    key="username_input"
)
username = st.session_state.username

# --- Instructions ---
# (Keep existing instructions)
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
col_left, col_right = st.columns([2, 3])

# --- LEFT COLUMN: Display & Navigation ---
# (Keep existing left column logic)
with col_left:
    idx = st.session_state.example_index
    try:
        current_example = data[idx]
    except IndexError:
        st.error("Error: Invalid example index encountered. Resetting to first example.")
        st.session_state.example_index = 0
        idx = 0
        current_example = data[idx]


    st.write(f"### Example {idx + 1} of {n_examples}")
    st.markdown(f"**Original Text (x):**")
    st.markdown(f"> {current_example.get('x', 'N/A')}") # Use .get for safety
    st.markdown(f"**Translation y1:**")
    st.markdown(f"> {current_example.get('y1', 'N/A')}")
    st.markdown(f"**Translation y2:**")
    st.markdown(f"> {current_example.get('y2', 'N/A')}")

    st.markdown("---")

    nav_cols = st.columns(2)
    with nav_cols[0]:
        if st.button("⬅️ Previous Example", disabled=(idx <= 0), use_container_width=True):
            if st.session_state.example_index > 0:
                st.session_state.example_index -= 1
                st.rerun()

    with nav_cols[1]:
        if st.button("Next Example ➡️", disabled=(idx >= n_examples - 1), use_container_width=True):
            if st.session_state.example_index < n_examples - 1:
                st.session_state.example_index += 1
                st.rerun()

# --- RIGHT COLUMN: Ratings Form (Scrollable) ---
# (Keep existing right column logic for the form)
with col_right:
    st.subheader("Provide Your Ratings (1-10)")

    with st.container(height=CONTAINER_HEIGHT):
        current_idx = st.session_state.example_index

        with st.form(key=f"rating_form_{current_idx}"):
            ratings_for_this_example = st.session_state.all_ratings.setdefault(current_idx, {})

            # Dynamically load qualities if possible, else use default
            try:
                from quality import qualities
            except ImportError:
                qualities = [{"name": f"Quality {i+1}", "direction": "Higher is better", "detailed_description": f"Details about quality {i+1}.", "range": [1, 10], "weight": 1.0/5.0} for i in range(5)] # Default if file missing


            for quality in qualities:
                q_name = quality["name"]
                current_q_ratings = ratings_for_this_example.setdefault(q_name, {"y1": 5, "y2": 5})

                st.markdown(f"**{q_name}** - *{quality.get('direction', 'N/A')}*") # Use .get
                with st.expander("Info", expanded=False):
                    st.markdown(quality.get('detailed_description', 'No description available.')) # Use .get

                slider_cols = st.columns(2)
                q_range = quality.get('range', [1, 10]) # Use .get with default

                with slider_cols[0]:
                    rating_y1 = st.slider(
                        f"Rating for y1",
                        min_value=q_range[0],
                        max_value=q_range[1],
                        value=current_q_ratings["y1"],
                        key=f"slider_{current_idx}_{q_name}_y1"
                    )
                with slider_cols[1]:
                    rating_y2 = st.slider(
                        f"Rating for y2",
                        min_value=q_range[0],
                        max_value=q_range[1],
                        value=current_q_ratings["y2"],
                        key=f"slider_{current_idx}_{q_name}_y2"
                    )

                ratings_for_this_example[q_name] = {"y1": rating_y1, "y2": rating_y2}
                st.markdown("---")

            submitted = st.form_submit_button("Submit Ratings for This Example")

            if submitted:
                st.session_state.all_ratings[current_idx] = ratings_for_this_example
                # Use .get for weights safely
                current_total_y1 = sum(q.get('weight', 0) * ratings_for_this_example[q['name']].get("y1", 0) for q in qualities if q['name'] in ratings_for_this_example)
                current_total_y2 = sum(q.get('weight', 0) * ratings_for_this_example[q['name']].get("y2", 0) for q in qualities if q['name'] in ratings_for_this_example)

                st.success(f"Ratings submitted for Example {current_idx + 1}! Weighted Scores: y1={current_total_y1:.2f}, y2={current_total_y2:.2f}")


# --- Submit All Ratings Section (Outside Columns) ---
st.markdown("---")

if st.button("⭐ Submit All Ratings and Save to Database ⭐", use_container_width=True): # Updated button text
    if not username.strip():
        st.warning("Please enter your name above before submitting all ratings.")
    else:
        # Calculate final averages (optional to display, but good to have)
        avg_score_y1, avg_score_y2, num_rated = calculate_average_scores(st.session_state.all_ratings)

        # --- Attempt to save to Firestore ---
        save_successful = save_to_firestore(username, st.session_state.all_ratings)
        # -----------------------------------

        if save_successful:
            if num_rated > 0:
                 st.success(
                    f"All ratings ({num_rated} examples) have been saved to the database for **{username}**!\n\n"
                    f"**Average Weighted Score (y1):** {avg_score_y1:.2f}\n\n"
                    f"**Average Weighted Score (y2):** {avg_score_y2:.2f}"
                )
            else:
                 # This case might mean save was successful but data was empty, which save_to_firestore should prevent.
                 # Still, good to handle.
                 st.warning("Ratings saved to database, but no examples appear to have been rated.")

            # Optional: Clear ratings from session state after successful save?
            # st.session_state.all_ratings = {}
            # st.rerun() # Rerun to reflect cleared state if needed

        # else: Error message is already shown by save_to_firestore