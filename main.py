from collections import Counter
from itertools import permutations

def load_word_list(file_path):
    with open(file_path, 'r') as file:
        return set(word.strip().strip('"').lower() for word in file)

def is_solvable(letters, word_list):
    letter_count = Counter(letters)

    # Base case: all letters used
    if not any(letter_count.values()):
        return True

    # Try forming words of valid lengths
    for i in range(3, len(letters) + 1):
        for perm in permutations(letters, i):
            word = ''.join(perm)
            if word in word_list:
                # Subtract used letters
                word_count = Counter(word)
                remaining_count = letter_count - word_count

                # Recursive call with remaining letters
                if is_solvable(''.join(remaining_count.elements()), word_list):
                    return True

    return False


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
