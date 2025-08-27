#!/usr/bin/env python
import argparse
import json
import random
import sys
import requests
import os # Import the os module to handle file paths

# --- Configuration ---
# Define the directory and file path for storing words and weights.
# os.path.expanduser("~") gets the path to the user's home directory.
WORD_DIR = os.path.expanduser("~/.word_dictionary")
WORD_FILE = os.path.join(WORD_DIR, "word.txt")
WEIGHT_FILE = os.path.join(WORD_DIR, "weights.json")
# The API endpoint for the dictionary.
DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
# Default weight for new words and weight adjustment values.
DEFAULT_WEIGHT = 5
WEIGHT_INCREASE = 2 # Increase weight by this much on wrong answer
WEIGHT_DECREASE = 1 # Decrease weight by this much on correct answer

# --- Helper Functions for File Operations ---

def get_words_from_file():
    """
    Reads all words from the WORD_FILE.
    Creates the directory and file if they don't exist.
    Returns a list of words.
    """
    try:
        # Ensure the directory exists before trying to access the file.
        os.makedirs(WORD_DIR, exist_ok=True)
        with open(WORD_FILE, "r") as f:
            # Read lines, strip whitespace from each, and filter out empty lines.
            words = [line.strip() for line in f.readlines() if line.strip()]
        return words
    except FileNotFoundError:
        # If the file doesn't exist, create it and return an empty list.
        with open(WORD_FILE, "w") as f:
            pass # Just create the file
        return []

def save_word_to_file(word):
    """
    Saves a single word to the WORD_FILE if it's not already there.
    """
    word = word.lower().strip()
    existing_words = get_words_from_file()
    if word not in existing_words:
        # Append the new word to the end of the file.
        with open(WORD_FILE, "a") as f:
            f.write(f"{word}\n")
        print(f"✅ Word '{word}' has been added to your list.")
    else:
        print(f"ℹ️ Word '{word}' is already in your list.")

def remove_word_from_file(word):
    """
    Removes a word from the WORD_FILE.
    """
    word = word.lower().strip()
    words = get_words_from_file()
    if word in words:
        words.remove(word)
        # Rewrite the file with the updated list of words.
        with open(WORD_FILE, "w") as f:
            for w in words:
                f.write(f"{w}\n")
        print(f"🗑️ Word '{word}' has been removed from your list.")
    else:
        print(f"❌ Word '{word}' was not found in your list.")

# --- Weight Management Functions ---

def load_weights():
    """
    Loads word weights from WEIGHT_FILE.
    Synchronizes with WORD_FILE, adding new words and removing old ones.
    """
    words = get_words_from_file()
    try:
        with open(WEIGHT_FILE, 'r') as f:
            weights = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        weights = {}

    # Add new words from word.txt to weights with default weight
    for word in words:
        if word not in weights:
            weights[word] = DEFAULT_WEIGHT

    # Remove words from weights that are no longer in word.txt
    words_to_remove = [word for word in weights if word not in words]
    for word in words_to_remove:
        del weights[word]

    return weights

def save_weights(weights):
    """Saves the weights dictionary to the WEIGHT_FILE."""
    with open(WEIGHT_FILE, 'w') as f:
        json.dump(weights, f, indent=4)

# --- Core Dictionary Functions ---

def get_definitions_for_word(word):
    """
    Fetches only the definitions for a word from the API.
    Returns a formatted string of definitions, or None on failure.
    """
    try:
        response = requests.get(f"{DICTIONARY_API_URL}{word}")
        response.raise_for_status()
        data = response.json()

        definitions_text = []
        for meaning in data[0]['meanings']:
            definitions_text.append(f"\n🔹 Part of Speech: {meaning['partOfSpeech']}")
            for i, definition in enumerate(meaning['definitions'], 1):
                definitions_text.append(f"  {i}. {definition['definition']}")
        return "".join(definitions_text)
    except (requests.exceptions.RequestException, KeyError, IndexError):
        return None

def lookup_word(word):
    """
    Looks up a word using the dictionary API, prints its meaning,
    and saves it to the file.
    """
    word = word.lower().strip()
    print(f"🔍 Looking up '{word}'...")
    try:
        response = requests.get(f"{DICTIONARY_API_URL}{word}")
        response.raise_for_status()
        data = response.json()

        print("\n" + "="*40)
        print(f"📖 Definitions for: {data[0]['word']}")
        if 'phonetic' in data[0] and data[0]['phonetic']:
            print(f"   🗣️  Phonetic: {data[0]['phonetic']}")
        print("="*40)

        for meaning in data[0]['meanings']:
            print(f"\n🔹 Part of Speech: {meaning['partOfSpeech']}")
            for i, definition in enumerate(meaning['definitions'], 1):
                print(f"  {i}. {definition['definition']}")
                if 'example' in definition and definition['example']:
                    print(f"     Example: \"{definition['example']}\"")
        print("\n" + "="*40)

        save_word_to_file(word)

    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            print(f"❌ Could not find a definition for '{word}'. Please check the spelling.")
        else:
            print(f"An HTTP error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"A network error occurred: {err}")
    except (KeyError, IndexError):
        print("❌ Could not parse the dictionary response. The API format might have changed.")

def random_word_quiz():
    """
    Selects a random word from the file and prompts the user
    to recall its meaning.
    """
    words = get_words_from_file()
    if not words:
        print("❌ Your word list is empty! Look up some words first using the 'lookup' command.")
        return

    print("--- Random Word Quiz ---")
    print("A random word from your list will be shown.")
    print("Press ENTER to see the next word. Press Ctrl+C to quit.")
    print("-" * 26)

    try:
        while True:
            chosen_word = random.choice(words)
            print(f"\n🤔 What does this word mean? -> {chosen_word.upper()}")
            input("   (Press Enter for the next word...)")
    except KeyboardInterrupt:
        print("\n👋 Quiz finished. Keep practicing!")

def list_all_words():
    """Prints all the words currently saved in the file."""
    words = get_words_from_file()
    if not words:
        print("ℹ️ Your word list is empty.")
        return

    print("--- Your Saved Words ---")
    for i, word in enumerate(sorted(words), 1):
        print(f"{i}. {word}")
    print("------------------------")

def word_test():
    """
    Gives the user a definition and asks them to guess the word.
    Tracks stats and uses a weighted system for word selection.
    """
    weights = load_weights()
    if not weights:
        print("❌ Your word list is empty! Look up some words first using the 'lookup' command.")
        return

    print("--- Word Guessing Test ---")
    print("You will be given a definition. Guess the word!")
    print("Press Ctrl+C to quit at any time and see your score.")
    print("-" * 30)

    correct_count = 0
    incorrect_count = 0

    try:
        while True:
            word_list = list(weights.keys())
            weight_list = list(weights.values())

            chosen_word = random.choices(word_list, weights=weight_list, k=1)[0]
            definitions = get_definitions_for_word(chosen_word)

            if not definitions:
                print(f"Could not fetch definition for '{chosen_word}', skipping.")
                continue

            print("\n" + "="*40)
            print("DEFINITION(S):")
            print(definitions)
            print("="*40)

            guess = input("What is the word? -> ").lower().strip()

            if guess == chosen_word:
                print("✅ Correct!")
                correct_count += 1
                # Decrease weight for correct answers, minimum weight is 1
                weights[chosen_word] = max(1, weights[chosen_word] - WEIGHT_DECREASE)
            else:
                print(f"❌ Incorrect. The word was: {chosen_word}")
                incorrect_count += 1
                # Increase weight for incorrect answers
                weights[chosen_word] += WEIGHT_INCREASE

    except KeyboardInterrupt:
        print("\n\n--- Test Over ---")
        total = correct_count + incorrect_count
        if total > 0:
            success_rate = (correct_count / total) * 100
            fail_rate = (incorrect_count / total) * 100
            print(f"Correct: {correct_count}")
            print(f"Incorrect: {incorrect_count}")
            print(f"Success Rate: {success_rate:.2f}%")
            print(f"Failure Rate: {fail_rate:.2f}%")
        else:
            print("You didn't answer any questions.")

        print("\nSaving your progress...")
        save_weights(weights)
        print("👋 Keep practicing!")

# --- Main Execution ---

def main():
    """
    Main function to parse command-line arguments and run the program.
    """
    parser = argparse.ArgumentParser(
        description="A personal dictionary and word-learning tool.",
        epilog="Example: python main.py lookup hello"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    lookup_parser = subparsers.add_parser("lookup", help="Look up a word's definition and save it.")
    lookup_parser.add_argument("word", type=str, help="The word to look up.")

    add_parser = subparsers.add_parser("add", help="Manually add a word to your list.")
    add_parser.add_argument("word", type=str, help="The word to add.")

    remove_parser = subparsers.add_parser("remove", help="Remove a word from your list.")
    remove_parser.add_argument("word", type=str, help="The word to remove.")

    subparsers.add_parser("random", help="Start a random word quiz from your list.")

    subparsers.add_parser("list", help="Show all words in your list.")

    subparsers.add_parser("test", help="Test your knowledge by guessing words from definitions.")

    args = parser.parse_args()

    if args.command == "lookup":
        lookup_word(args.word)
    elif args.command == "add":
        save_word_to_file(args.word)
    elif args.command == "remove":
        remove_word_from_file(args.word)
    elif args.command == "random":
        random_word_quiz()
    elif args.command == "list":
        list_all_words()
    elif args.command == "test":
        word_test()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

