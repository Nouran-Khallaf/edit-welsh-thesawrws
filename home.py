import streamlit as st

# Simple "database" of words and their synonyms
data = {
    'happy': ['joyful', 'content', 'pleased'],
    'sad': ['downcast', 'mournful', 'unhappy'],
    'angry': ['furious', 'irate', 'enraged']
}

marked_for_deletion = []

# Function to handle login (dummy function for demonstration purposes)
def is_authenticated(username, password):
    return username == "admin" and password == "password"

def main():
    st.title("Word Synonym Selector")
    
    # Login mechanism
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if is_authenticated(username, password):
            st.success("Logged in successfully!")
            
            # Word selector
            selected_word = st.selectbox("Select a word", list(data.keys()))
            
            # Display synonyms
            synonyms = data[selected_word]
            st.write(f"Synonyms for {selected_word}: {', '.join(synonyms)}")
            
            # Select word to mark for deletion
            word_to_remove = st.selectbox("Select a word to mark for deletion", synonyms)
            if st.button("Mark for Deletion"):
                marked_for_deletion.append((selected_word, word_to_remove))
                st.success(f"Marked {word_to_remove} (synonym of {selected_word}) for deletion!")
                
            # Display words marked for deletion
            deletion_display = [f"{synonym} (of {word})" for word, synonym in marked_for_deletion]
            st.write("Words marked for deletion:", ', '.join(deletion_display))
        
        else:
            st.error("Incorrect username or password.")

if __name__ == "__main__":
    main()
