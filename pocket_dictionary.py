#!/usr/bin/env python
# main.py
import argparse
import json
import random
import sys
import requests
import os # Import the os module to handle file paths

# --- Configuration ---
# Define the directory and file path for storing words.
# os.path.expanduser("~") gets the path to the user's home directory.
WORD_DIR = os.path.expanduser("~/.word_dictionary")
WORD_FILE = os.path.join(WORD_DIR, "word.txt")
# The API endpoint for the dictionary.
DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

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

# --- Core Dictionary Functions ---

def lookup_word(word):
    """
    Looks up a word using the dictionary API, prints its meaning,
    and saves it to the file.
    """
    word = word.lower().strip()
    print(f"🔍 Looking up '{word}'...")
    try:
        response = requests.get(f"{DICTIONARY_API_URL}{word}")
        # Raise an exception for bad status codes (like 404, 500)
        response.raise_for_status()

        data = response.json()

        # --- Print Formatted Output ---
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

        # If the lookup was successful, save the word.
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


# --- Main Execution ---

def main():
    """
    Main function to parse command-line arguments and run the program.
    """
    parser = argparse.ArgumentParser(
        description="A personal dictionary and word-learning tool.",
        epilog="Example: python main.py lookup hello"
    )
    # This creates mutually exclusive commands, so you can only run one at a time.
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Command: lookup
    lookup_parser = subparsers.add_parser("lookup", help="Look up a word's definition and save it.")
    lookup_parser.add_argument("word", type=str, help="The word to look up.")

    # Command: add
    add_parser = subparsers.add_parser("add", help="Manually add a word to your list.")
    add_parser.add_argument("word", type=str, help="The word to add.")

    # Command: remove
    remove_parser = subparsers.add_parser("remove", help="Remove a word from your list.")
    remove_parser.add_argument("word", type=str, help="The word to remove.")

    # Command: random
    subparsers.add_parser("random", help="Start a random word quiz from your list.")

    # Command: list
    subparsers.add_parser("list", help="Show all words in your list.")

    args = parser.parse_args()

    # --- Execute the chosen command ---
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

