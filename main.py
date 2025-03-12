from collections import Counter
from itertools import permutations

def load_word_list(file_path):
    with open(file_path, 'r') as file:
        return set(word.strip().strip('"').lower() for word in file)

def get_valid_words(letters, word_list):
    """Find all valid words that can be formed from the given letters."""
    letter_counter = Counter(letters)
    valid_words = []
    
    # Filter word_list to only include words with length 3 or more
    # and that can be formed from the available letters
    for word in word_list:
        if len(word) >= 3 and all(letter_counter[letter] >= count for letter, count in Counter(word).items()):
            valid_words.append(word)
    
    return valid_words

def can_interconnect(words, remaining_letters):
    """Check if words can be interconnected to use all letters."""
    if not remaining_letters:
        return True
    
    if not words:
        return False
    
    # Try each word as a starting point
    for i, word in enumerate(words):
        # Count letters used in the current word
        word_counter = Counter(word)
        
        # Calculate remaining letters after using this word
        new_remaining = Counter(remaining_letters)
        for letter, count in word_counter.items():
            new_remaining[letter] -= count
            if new_remaining[letter] < 0:
                # This means the word uses more of a letter than available
                # This shouldn't happen with our valid_words filtering, but just in case
                break
        else:
            # If we got here, the word can be used
            # Remove letters used by this word
            updated_remaining = ''.join(new_remaining.elements())
            
            # If no letters remain, we've solved it
            if not updated_remaining:
                return True
            
            # Try to interconnect with other words
            remaining_words = words[:i] + words[i+1:]
            
            # Find all potential shared letters between current word and remaining letters
            shared_letters = set(word) & set(updated_remaining)
            
            # If there are shared letters, we can potentially interconnect
            if shared_letters and can_interconnect(remaining_words, updated_remaining):
                return True
    
    return False

def is_solvable(letters, word_list):
    """Check if the set of letters is solvable in Q-Less."""
    # Get all valid words that can be formed from the letters
    valid_words = get_valid_words(letters, word_list)
    
    # No valid words means it's not solvable
    if not valid_words:
        return False
    
    # Check if words can be interconnected to use all letters
    return can_interconnect(valid_words, letters)


def main():
    word_list = load_word_list("wordlist-20210729.txt")

    print("Got your dice? Let's check if your roll is solvable!")
    print("Please enter a set of letters:")

    while True:
        user_input = input("> ").strip()

        if not user_input.isalpha():
            print("Input must contain only letters. Please try again.")
            continue

        if len(user_input) != 12:
            print("Input must be exactly 12 letters. Please try again.")
            continue

        user_input = user_input.lower()

        if is_solvable(user_input, word_list):
            print("This set is solvable, good luck!")
        else:
            print("This set is not solvable. Roll again!")

        print("\nWould you like to check another roll? (yes/no)")
        retry = input("> ").strip().lower()
        if retry != 'yes':
            break

    print("See ya!")

if __name__ == "__main__":
    main()
