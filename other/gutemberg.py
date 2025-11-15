import nltk
from nltk import corpus
from nltk.corpus import gutenberg
from collections import Counter

# Download the necessary data (only needs to be done once)
nltk.download('gutenberg')
nltk.download('averaged_perceptron_tagger', quiet=True)
#nltk.download('averaged_perceptron_tagger')
nltk.download('universal_tagset')
nltk.download('punkt')  # Also download tokenizer if needed
from nltk.tokenize import word_tokenize
print("Processing Gutenberg corpus...")

# Get all words from the Gutenberg corpus included in NLTK
words = gutenberg.words()

# Tag the parts of speech (POS)
# This uses the Universal Tagset: ADJ (Adjective), VERB (Verb), NOUN (Noun)
tagged_words = nltk.pos_tag(words, tagset='universal')

# Create sets to store unique words (prevents duplicates)
adjectives = set()
verbs = set()
nouns = set()

# Filter words into categories
# We define a "word" as having only alphabetical characters to avoid punctuation
for word, tag in tagged_words:
    if word.isalpha(): 
        clean_word = word.lower()
        if tag == 'ADJ':
            adjectives.add(clean_word)
        elif tag == 'VERB':
            verbs.add(clean_word)
        elif tag == 'NOUN':
            nouns.add(clean_word)

# Function to save to file
def save_to_file(filename, word_set):
    with open(filename, 'w', encoding='utf-8') as f:
        # Sort alphabetically for easier pasting
        for w in sorted(list(word_set)):
            f.write(f"{w}\n")
    print(f"Saved {len(word_set)} words to {filename}")

# Save the files
save_to_file('zynthalic_adjectives.txt', adjectives)
save_to_file('zynthalic_verbs.txt', verbs)
save_to_file('zynthalic_nouns.txt', nouns)

print("Done! You can now paste these files into Anchor.")