import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords

# Extracting the article content and title from URL
def extract_article_content(url):
    try:
        request = requests.get(url)
        content = BeautifulSoup(request.text, "html.parser")

        # Removing header, footer, and other unwanted contents from the article
        for element in content(["header", "footer"]):
            element.decompose()

        # Getting the article title and text
        article_title = content.find("title").text.strip()
        article_text = ""

        # Main content extraction which is enclosed in the <div class> on each webpage
        article = content.find("div", class_="td-post-content tagdiv-type")
        if article:
            article_text = article.get_text()
            return article_title, article_text

        return None, None

    except Exception as e:
        print(f"Error while extracting the article from {url}: {e}")
        return None, None

# Storing the article content and title in text files
def save_content_to_textfile(url_id, article_title, article_text, output_directory="E:\\Blackcoffer_assignment\\TextFiles"):
    os.makedirs(output_directory, exist_ok=True)
    path = os.path.join(output_directory, f"{url_id}.txt")
    with open(path, "w", encoding="utf-8") as file:
        file.write(f"Title: {article_title}\n")
        file.write(article_text)

# Load positive and negative words from files
def dictionary(positive_words_file, negative_words_file):
    with open(positive_words_file, "r") as file:
        positive_words = set(file.read().splitlines())
    with open(negative_words_file, "r") as file:
        negative_words = set(file.read().splitlines())
    return positive_words, negative_words

# Calculating polarity and subjectivity scores
def scores(text, positive_words, negative_words):
    analyzer = SentimentIntensityAnalyzer()
    tokens = word_tokenize(text)

    positive_score = 0
    negative_score = 0

    for word in tokens:
        word = word.lower()
        if word.isalpha():
            if word in positive_words:
                positive_score += 1
            if word in negative_words:
                negative_score += 1

    polarity_score = (positive_score - negative_score) / (positive_score + negative_score) if (positive_score + negative_score) != 0 else 0
    subjectivity_score = (positive_score + negative_score) / len(tokens) if len(tokens) != 0 else 0
    
    return positive_score, negative_score, polarity_score, subjectivity_score

# Calculating length of the sentence
def sentence_length(sentences):
    total_words = sum(len(word_tokenize(sentence)) for sentence in sentences)
    total_sentences = len(sentences)
    return total_words / total_sentences if total_sentences > 0 else 0

# Counting syllables in a single word
def count_syllables(word):
    vowels = "aeiouAEIOU"
    count = 0
    word = word.lower()

    if word.endswith('e'):
        word = word[:-1]

    # Counting the syllables
    for index, letter in enumerate(word):
        if letter in vowels:
            if index == 0 or word[index - 1] not in vowels:
                count += 1

    return max(1, count)

# Complex words and metrics
def complex_words_metrics(text):
    words = word_tokenize(text)
    stop_words = set(stopwords.words("english"))
    filtered_words = [word for word in words if word.isalpha() and word.lower() not in stopwords.words('english')]

    total_word_count = len(filtered_words)
    complex_words_list = [word for word in filtered_words if count_syllables(word) > 2]
    complex_word_count = len(complex_words_list)

    total_syllables = sum(count_syllables(word) for word in filtered_words)
    avg_syllables_per_word = total_syllables / total_word_count if total_word_count > 0 else 0
    percentage_complex_words = (complex_word_count / total_word_count) if total_word_count > 0 else 0

    total_characters = sum(len(word) for word in filtered_words)
    avg_word_length = total_characters / total_word_count if total_word_count > 0 else 0

    return {
        "Total_Syllables": total_syllables,
        "Total_Word_Count": total_word_count,
        "Complex_Word_Count": complex_word_count,
        "Percentage_Complex_Words": percentage_complex_words,
        "Average_Syllables_Per_Word": avg_syllables_per_word,
        "Average_Word_Length": avg_word_length
    }

# Calculating personal pronouns count
def personal_pronouns(text):
    personal_pronouns = [
        "I", "me", "my", "mine", "we", "us", "our", "ours", 
        "you", "your", "yours", "he", "him", "his", "she", 
        "her", "hers", "it", "its", "they", "them", "their", 
        "theirs", "myself", "ourselves", "yourself", "yourselves", 
        "himself", "herself", "itself", "themselves"
    ]
    
    personal_pronouns_set = set(pronoun.lower() for pronoun in personal_pronouns)
    words = word_tokenize(text)
    words_lower = [word.lower() for word in words]
    return sum(1 for word in words_lower if word in personal_pronouns_set)

# Calculating fog index
def fog_index(sentence_length, percentage_complex_words):
    return 0.4 * (sentence_length + percentage_complex_words)

# Calculating average number of words per sentence
def avg_words(words, sentences):
    return len(words) / len(sentences) if len(sentences) > 0 else 0

# Main function to orchestrate extraction, analysis, and saving results
def main():
    input_file = "E:\\Blackcoffer_assignment\\Input.xlsx"
    articles_dir = "E:\\Blackcoffer_assignment\\TextFiles"
    positive_words_file = "E:\\Blackcoffer_assignment\\MasterDictionary\\positive-words.txt"
    negative_words_file = "E:\\Blackcoffer_assignment\\MasterDictionary\\negative-words.txt"
    
    positive_words, negative_words = dictionary(positive_words_file, negative_words_file)
    output_data = pd.read_excel(input_file)
    results = []
    
    for index, row in output_data.iterrows():
        url_id = row["URL_ID"]
        url = row.get("URL", "")
        article_file = os.path.join(articles_dir, f"{url_id}.txt")
        
        if os.path.exists(article_file):
            with open(article_file, 'r', encoding='utf-8') as file:
                article_text = file.read()
            
            pos_score, neg_score, pol_score, sub_score = scores(article_text, positive_words, negative_words)
            sentences = sent_tokenize(article_text)
            avg_sentence_len = sentence_length(sentences)
            complex_word_metrics = complex_words_metrics(article_text)
            pronoun_count = personal_pronouns(article_text)
            
            words = word_tokenize(article_text)
            avg_words_per_sentence = avg_words(words, sentences)
            
            fog_index_value = fog_index(avg_sentence_len, complex_word_metrics["Percentage_Complex_Words"])
            
            results.append({
                "URL_ID": url_id,
                "URL": url,
                "Positive_Score": pos_score,
                "Negative_Score": neg_score,
                "Polarity_Score": pol_score,
                "Subjectivity_Score": sub_score,
                "Avg_Sentence_Length": avg_sentence_len,
                "Percentage_Complex_Words": complex_word_metrics["Percentage_Complex_Words"],
                "Fog_Index": fog_index_value,
                "Avg_Words_Per_Sentence": avg_words_per_sentence,
                "Complex_Word_Count": complex_word_metrics["Complex_Word_Count"],
                "Word_Count": complex_word_metrics["Total_Word_Count"],
                "Syllable_Count_Per_Word": complex_word_metrics["Average_Syllables_Per_Word"],
                "Personal_Pronoun_Count": pronoun_count,
                "Avg_Word_Length": complex_word_metrics["Average_Word_Length"]
            })
    
    result_df = pd.DataFrame(results)
    output_file = "E:\\Blackcoffer_assignment\\Output.xlsx"
    result_df.to_excel(output_file, index=False)
    print(f"Analysis completed. Results saved to: {output_file}")

if __name__ == "__main__":
    main()
