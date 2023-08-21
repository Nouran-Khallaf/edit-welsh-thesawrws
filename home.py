import streamlit as st
import pandas as pd
import os
import sqlite3

def connect_to_db():
    return sqlite3.connect('Data_alledited.db')

def load_data_for_user(username):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Assuming the column which indicates the user assignment is called "user"
    cursor.execute('SELECT * FROM data WHERE user=?', (username,))
    data = cursor.fetchall()
    
    # Convert fetched data to pandas DataFrame
    columns = [column[0] for column in cursor.description]
    df = pd.DataFrame(data, columns=columns)
    
    conn.close()
    return df


def load_data_for_user(username):
    conn = sqlite3.connect('Data_alledited.db')
    cursor = conn.cursor()
    # Generate synset column names
    synset_columns = [f"synset_{i}" for i in range(1, 95)]  # 95 is exclusive
    # Create the full query string
    query_string = f"SELECT word, is_saved, {', '.join(synset_columns)} FROM data WHERE user=?"
    cursor.execute(query_string, (username,))
    data = cursor.fetchall()
    
    conn.close()
    columns = ["word", 'is_saved'] + synset_columns
    return pd.DataFrame(data, columns=columns)


def save_word_for_user(username, word, synonyms):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE data
    SET user=?, is_saved=1 
    WHERE word=?
    ''', (username, word))
    
    conn.commit()
    conn.close()

def get_progress_data(username):
    df = load_data_for_user(username)
    
    total_words = len(df)
    saved_words = df["is_saved"].sum()
    unsaved_words = total_words - saved_words
    
    return unsaved_words, total_words



# authentication data
USERS = {
    "admin": {"password": "admin_pass", "start": 0, "end": -1},  
    "user1": {"password": "user1_pass", "start": 0, "end": 100},
    "user2": {"password": "user2_pass", "start": 100, "end": 200}
    
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
            st.experimental_rerun()  # Force rerun of the app
        else:
            st.warning("Incorrect username or password.")



def display_synonym_selector():
    unsaved_words, total_words = get_progress_data(st.session_state.username)
    
    # Display progress bar and associated text
    st.text(f"Unsaved words: {unsaved_words}/{total_words}")
    progress = (total_words - unsaved_words) / total_words  # Fraction of saved words
    st.progress(progress)
    data_df = load_data_for_user(st.session_state.username)

    # Prepare the word list for the dropdown
    word_list = []
    for idx, row in data_df.iterrows():
        word = row["word"]
        if row["is_saved"] == 1:  # The word is saved
            word += " (saved)" 
        word_list.append(word)

    # If word_list is empty, show a message and return early from the function
    if not word_list:
        st.warning("No words available for selection.")
        return

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
    for idx, word in enumerate(synonyms):
        word_str = str(word)  # Convert word to string
        unique_key = f"{word_str}_{idx}"  # Create a unique key for each checkbox
    
        if word_str in st.session_state.checked_synonyms:
            if idx % 2 == 0:  # Even indexed synonyms in col1
                with col1:
                    if not st.checkbox(word_str, value=True, key=unique_key):  # Pass the unique key
                        st.session_state.checked_synonyms.remove(word_str)
            else:  # Odd indexed synonyms in col2
                with col2:
                    if not st.checkbox(word_str, value=True, key=unique_key):  # Pass the unique key
                        st.session_state.checked_synonyms.remove(word_str)
        selected_synonyms.append(word_str)


    # Save Button
    if st.button("Save Word with Synonyms"):
    # Save the word to the SQLite database
        save_word_for_user(st.session_state.username, actual_selected_word, st.session_state.checked_synonyms)

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
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE data
        SET user=?
        WHERE rowid BETWEEN ? AND ?
        ''', (user_selection, start_range + 1, end_range + 1))  # +1 because rowid starts at 1

        conn.commit()
        conn.close()
    
        st.success(f"Updated word range for {user_selection}")


# Inside the main function
def main():
    st.title("Word Synonym Modefier")
    
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
