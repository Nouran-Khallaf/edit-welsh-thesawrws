import streamlit as st
import pandas as pd
import os
# File to store the data
FILE_NAME = "Data_alledited.csv"

# authentication data
USERS = {
    "admin": {"password": "admin_pass", "start": 0, "end": -1, "filename": None},  
    "user1": {"password": "user1_pass", "start": 0, "end": 100, "filename": "data_0_100.csv"},
    "user2": {"password": "user2_pass", "start": 100, "end": 200, "filename": "data_100_200.csv"}
    # Add more users as required
}



# Authentication function
def is_authenticated(username, password):
    print(f"Input Username: {username}")
    print(f"Input Password: {password}")
    print(f"Stored Password for {username}: {USERS.get(username, {}).get('password')}")
    return USERS.get(username, {}).get("password") == password

def display_login():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if is_authenticated(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.warning("Incorrect username or password.")



def load_data():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    return pd.DataFrame(columns=["word"])


def display_synonym_selector():
    user_filename = USERS[st.session_state.username].get('filename')

    if not user_filename:
        st.error("Error: Filename is not set for this user. Please contact the admin.")
        return

    if not os.path.exists(user_filename):
        st.error(f"The data file {user_filename} does not exist.")
        return
    
    data_df = pd.read_csv(user_filename)
    
    # Prepare the word list for the dropdown
    word_list = []
    for idx, row in data_df.iterrows():
        word = row["word"]
        if row["is_saved"] == 1:  # The word is saved
            word += " (saved)"  # You can adjust this to your needs
        word_list.append(word)

    selected_word = st.selectbox("Select a word", word_list)

    # Extract just the word name without "(saved)" if present
    actual_selected_word = selected_word.split(" ")[0]

    # Extract synonyms
    synonyms = data_df.loc[data_df['word'] == actual_selected_word].iloc[0, 1:-1].dropna().tolist()

    if 'last_selected_word' not in st.session_state or st.session_state.last_selected_word != selected_word:
        st.session_state.checked_synonyms = synonyms.copy()
        st.session_state.last_selected_word = selected_word

    col1, col2 = st.columns(2)  # Adjust the number of columns based on your needs

    selected_synonyms = []
    for word in synonyms:
        if word in st.session_state.checked_synonyms:
            if synonyms.index(word) % 2 == 0:  # Even indexed synonyms in col1
                with col1:
                    if not st.checkbox(word, value=True):
                        st.session_state.checked_synonyms.remove(word)
            else:  # Odd indexed synonyms in col2
                with col2:
                    if not st.checkbox(word, value=True):
                        st.session_state.checked_synonyms.remove(word)
        selected_synonyms.append(word)

    # Save Button
    if st.button("Save Word with Synonyms"):
        # Mark the word as saved in the dataframe
        data_df.loc[data_df['word'] == actual_selected_word, 'is_saved'] = 1
        data_df.to_csv(FILE_NAME, index=False)

        st.success(f"Saved {actual_selected_word} and its synonyms.")
        st.write(data_df)

def display_admin_interface():
    st.header("Admin Interface")
    st.subheader("Assign Word Ranges to Users")

    # Select the user
    user_selection = st.selectbox("Select a user", list(USERS.keys())[1:])  # Excluding the admin

    # Define word ranges for the user
    start_range = st.number_input(f"Start range for {user_selection}", min_value=0, value=USERS[user_selection]['start'])
    end_range = st.number_input(f"End range for {user_selection}", min_value=0, value=USERS[user_selection]['end'])

    if st.button("Update Range"):
        USERS[user_selection]['start'] = start_range
        USERS[user_selection]['end'] = end_range
        USERS[user_selection]['filename'] = f"data_{start_range}_{end_range}.csv"
        st.success(f"Updated word range for {user_selection}")

    st.subheader("All User Ranges")
    for user, details in USERS.items():
        if user != "admin":
            st.write(f"{user}: {details['start']} - {details['end']}")





# Inside the main function
def main():
    st.title("Word Synonym Selector")
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Show the login page if not logged in
    if not st.session_state.logged_in:
        display_login()
    else:
        if st.session_state.username == "admin":
            display_admin_interface()
        else:
            display_synonym_selector()


if __name__ == "__main__":
    main()
