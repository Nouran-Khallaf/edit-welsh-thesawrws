import streamlit as st
import pandas as pd
import os
import sqlite3
import bcrypt
import streamlit_perspective as perspective

st.beta_set_page_config(layout="wide")
def connect_to_db():
    return sqlite3.connect('Dict_alledited.db')

def load_data_for_user(username):
    conn = connect_to_db()
    cursor = conn.cursor()
    if username == 'admin':
        cursor.execute('SELECT * FROM data')
    else:
        cursor.execute('SELECT * FROM data WHERE user=?', (username,))
  
 
    data = cursor.fetchall()
    
    # Convert fetched data to pandas DataFrame
    columns = [column[0] for column in cursor.description]
    df = pd.DataFrame(data, columns=columns)
    
    conn.close()
    return df





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
    
    if df is None or df.empty:
        return 0, 0  # Return default values if df is None or empty

    total_words = len(df)
    saved_words = df["is_saved"].sum()
    unsaved_words = total_words - saved_words
    
    return unsaved_words, total_words



def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()  # This will generate a new random salt every time
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed
def check_password(password: str, hashed: bytes) -> bool:
    # Ensure password is encoded
    if isinstance(password, str):
        password = password.encode('utf-8')

    # Ensure hashed is encoded
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')

    return bcrypt.checkpw(password, hashed)

def create_users_table():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        start INT NOT NULL,
        end INT NOT NULL
        
    )
    ''')
    
    conn.commit()
    conn.close()
def get_word_range_for_user(username):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT start, end FROM users WHERE username=?', (username,))
    result = cursor.fetchone()
    
    conn.close()
    
    return result

def register_user(username, password, start, end):
    conn = connect_to_db()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute('''
    INSERT INTO users (username, password, start, end)
    VALUES (?, ?, ?, ?)
    ''', (username, hashed_password, start, end))
    
    conn.commit()
    conn.close()
def initialize_admin():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Hash the 'admin_pass' password using bcrypt
    hashed_password = bcrypt.hashpw('admin_pass'.encode('utf-8'), bcrypt.gensalt())
    
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password, start, end)
    VALUES (?, ?, ?, ?)
    ''', ('admin', hashed_password, 0, -1))
    
    conn.commit()
    conn.close()

def is_authenticated(username, password):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username=?', (username,))
    stored_hash = cursor.fetchone()
    conn.close()

    if stored_hash is None:
        return False

    # Ensure stored_hash[0] is encoded
    stored_hash_encoded = stored_hash[0]
    if isinstance(stored_hash[0], str):
        stored_hash_encoded = stored_hash[0].encode('utf-8')

    return check_password(password, stored_hash_encoded)




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


def get_all_users_except_admin():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT username FROM users WHERE username!=?', ('admin',))
    users = cursor.fetchall()
    
    conn.close()
    
    return [user[0] for user in users]

 
def display_synonym_selector():
    # Ensure username is set
    if "username" not in st.session_state:
        st.session_state.username = "default_username"  # or prompt the user to enter a username or log in
    
    unsaved_words, total_words = get_progress_data(st.session_state.username)
    
    # Handle division by zero
    if total_words == 0:
        progress = 0
    else:
        progress = (total_words - unsaved_words) / total_words

    # Display progress bar and associated text
    st.text(f"Unsaved words: {unsaved_words}/{total_words}")
    st.progress(progress)
    
    data_df = load_data_for_user(st.session_state.username)

    # Provide feedback if no data is returned
    if data_df.empty:
        st.warning("No data available for this user.")
        return
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

    col1, col2 = st.columns(2)  # Adjust the number of columns 

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
     
    #st.write(data_df)

def display_admin_interface():
    st.header("Admin Interface")
    st.subheader("Add New User")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    new_start_range = st.number_input("Start range", min_value=0)
    new_end_range = st.number_input("End range", min_value=0)
    
    if st.button("Add User"):
        register_user(new_username, new_password, new_start_range, new_end_range)
        st.success(f"Added user: {new_username}")
    
    st.subheader("Assign Word Ranges to Users")

    # Select the user
    user_selection = st.selectbox("Select a user", get_all_users_except_admin())


    # Define word ranges for the user
    start_db, end_db = get_word_range_for_user(user_selection)
    start_range = st.number_input(f"Start range for {user_selection}", min_value=0, value=start_db)
    end_range = st.number_input(f"End range for {user_selection}", min_value=0, value=end_db)

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
    df = load_data_for_user("admin")
    st.dataframe(df)
    

# The main function
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
    create_users_table()
    initialize_admin()
    main()
