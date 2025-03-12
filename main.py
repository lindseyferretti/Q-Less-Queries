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

def can_interconnect(words, remaining_letters, solution=None):
    """Check if words can be interconnected to use all letters and return the solution."""
    if solution is None:
        solution = []
        
    if not remaining_letters:
        return True, solution
    
    if not words:
        return False, []
    
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
                break
        else:
            # If we got here, the word can be used
            # Remove letters used by this word
            updated_remaining = ''.join(new_remaining.elements())
            
            # Add this word to the current solution path
            current_solution = solution + [word]
            
            # If no letters remain, we've solved it
            if not updated_remaining:
                return True, current_solution
            
            # Try to interconnect with other words
            remaining_words = words[:i] + words[i+1:]
            
            # Find all potential shared letters between current word and remaining letters
            shared_letters = set(word) & set(updated_remaining)
            
            # If there are shared letters, we can potentially interconnect
            if shared_letters:
                is_valid, found_solution = can_interconnect(remaining_words, updated_remaining, current_solution)
                if is_valid:
                    return True, found_solution
    
    return False, []

def is_solvable(letters, word_list):
    """Check if the set of letters is solvable in Q-Less and return a solution if found."""
    # Get all valid words that can be formed from the letters
    valid_words = get_valid_words(letters, word_list)
    
    # No valid words means it's not solvable
    if not valid_words:
        return False, []
    
    # Check if words can be interconnected to use all letters
    is_valid, solution = can_interconnect(valid_words, letters)
    return is_valid, solution

def display_solution(solution):
    """Display the solution in a readable format with a matrix visualization."""
    print("\nHere's a potential solution:")
    print("--------------------------")
    for i, word in enumerate(solution, 1):
        print(f"Word {i}: {word}")
    
    # Create a crossword-like visualization
    print("\nPossible arrangement:")
    print("--------------------------")
    
    # We'll use a simple algorithm to create a 2D grid representation
    # First, place the first word horizontally in the middle
    # Then try to add subsequent words vertically or horizontally
    
    # Initialize grid size - make it generous to accommodate the solution
    grid_size = 30
    middle = grid_size // 2
    grid = [[' ' for _ in range(grid_size)] for _ in range(grid_size)]
    
    # Keep track of word placements
    placed_words = []
    
    # Place first word horizontally in the middle
    if solution:
        first_word = solution[0]
        start_col = middle - len(first_word) // 2
        for j, char in enumerate(first_word):
            grid[middle][start_col + j] = char
        placed_words.append((first_word, middle, start_col, 'horizontal'))
    
    # Try to place remaining words
    for word in solution[1:]:
        placed = False
        
        # Try to connect with already placed words
        for placed_word, row, col, orientation in placed_words:
            if placed:
                break
                
            # Find shared letters
            for i, char in enumerate(word):
                if char in placed_word:
                    # Find all occurrences of this char in the placed word
                    for j, placed_char in enumerate(placed_word):
                        if char == placed_char:
                            # Determine position of the shared letter
                            if orientation == 'horizontal':
                                shared_row, shared_col = row, col + j
                            else:  # vertical
                                shared_row, shared_col = row + j, col
                                
                            # Try to place this word in the opposite orientation
                            if orientation == 'horizontal':  # Place new word vertically
                                # Check if there's room
                                start_row = shared_row - i
                                if start_row >= 0 and start_row + len(word) < grid_size:
                                    # Check if placement is valid (no conflicts)
                                    valid = True
                                    for k, word_char in enumerate(word):
                                        curr_row = start_row + k
                                        if grid[curr_row][shared_col] != ' ' and grid[curr_row][shared_col] != word_char:
                                            valid = False
                                            break
                                    
                                    if valid:
                                        # Place the word
                                        for k, word_char in enumerate(word):
                                            grid[start_row + k][shared_col] = word_char
                                        placed_words.append((word, start_row, shared_col, 'vertical'))
                                        placed = True
                                        break
                            else:  # Place new word horizontally
                                # Check if there's room
                                start_col = shared_col - i
                                if start_col >= 0 and start_col + len(word) < grid_size:
                                    # Check if placement is valid
                                    valid = True
                                    for k, word_char in enumerate(word):
                                        curr_col = start_col + k
                                        if grid[shared_row][curr_col] != ' ' and grid[shared_row][curr_col] != word_char:
                                            valid = False
                                            break
                                    
                                    if valid:
                                        # Place the word
                                        for k, word_char in enumerate(word):
                                            grid[shared_row][start_col + k] = word_char
                                        placed_words.append((word, shared_row, start_col, 'horizontal'))
                                        placed = True
                                        break
        
        # If couldn't place the word connected to others, place it somewhere else
        if not placed and solution.index(word) < len(solution) - 1:  # Skip this for the last word
            # Place horizontally below the last word
            last_word, last_row, last_col, orientation = placed_words[-1]
            if orientation == 'horizontal':
                new_row = last_row + 2
            else:
                new_row = last_row + len(last_word) + 1
            
            if new_row < grid_size:
                start_col = middle - len(word) // 2
                for j, char in enumerate(word):
                    grid[new_row][start_col + j] = char
                placed_words.append((word, new_row, start_col, 'horizontal'))
    
    # Determine bounds of the grid to print
    min_row, max_row = grid_size, 0
    min_col, max_col = grid_size, 0
    
    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col] != ' ':
                min_row = min(min_row, row)
                max_row = max(max_row, row)
                min_col = min(min_col, col)
                max_col = max(max_col, col)
    
    # Add some padding
    min_row = max(0, min_row - 1)
    min_col = max(0, min_col - 1)
    max_row = min(grid_size - 1, max_row + 1)
    max_col = min(grid_size - 1, max_col + 1)
    
    # Print the relevant part of the grid
    for row in range(min_row, max_row + 1):
        print(''.join(grid[row][min_col:max_col + 1]))
    
    print("--------------------------")

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

        is_valid, solution = is_solvable(user_input, word_list)
        
        if is_valid:
            print("This set is solvable, good luck!")
            
            # Ask if the user wants to see a solution
            show_solution = input("Would you like to see a potential solution? (yes/no)\n> ").strip().lower()
            if show_solution == 'yes':
                display_solution(solution)
        else:
            print("This set is not solvable. Roll again!")

        print("\nWould you like to check another roll? (yes/no)")
        retry = input("> ").strip().lower()
        if retry != 'yes':
            break

    print("See ya!")

if __name__ == "__main__":
    main()
