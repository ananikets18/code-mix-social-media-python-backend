# Romanized Dictionaries

This directory contains romanized-to-native-script dictionaries for multiple Indian languages. These dictionaries are used to convert casual romanized text into proper native scripts before translation.

## 📁 Available Dictionaries

| Language | ISO Code | Script | Word Count | File |
|----------|----------|--------|------------|------|
| **Hindi** | hin/hi | Devanagari | 150+ | `hindi.json` |
| **Marathi** | mar/mr | Devanagari | 120+ | `marathi.json` |
| **Bengali** | ben/bn | Bengali | 100+ | `bengali.json` |
| **Tamil** | tam/ta | Tamil | 90+ | `tamil.json` |
| **Telugu** | tel/te | Telugu | 85+ | `telugu.json` |
| **Punjabi** | pan/pa | Gurmukhi | 80+ | `punjabi.json` |

## 📊 Dictionary Structure

Each JSON file contains:

```json
{
  "language": "Language Name",
  "script": "Script Name",
  "iso_code": "3-letter ISO code",
  "version": "1.0",
  "word_count": 150,
  "categories": {
    "time": { "aaj": "आज", "kal": "कल" },
    "pronouns": { "mai": "मैं", "tum": "तुम" },
    "verbs": { "hai": "है", "kar": "कर" },
    "adjectives": { "bahut": "बहुत", "khush": "खुश" },
    "question_words": { "kya": "क्या", "kaise": "कैसे" },
    "negation": { "nahi": "नहीं" },
    "affirmation": { "haan": "हाँ" },
    "family": { "maa": "माँ", "bhai": "भाई" },
    "common_nouns": { "ghar": "घर", "kaam": "काम" },
    "borrowed_words": { "phone": "फोन", "traffic": "ट्रैफिक" }
  }
}
```

## 🎯 Categories

Each dictionary is organized into these categories:

1. **time** - Time-related words (today, tomorrow, now, etc.)
2. **pronouns** - Personal and possessive pronouns
3. **verbs** - Common verbs and their forms
4. **adjectives** - Descriptive words (good, bad, happy, etc.)
5. **question_words** - Question words (what, when, where, why, etc.)
6. **negation** - Negative words (no, not, never, etc.)
7. **affirmation** - Affirmative words (yes, okay, sure, etc.)
8. **family** - Family members and relations
9. **common_nouns** - Frequently used nouns
10. **borrowed_words** - English/borrowed words commonly used in Indian languages

## 🔧 Usage

The dictionaries are automatically loaded by the translation module:

```python
from translation import translate_text

# Romanized Marathi text
result = translate_text(
    text="Mi aaj khup khush ahe",
    target_lang="en",
    is_romanized=True
)

# Converts: "Mi aaj khup khush ahe" → "मी आज खूप खुश आहे"
# Translates: "I am very happy today"
```

## ➕ Adding New Words

To add new words to a dictionary:

1. Open the respective JSON file
2. Find the appropriate category
3. Add the romanized → native script mapping
4. Update the `word_count` field
5. Save the file (automatic reload in API)

**Example:**
```json
"adjectives": {
  "existing_word": "existing_translation",
  "new_word": "नया_अनुवाद"
}
```

## 🌐 Adding New Languages

To add support for a new language:

1. Create a new JSON file: `language_name.json`
2. Follow the structure shown above
3. Include ISO codes (both 2-letter and 3-letter)
4. Categorize words properly
5. Add at least 50-80 common words
6. Update `translation.py` to include the new language mapping

## 📈 Future Enhancements

- [ ] Add Gujarati dictionary
- [ ] Add Kannada dictionary
- [ ] Add Malayalam dictionary
- [ ] Add Urdu dictionary
- [ ] Add more verb conjugations
- [ ] Add slang/informal words
- [ ] Add regional variations
- [ ] Community contributions via GitHub

## 🤝 Contributing

To contribute:

1. Add new words maintaining the JSON structure
2. Test with romanized text examples
3. Ensure proper categorization
4. Update word count
5. Submit changes

## 📝 Notes

- **Case Sensitivity**: All romanized words are stored in lowercase
- **Variations**: Multiple romanizations can map to same native word
  - Example: `mai`, `main`, `mein` all → `मैं`
- **Context**: These are common word mappings, may not cover all contexts
- **Accuracy**: ~70-80% coverage for casual conversational text
- **Priority**: Focus on most frequently used words first

## 🔗 Related Files

- `translation.py` - Loads and uses these dictionaries
- `preprocessing.py` - Detects romanized Indian languages
- `main.py` - Integration with analysis pipeline

---

**Last Updated**: November 2025  
**Maintainer**: NLP Project Team
