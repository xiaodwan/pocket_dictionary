#!/usr/bin/env python
# main.py
import argparse
import json
import random
import sys
import requests
import os

# --- Configuration ---
WORD_DIR = os.path.expanduser("~/.pocket_dictionary")
GROUP_FILE = os.path.join(WORD_DIR, "groups.json")
DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
DEFAULT_WEIGHT = 5
WEIGHT_INCREASE = 2
WEIGHT_DECREASE = 1

# --- Helper Functions for Group and Word Operations ---

def load_groups():
    """
    Loads groups and their words from the GROUP_FILE.
    Creates the directory and file if they don't exist.
    Returns a dictionary of groups.
    """
    try:
        os.makedirs(WORD_DIR, exist_ok=True)
        with open(GROUP_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"default": {}}

def save_groups(groups):
    """Saves the groups dictionary to the GROUP_FILE."""
    with open(GROUP_FILE, 'w') as f:
        json.dump(groups, f, indent=4)

def add_word_to_group(word, group_name="default"):
    """
    Adds a word to a specified group.
    """
    word = word.lower().strip()
    groups = load_groups()
    if group_name not in groups:
        groups[group_name] = {}
    if word not in groups[group_name]:
        groups[group_name][word] = {"weight": DEFAULT_WEIGHT, "seen_definitions": []}
        save_groups(groups)
        print(f"✅ Word '{word}' has been added to group '{group_name}'.")
    else:
        print(f"ℹ️ Word '{word}' is already in group '{group_name}'.")

def remove_word_from_group(word, group_name):
    """
    Removes a word from a specified group.
    """
    word = word.lower().strip()
    groups = load_groups()
    if group_name in groups and word in groups[group_name]:
        del groups[group_name][word]
        save_groups(groups)
        print(f"🗑️ Word '{word}' has been removed from group '{group_name}'.")
    else:
        print(f"❌ Word '{word}' not found in group '{group_name}'.")

def add_group(group_name):
    """
    Adds a new group.
    """
    groups = load_groups()
    if group_name not in groups:
        groups[group_name] = {}
        save_groups(groups)
        print(f"✅ Group '{group_name}' has been added.")
    else:
        print(f"ℹ️ Group '{group_name}' already exists.")

def remove_group(group_name):
    """
    Removes a group and all its words.
    """
    groups = load_groups()
    if group_name in groups:
        del groups[group_name]
        save_groups(groups)
        print(f"🗑️ Group '{group_name}' has been removed.")
    else:
        print(f"❌ Group '{group_name}' not found.")

def get_words_from_group(group_name=None):
    """
    Returns words from a specific group, or all words if no group is specified.
    """
    groups = load_groups()
    if group_name:
        return list(groups.get(group_name, {}).keys())
    else:
        all_words = []
        for group in groups.values():
            all_words.extend(group.keys())
        return all_words

# --- Core Dictionary Functions ---

def get_all_definitions(word):
    """
    Fetches all definitions for a word from the API.
    Returns a list of individual definition strings, or None on failure.
    """
    try:
        response = requests.get(f"{DICTIONARY_API_URL}{word}")
        response.raise_for_status()
        data = response.json()

        definitions_list = []
        for meaning in data[0]['meanings']:
            pos = meaning['partOfSpeech']
            for i, definition in enumerate(meaning['definitions'], 1):
                def_text = f"({pos}) {definition['definition']}"
                definitions_list.append(def_text)
        return definitions_list
    except (requests.exceptions.RequestException, KeyError, IndexError):
        return None

def lookup_word(word, group_name="default"):
    """
    Looks up a word, prints its meaning, and saves it to a group.
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

        add_word_to_group(word, group_name)

    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            print(f"❌ Could not find a definition for '{word}'. Please check the spelling.")
        else:
            print(f"An HTTP error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"A network error occurred: {err}")
    except (KeyError, IndexError):
        print("❌ Could not parse the dictionary response. The API format might have changed.")

def random_word_quiz(group_name=None):
    """
    Selects a random word from a group and prompts the user.
    """
    groups = load_groups()
    if not groups:
        print("❌ Your word list is empty!")
        return

    if group_name:
        if group_name not in groups or not groups[group_name]:
            print(f"❌ Group '{group_name}' is empty or does not exist.")
            return
        words = list(groups[group_name].keys())
    else:
        # Pick a random group
        random_group_name = random.choice(list(groups.keys()))
        words = list(groups[random_group_name].keys())
        print(f" quizzing you on words from the '{random_group_name}' group.")


    if not words:
        print("❌ No words found to quiz.")
        return

    print("--- Random Word Quiz ---")
    try:
        while True:
            chosen_word = random.choice(words)
            print(f"\n🤔 What does this word mean? -> {chosen_word.upper()}")
            input("   (Press Enter for the next word...)")
    except KeyboardInterrupt:
        print("\n👋 Quiz finished. Keep practicing!")

def list_all(group_name=None):
    """Prints all groups or words in a specific group."""
    groups = load_groups()
    if group_name:
        if group_name in groups:
            print(f"--- Words in '{group_name}' ---")
            for i, word in enumerate(sorted(groups[group_name].keys()), 1):
                print(f"{i}. {word}")
            print("------------------------")
        else:
            print(f"❌ Group '{group_name}' not found.")
    else:
        print("--- All Groups ---")
        for g_name in sorted(groups.keys()):
            print(f"- {g_name} ({len(groups[g_name])} words)")
        print("------------------")


def word_test(group_name=None):
    """
    Gives the user a single definition and asks them to guess the word.
    """
    groups = load_groups()
    if not groups:
        print("❌ Your word list is empty!")
        return

    if group_name:
        if group_name not in groups or not groups[group_name]:
            print(f"❌ Group '{group_name}' is empty or does not exist.")
            return
        weights_data = groups[group_name]
    else:
        # Pick a random group
        random_group_name = random.choice(list(groups.keys()))
        weights_data = groups[random_group_name]
        print(f" quizzing you on words from the '{random_group_name}' group.")


    if not weights_data:
        print("❌ No words found to test.")
        return

    print("--- Word Guessing Test ---")
    correct_count = 0
    incorrect_count = 0

    try:
        while True:
            word_list = list(weights_data.keys())
            weight_values = [d['weight'] for d in weights_data.values()]
            chosen_word = random.choices(word_list, weights=weight_values, k=1)[0]
            all_definitions = get_all_definitions(chosen_word)
            if not all_definitions:
                print(f"Could not fetch definitions for '{chosen_word}', skipping.")
                continue

            seen_definitions = weights_data[chosen_word]["seen_definitions"]
            unseen_definitions = [d for d in all_definitions if d not in seen_definitions]
            if not unseen_definitions:
                weights_data[chosen_word]["seen_definitions"] = []
                unseen_definitions = all_definitions
            definition_to_show = random.choice(unseen_definitions)

            print("\n" + "="*40)
            print("DEFINITION:")
            print(definition_to_show)
            print("="*40)

            guess = input("What is the word? -> ").lower().strip()

            if guess == chosen_word:
                print("✅ Correct!")
                correct_count += 1
                weights_data[chosen_word]['weight'] = max(1, weights_data[chosen_word]['weight'] - WEIGHT_DECREASE)
            else:
                print(f"❌ Incorrect. The word was: {chosen_word}")
                incorrect_count += 1
                weights_data[chosen_word]['weight'] += WEIGHT_INCREASE

            weights_data[chosen_word]["seen_definitions"].append(definition_to_show)

    except KeyboardInterrupt:
        print("\n\n--- Test Over ---")
        total = correct_count + incorrect_count
        if total > 0:
            success_rate = (correct_count / total) * 100
            print(f"Correct: {correct_count}, Incorrect: {incorrect_count}")
            print(f"Success Rate: {success_rate:.2f}%")
        else:
            print("You didn't answer any questions.")
        print("\nSaving your progress...")
        save_groups(groups)
        print("👋 Keep practicing!")

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="A personal dictionary and word-learning tool.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    lookup_parser = subparsers.add_parser("lookup", help="Look up a word's definition and save it.")
    lookup_parser.add_argument("word", type=str, help="The word to look up.")
    lookup_parser.add_argument("--group", type=str, default="default", help="The group to add the word to.")

    add_parser = subparsers.add_parser("add", help="Manually add a word to a group.")
    add_parser.add_argument("word", type=str, help="The word to add.")
    add_parser.add_argument("--group", type=str, default="default", help="The group to add the word to.")

    remove_parser = subparsers.add_parser("remove", help="Remove a word from a group.")
    remove_parser.add_argument("word", type=str, help="The word to remove.")
    remove_parser.add_argument("--group", type=str, required=True, help="The group to remove the word from.")

    add_group_parser = subparsers.add_parser("add_group", help="Add a new group.")
    add_group_parser.add_argument("group", type=str, help="The name of the group to add.")

    remove_group_parser = subparsers.add_parser("remove_group", help="Remove a group.")
    remove_group_parser.add_argument("group", type=str, help="The name of the group to remove.")

    random_parser = subparsers.add_parser("random", help="Start a random word quiz.")
    random_parser.add_argument("--group", type=str, help="The group to quiz on.")

    list_parser = subparsers.add_parser("list", help="List all groups or words in a group.")
    list_parser.add_argument("--group", type=str, help="The group to list words from.")

    test_parser = subparsers.add_parser("test", help="Test your knowledge.")
    test_parser.add_argument("--group", type=str, help="The group to test on.")

    args = parser.parse_args()

    if args.command == "lookup":
        lookup_word(args.word, args.group)
    elif args.command == "add":
        add_word_to_group(args.word, args.group)
    elif args.command == "remove":
        remove_word_from_group(args.word, args.group)
    elif args.command == "add_group":
        add_group(args.group)
    elif args.command == "remove_group":
        remove_group(args.group)
    elif args.command == "random":
        random_word_quiz(args.group)
    elif args.command == "list":
        list_all(args.group)
    elif args.command == "test":
        word_test(args.group)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()