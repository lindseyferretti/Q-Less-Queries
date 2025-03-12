from collections import Counter, defaultdict, deque
import time
import os
import functools

class WordList:
    """Class for handling word list operations"""
    
    @staticmethod
    def load(file_path):
        """Load a word list from a file, with error handling.
        
        Args:
            file_path: Path to the word list file
            
        Returns:
            Set of words (lowercase)
        """
        if not os.path.exists(file_path):
            print(f"Error: Word list file '{file_path}' not found.")
            print("Make sure the file exists in the correct location.")
            return set()
            
        try:
            with open(file_path, 'r') as file:
                return set(word.strip().strip('"').lower() for word in file if len(word.strip()) >= 3)
        except Exception as e:
            print(f"Error loading word list: {e}")
            return set()


class QlessSolver:
    """Core solver logic for the Q-Less game"""
    
    def __init__(self, word_list):
        """Initialize the solver with a word list
        
        Args:
            word_list: Set of valid words to use for solving
        """
        self.word_list = word_list
        # Create a lookup structure of words by letter counts for fast filtering
        self.word_counter_map = {word: Counter(word) for word in word_list}
        
    def get_valid_words(self, letters):
        """Find all valid words that can be formed from the given letters.
        
        Args:
            letters: String of available letters
            
        Returns:
            List of valid words sorted by length (descending)
        """
        letter_counter = Counter(letters)
        valid_words = []
        
        # Filter word_list using precomputed counters
        for word, word_counter in self.word_counter_map.items():
            # Fast check: Skip words with letters not in our set
            if not (word_counter.keys() <= letter_counter.keys()):
                continue
                
            # Check if we have enough of each letter
            if all(letter_counter[letter] >= count for letter, count in word_counter.items()):
                valid_words.append(word)
        
        # Sort words by length (descending) to optimize search
        valid_words.sort(key=len, reverse=True)
        return valid_words
    
    def find_all_solutions(self, letters, max_solutions=100, timeout=5):
        """Find all valid solutions for a set of letters
        
        Args:
            letters: String of available letters
            max_solutions: Maximum number of solutions to find
            timeout: Maximum time to spend searching (seconds)
            
        Returns:
            List of valid solutions, where each solution is a list of words
        """
        valid_words = self.get_valid_words(letters)
        
        # No valid words means it's not solvable
        if not valid_words:
            return []
        
        # Precompute letter counters for each word to avoid recomputing
        word_counters = {word: Counter(word) for word in valid_words}
        
        # Iterative approach with an explicit stack to avoid recursion depth issues
        start_time = time.time()
        all_solutions = []
        
        # Stack entries: (words_to_try, remaining_letters, current_solution, skip_index)
        # skip_index tells us which word in words_to_try we're currently considering
        stack = [(valid_words, letters, [], 0)]
        
        while stack and len(all_solutions) < max_solutions and time.time() - start_time < timeout:
            words, remaining, solution, skip_idx = stack.pop()
            
            # No letters left means we found a solution
            if not remaining:
                all_solutions.append(solution)
                continue
                
            # No words left or tried all words but still have letters, this path fails
            if not words or skip_idx >= len(words):
                continue
                
            # Get the current word we're considering
            word = words[skip_idx]
            
            # Option 1: Skip this word and try the next one
            stack.append((words, remaining, solution, skip_idx + 1))
            
            # Option 2: Use this word if possible
            if len(word) <= len(remaining):
                # Check if we can use this word
                remaining_counter = Counter(remaining)
                word_counter = word_counters[word]
                
                can_use = True
                for letter, count in word_counter.items():
                    if remaining_counter[letter] < count:
                        can_use = False
                        break
                
                if can_use:
                    # Remove letters used by this word
                    for letter, count in word_counter.items():
                        remaining_counter[letter] -= count
                    
                    # Create new remaining letters string
                    updated_remaining = ''.join(remaining_counter.elements())
                    
                    # Create new word list without the current word
                    remaining_words = words[:skip_idx] + words[skip_idx+1:]
                    
                    # Add to stack - try with this word
                    new_solution = solution + [word]
                    stack.append((remaining_words, updated_remaining, new_solution, 0))
        
        # If we didn't find any solutions with our main approach, try the simpler backup approach
        if not all_solutions and time.time() - start_time < timeout:
            # Try a simple approach focused on finding pairs of words
            for i, word1 in enumerate(valid_words):
                word1_counter = word_counters[word1]
                
                # For each word, find other words that can be formed with remaining letters
                remaining_letters = ''.join((Counter(letters) - word1_counter).elements())
                
                if not remaining_letters:  # If word1 uses all letters
                    # A single word that uses all letters is a valid solution if it's long enough
                    if len(word1) >= len(letters) * 0.75:  # Heuristic: word should use most letters
                        all_solutions.append([word1])
                        continue
                
                # Look for a second word that uses remaining letters and shares letters with word1
                for word2 in valid_words:
                    if word2 == word1:
                        continue
                        
                    # Check if words share any letters
                    if not set(word1) & set(word2):
                        continue
                    
                    # Check if word2 can be formed from remaining letters plus some from word1
                    # This allows for valid interlocking words
                    word2_counter = word_counters[word2]
                    combined_counter = word1_counter + Counter(remaining_letters)
                    
                    if all(combined_counter[letter] >= count for letter, count in word2_counter.items()):
                        # Check if together they use all or nearly all letters
                        combined_used = sum((word1_counter | word2_counter).values())
                        if combined_used >= len(letters) * 0.9:  # Allow for slight inefficiency
                            all_solutions.append([word1, word2])
                            if len(all_solutions) >= max_solutions:
                                break
                                
                if len(all_solutions) >= max_solutions:
                    break
        
        # Filter solutions to only keep valid ones (interconnected words)
        valid_solutions = self._filter_valid_solutions(all_solutions, max_count=20)
        
        return valid_solutions
    
    def _filter_valid_solutions(self, all_solutions, max_count=10):
        """Filter solutions to only keep those that are valid for Q-Less.
        
        Args:
            all_solutions: List of potential solutions
            max_count: Maximum number of solutions to return
            
        Returns:
            List of valid solutions
        """
        valid_solutions = []
        
        # Pre-compute letter sets for each word for faster comparisons
        solution_letter_sets = {}
        
        for solution in all_solutions:
            if len(solution) <= 1:
                continue  # Skip solutions with only one word
            
            # Cache letter sets for words in this solution
            for word in solution:
                if word not in solution_letter_sets:
                    solution_letter_sets[word] = set(word)
                    
            # Special fast path for two-word solutions - just check if they share any letters
            if len(solution) == 2:
                word1, word2 = solution
                word1_letters = solution_letter_sets[word1]
                word2_letters = solution_letter_sets[word2]
                
                if word1_letters & word2_letters:  # If words share any letters
                    valid_solutions.append(solution)
                    continue
                    
            # For more complex solutions, check graph connectivity
            if self._check_solution_connectivity(solution, solution_letter_sets):
                valid_solutions.append(solution)
                
                # Limit the number of valid solutions we store
                if len(valid_solutions) >= max_count:
                    break
        
        return valid_solutions
    
    def _check_solution_connectivity(self, solution, letter_sets=None):
        """Check if all words in a solution are connected through shared letters.
        
        Args:
            solution: List of words
            letter_sets: Precomputed letter sets for words (optimization)
            
        Returns:
            True if all words are connected, False otherwise
        """
        # Create a graph of connections
        if not letter_sets:
            letter_sets = {word: set(word) for word in solution}
            
        connections = defaultdict(set)
        for i, word1 in enumerate(solution):
            word1_letters = letter_sets[word1]
            for word2 in solution[i+1:]:
                word2_letters = letter_sets[word2]
                if word1_letters & word2_letters:  # If words share any letters
                    connections[word1].add(word2)
                    connections[word2].add(word1)
        
        # Check if all words are connected using BFS
        visited = set()
        queue = deque([solution[0]])  # Start with the first word (using deque for better performance)
        while queue:
            word = queue.popleft()
            visited.add(word)
            for connected_word in connections[word]:
                if connected_word not in visited:
                    queue.append(connected_word)
        
        # If we've visited all words, they're connected
        return len(visited) == len(solution)


class QlessVisualizer:
    """Handles visualization of Q-Less solutions"""
    
    @staticmethod
    def display_solution(solution):
        """Display a solution in a readable format with visualization.
        
        Args:
            solution: List of words that form a valid solution
        """
        print("\nHere's a potential solution:")
        print("--------------------------")
        for i, word in enumerate(solution, 1):
            print(f"Word {i}: {word}")
        
        print("\nPossible arrangement:")
        print("--------------------------")
        
        # Choose appropriate visualization based on solution size
        if len(solution) <= 3:
            # For small solutions, use the specialized methods
            if len(solution) == 2:
                QlessVisualizer._visualize_two_word_solution(solution)
            elif len(solution) == 3:
                QlessVisualizer._visualize_three_word_solution(solution)
            print("--------------------------")
        else:
            # For larger solutions, use the connection diagram
            QlessVisualizer._print_word_connections(solution)
        
    @staticmethod
    def _find_word_connections(solution):
        """Find all connections (shared letters) between words.
        
        Args:
            solution: List of words
            
        Returns:
            Dictionary mapping words to lists of connections
        """
        connections = defaultdict(list)
        # Pre-compute word letter sets
        letter_sets = {word: set(word) for word in solution}
        
        for i, word1 in enumerate(solution):
            for j, word2 in enumerate(solution[i+1:], i+1):
                shared = letter_sets[word1] & letter_sets[word2]
                if shared:
                    for letter in shared:
                        connections[word1].append((word2, letter))
                        connections[word2].append((word1, letter))
        
        return connections
    
    @staticmethod
    def _visualize_two_word_solution(solution):
        """Create a crossword-style visualization for a two-word solution.
        
        Args:
            solution: List of two words
        """
        word1, word2 = solution
        # Find all shared letters
        shared_letters = set(word1) & set(word2)
        if not shared_letters:
            # If no shared letters (shouldn't happen), just print the words
            print(word1)
            print(word2)
            return
        
        # Choose the best shared letter
        shared_letter = QlessVisualizer._choose_best_shared_letter(shared_letters)
        
        # Get optimal positions for the shared letter
        pos1 = QlessVisualizer._find_best_letter_position(word1, shared_letter)
        pos2 = QlessVisualizer._find_best_letter_position(word2, shared_letter)
        
        # Display with word1 horizontally and word2 vertically at the intersection
        indent = pos1
        
        # Print the vertical word (word2) with horizontal word (word1) at intersection
        for i in range(len(word2)):
            if i == pos2:
                # This is the row with the intersection
                print(word1)
            else:
                # Calculate the position for this letter
                print(' ' * indent + word2[i])
    
    @staticmethod
    def _choose_best_shared_letter(shared_letters):
        """Choose the best shared letter for visualization.
        
        Args:
            shared_letters: Set of shared letters
            
        Returns:
            The chosen shared letter
        """
        # If 'r' is a shared letter, prioritize it for intersection
        if 'r' in shared_letters:
            return 'r'
            
        # Try to find the most appropriate shared letter if there are multiple options
        priority_letters = ['e', 'a', 'o', 'i', 'u', 'n', 's', 't']
        for letter in priority_letters:
            if letter in shared_letters:
                return letter
        
        # Default to first letter
        return next(iter(shared_letters))
    
    @staticmethod
    def _find_best_letter_position(word, letter):
        """Find the best position for a shared letter within a word.
        
        Args:
            word: The word to search in
            letter: The letter to find
            
        Returns:
            Optimal position index
        """
        positions = [i for i, char in enumerate(word) if char == letter]
        
        # Default to first occurrence
        if not positions:
            return 0
            
        # Try to prefer positions closer to the middle of words for better layout
        if len(positions) > 1:
            # Choose position closest to the middle of the word
            middle = len(word) // 2
            return min(positions, key=lambda p: abs(p - middle))
            
        return positions[0]
    
    @staticmethod
    def _visualize_three_word_solution(solution):
        """Create a visualization for a three-word solution.
        
        Args:
            solution: List of three words
        """
        # Find all connections between the words
        word_connections = defaultdict(list)
        # Precompute word letter sets for faster operation
        letter_sets = {word: set(word) for word in solution}
        
        for word1 in solution:
            for word2 in solution:
                if word1 != word2:
                    shared = letter_sets[word1] & letter_sets[word2]
                    if shared:
                        for letter in shared:
                            pos1 = word1.find(letter)
                            pos2 = word2.find(letter)
                            word_connections[word1].append((word2, letter, pos1, pos2))
        
        # Try to find a word that connects to both others
        central_candidates = []
        for word in solution:
            connected_words = set(w for w, _, _, _ in word_connections.get(word, []))
            if len(connected_words) >= 2:
                central_candidates.append(word)
        
        # Choose the best central word (if available)
        if central_candidates:
            central_word = sorted(central_candidates, key=len, reverse=True)[0]
            QlessVisualizer._visualize_central_pattern(solution, central_word, word_connections)
        else:
            # Try to create a chain layout (A connects to B connects to C)
            chain = QlessVisualizer._find_word_chain(solution, word_connections)
            if chain:
                QlessVisualizer._visualize_chain_pattern(chain, word_connections)
            else:
                # Fallback to descriptive approach
                QlessVisualizer._visualize_descriptive(solution, word_connections)
    
    @staticmethod
    def _find_word_chain(solution, word_connections):
        """Find a chain of words where each connects to the next.
        
        Args:
            solution: List of words
            word_connections: Dictionary mapping words to their connections
            
        Returns:
            List of words in chain order, or None if no chain exists
        """
        # More efficient approach with dict keying
        connection_map = {word: set() for word in solution}
        for word in solution:
            for other_word, _, _, _ in word_connections.get(word, []):
                connection_map[word].add(other_word)
                
        # Try to find a chain of length 3
        for word1 in solution:
            for word2 in connection_map[word1]:
                for word3 in connection_map[word2]:
                    if word3 != word1:  # Avoid cycles
                        return [word1, word2, word3]
        return None
    
    @staticmethod
    def _visualize_central_pattern(solution, central_word, word_connections):
        """Visualize a solution with a central word that connects to others.
        
        Args:
            solution: List of words
            central_word: The central word that connects to others
            word_connections: Dictionary mapping words to their connections
        """
        # Place central word horizontally and others vertically
        connections_to_central = []
        vertical_words = [w for w in solution if w != central_word]
        
        # Find connections from central word to vertical words
        for v_word in vertical_words:
            # Check connections from central word to v_word
            for connection in word_connections.get(central_word, []):
                if connection[0] == v_word:
                    connections_to_central.append((v_word, connection[1], connection[2], connection[3]))
                    break
            
            # If no direct connection, check reverse direction
            if not any(v == v_word for v, _, _, _ in connections_to_central):
                for connection in word_connections.get(v_word, []):
                    if connection[0] == central_word:
                        connections_to_central.append((v_word, connection[1], connection[3], connection[2]))
                        break
        
        # Sort and adjust connections
        connections_to_central.sort(key=lambda x: x[2])
        QlessVisualizer._adjust_overlapping_connections(connections_to_central, central_word, word_connections)
        
        # Create the visual layout
        QlessVisualizer._create_central_pattern_grid(central_word, connections_to_central)
    
    @staticmethod
    def _adjust_overlapping_connections(connections, central_word, word_connections):
        """Adjust connections to avoid overlaps in the visualization."""
        h_positions = [c_pos for _, _, c_pos, _ in connections]
        if len(h_positions) == 2 and h_positions[0] == h_positions[1]:
            # If both vertical words want to connect at the same position,
            # adjust one of them to use a different shared letter if possible
            v_word, letter, c_pos, v_pos = connections[1]
            
            # Find an alternative connection
            for connection in word_connections.get(central_word, []):
                if connection[0] == v_word and connection[2] != h_positions[0]:
                    connections[1] = (v_word, connection[1], connection[2], connection[3])
                    break
    
    @staticmethod
    def _create_central_pattern_grid(central_word, connections):
        """Create and print a grid for a central pattern visualization."""
        # Calculate horizontal span
        max_h = len(central_word) - 1
        
        # Place all vertical words
        v_word_grids = {}
        
        for v_word, _, c_pos, v_pos in connections:
            # Calculate vertical bounds
            v_min = -v_pos
            v_max = len(v_word) - v_pos - 1
            
            # Create a grid for this vertical word
            v_grid = [' '] * (v_max - v_min + 1)
            for i in range(len(v_word)):
                v_grid[i - v_pos - v_min] = v_word[i]
            
            v_word_grids[v_word] = (v_grid, v_min, v_max, c_pos)
        
        # Determine overall vertical bounds
        min_v = min([v_min for _, v_min, _, _ in v_word_grids.values()])
        max_v = max([v_max for _, _, v_max, _ in v_word_grids.values()])
        
        # Create the final grid
        for v_idx in range(min_v, max_v + 1):
            if v_idx == 0:
                # This is the central word row
                print(central_word)
            else:
                # Check which vertical words have a letter in this row
                row = [' '] * (max_h + 1)
                for v_word, (v_grid, v_min, v_max, h_pos) in v_word_grids.items():
                    grid_idx = v_idx - v_min
                    if 0 <= grid_idx < len(v_grid):
                        row[h_pos] = v_grid[grid_idx]
                print(''.join(row))
    
    @staticmethod
    def _visualize_chain_pattern(chain, word_connections):
        """Visualize a chain pattern (A connects to B connects to C)."""
        word1, word2, word3 = chain
        
        # Find connection between word1 and word2
        connection_1_2 = None
        for w2, letter, pos1, pos2 in word_connections.get(word1, []):
            if w2 == word2:
                connection_1_2 = (letter, pos1, pos2)
                break
        
        # Find connection between word2 and word3
        connection_2_3 = None
        for w3, letter, pos2, pos3 in word_connections.get(word2, []):
            if w3 == word3:
                connection_2_3 = (letter, pos2, pos3)
                break
        
        if not connection_1_2 or not connection_2_3:
            # Fallback to simple approach
            print(f"{word1}\n{word2}\n{word3}")
            return
        
        # Place word1 horizontally, word2 vertically at the intersection
        letter1, pos1, pos2 = connection_1_2
        letter2, pos2_in_word2, pos3 = connection_2_3
        
        # Create the visualization
        for i in range(len(word2)):
            if i == pos2:
                # This is the row with the intersection with word1
                print(word1)
            else:
                # This is a row with just the letter from word2
                print(' ' * pos1 + word2[i])
        
        # Indicate the connection to word3
        print(f"\nAnd {word3} connects to {word2} through '{letter2}'")
    
    @staticmethod
    def _visualize_descriptive(solution, word_connections):
        """Create a descriptive (text-based) visualization when other methods fail."""
        print("Words in solution:")
        for word in solution:
            print(f"  {word}")
        
        print("\nThese words connect through shared letters:")
        word_pairs_shown = set()
        for word1 in solution:
            for word2, letter, _, _ in word_connections.get(word1, []):
                pair_key = tuple(sorted([word1, word2]))
                if pair_key not in word_pairs_shown:
                    print(f"  {word1} and {word2} share '{letter}'")
                    word_pairs_shown.add(pair_key)
    
    @staticmethod
    def _print_word_connections(solution):
        """Print a simplified diagram showing how words connect."""
        # Create a graph of word connections
        connections = defaultdict(list)
        # Pre-compute letter sets for better performance
        letter_sets = {word: set(word) for word in solution}
        
        for i, word1 in enumerate(solution):
            for word2 in solution[i+1:]:
                shared = letter_sets[word1] & letter_sets[word2]
                if shared:
                    connections[word1].append((word2, ", ".join(shared)))
                    connections[word2].append((word1, ", ".join(shared)))
        
        # List all the words in the solution
        for word in solution:
            print(word)
        
        print("\n(Words connect through shared letters:)")
        # Print the connections
        for word in solution:
            if word in connections:
                print(f"{word} connects to:")
                for connected_word, shared_letters in connections[word]:
                    print(f"  - {connected_word} (sharing: {shared_letters})")
        
        print("--------------------------")


class QlessGame:
    """Main game controller class"""
    
    def __init__(self, word_list_path="wordlist-20210729.txt"):
        """Initialize the game."""
        self.word_list = WordList.load(word_list_path)
        self.solver = QlessSolver(self.word_list)
        
    def run(self):
        """Run the main game loop"""
        print("Got your dice? Let's check if your roll is solvable!")
        print("Please enter a set of letters:")

        while True:
            user_input = self._get_valid_input()
            if not user_input:
                continue
                
            solutions = self.solver.find_all_solutions(user_input)
            
            if solutions:
                self._handle_solutions(solutions)
            else:
                print("This set is not solvable. Roll again!")

            if not self._should_continue():
                break

        print("See ya!")
    
    def _get_valid_input(self):
        """Get and validate user input."""
        user_input = input("> ").strip()

        if not user_input.isalpha():
            print("Input must contain only letters. Please try again.")
            return None

        if len(user_input) != 12:
            print("Input must be exactly 12 letters. Please try again.")
            return None

        return user_input.lower()
    
    def _handle_solutions(self, solutions):
        """Handle displaying solutions to the user."""
        print(f"This set is solvable! Found {len(solutions)} different solutions.")
        
        # Keep track of which solutions have been shown
        shown_solutions = set()
        
        while True:
            option = self._get_solution_option(shown_solutions)
            
            if option == "no":
                break
            elif option == "show_all":
                self._show_all_solutions(solutions, shown_solutions)
                break
            elif option == "yes":
                self._show_next_solution(solutions, shown_solutions)
            else:
                print("Please enter 'yes'/'y', 'no'/'n', or 'show all'.")
    
    def _get_solution_option(self, shown_solutions):
        """Get the user's solution display option."""
        if not shown_solutions:
            prompt = "Would you like to see a potential solution? (yes/y, no/n, or show all)\n> "
        else:
            prompt = "Would you like to see another potential solution? (yes/y, no/n, or show all)\n> "
        
        option = input(prompt).strip().lower()
        
        if option in ["no", "n"]:
            return "no"
        elif option == "show all":
            return "show_all"
        elif option in ["yes", "y"]:
            return "yes"
        else:
            return "invalid"
    
    def _show_all_solutions(self, solutions, shown_solutions):
        """Show all remaining solutions."""
        print("\nShowing all potential solutions:")
        print("================================")
        
        for i, sol in enumerate(solutions):
            if i not in shown_solutions:
                print(f"\nSolution {i+1}:")
                QlessVisualizer.display_solution(sol)
                shown_solutions.add(i)
        
        print("\nAll possible solutions have been shown!")
    
    def _show_next_solution(self, solutions, shown_solutions):
        """Show the next unseen solution."""
        remaining_solutions = [i for i in range(len(solutions)) if i not in shown_solutions]
        
        if not remaining_solutions:
            print("\nAll possible solutions have been shown!")
            return
        
        next_solution_idx = len(shown_solutions)
        QlessVisualizer.display_solution(solutions[next_solution_idx])
        shown_solutions.add(next_solution_idx)
    
    def _should_continue(self):
        """Check if the user wants to continue."""
        print("\nWould you like to check another roll? (yes/y, no/n)")
        retry = input("> ").strip().lower()
        return retry in ["yes", "y"]


if __name__ == "__main__":
    game = QlessGame()
    game.run()
