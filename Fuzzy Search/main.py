""" 
This script is used for highlighting keywords in the body of an email that are given as input, uses 'Levenshtein Distance Algorithm' to do the fuzzy search
"""

import re
import time
import html
import json

import pandas as pd

from Levenshtein import ratio


def clean_input(input_string, char_list):
    """Cleans the input string making it ready for processing
    Cleaning steps:
        1. Remove english stop words
        2. Remove line feed characters
        3. Remove emails
        4. Remove any characters that are not present in the restricted list character set
        5. Remove Vincent's email signature
        6. Remove URLs

    Args:
        input_string (str): Input string to be cleaned
        char_list (list[str]): List of distinct characters found in the Restricted List strings
        
    Returns:
        str: Cleaned string
    """
    
    # Get stopwords list
    with open('stopwords.txt', 'r') as s:
        stop_words = s.read()
    stop_words = stop_words.split()
    
    # Get URL regex list
    with open('url_regex.txt', 'r', encoding='utf-8') as s:
        url_re = s.read().strip()
   
    # Remove stop words (e.g. 'and', 'or', etc. )
    output = ' '.join([x for x in input_string.split() if x.lower() not in stop_words])
    
    # Remove line feed characters
    output = re.sub('[\\n\\r\\\\]', ' ', output) 
    
    # Remove emails
    output = re.sub(r'[\w\.-]+@[\w\.-]+', '', output)
    
    # Remove any character that is not in the restricted list
    output = ''.join([x for x in output if x in char_list])
    
    # Remove URLs
    output = re.sub(url_re, '', output)
    
    print(output)
    return output


def get_ngrams(list_str, ngrams_value):
    """Generates ngrams of length 'ngrams_value' from a list of strings

    Args:
        list_str (list[str]): Input for generating ngrams
        ngrams_value (int32): The length of the ngrams

    Returns:
        list[str]: List of generated ngrams
    """
    result = []
    i = 0   
   
    while i <= len(list_str) - ngrams_value:
        j = 0
        temp_str = ''
        while j < ngrams_value:
            temp_str = temp_str + ' ' + list_str[i+j]
            j = j + 1
        result.append(temp_str.strip())
        i = i + 1

    return result


def get_matches(content_list, restricted_list, similarity, restricted_type):
    """Uses 'Levenshtein Distance Algorithm' to get a ratio score between ngrams from the input and the restricted list words

    Args:
        content_list (list[str]): List of ngram content of the email boy
        restricted_list (list[str]): List of restricted words data
        similarity (float): Maximum similarity ratio allowed for a match to be considered valid
        restricted_type (str): What restricted list is being used

    Returns:
        pandas.DataFrame: Dataframe with the following columns -> ['matched_word', 'restricted_word', 'similarity']
    """
    matches = []
    pattern = re.compile(r'[^a-zA-Z0-9]')
    strip_pattern = re.compile(r'[^\w\d\s\.]')
    
    for input in content_list:
        if len(input) == 0 or input.isspace():
                continue
        
        # Remove all non alphanum characters except dot at the end of the input
        if re.match(strip_pattern, input[-1]):
            input = input[:-1]
            
        for res in restricted_list: 
                
            # Tickers usually are short and are comprised of alphanumerics
            # So we are removing anything else from the found match    
            if restricted_type == 'ticker':
                r = ratio(re.sub(pattern, '', input), res, score_cutoff=similarity)
            else:
                r = ratio(input, res, score_cutoff=similarity)
                
            if r > similarity:
                matches.append((input.strip(), res, r))
                
    return pd.DataFrame({
        'matched_word': [x[0] for x in matches],
        'restricted_word': [x[1] for x in matches],
        'similarity': [x[2] for x in matches]
    })
    
    
def get_list_of_chars(json_data_issuer, json_data_ticker):
    """Retrieves the distinct characters from the Restricted List strings

    Args:
        json_data_issuer (dict[str: object]): Json dictionary for the Issuer restricted data
        json_data_ticker (dict[str: object]): Json dictionary for the Ticker restricted data

    Returns:
        list[str]: List of distinct characters found in the Restricted List strings
    """
    
    issuer_list = json_data_issuer['restricted_words']
    ticker_list = json_data_ticker['restricted_words']
    
    combined_string = ''.join(issuer_list) + ''.join(ticker_list)
    
    return list(set(combined_string))


def fuzzy_search(input_string, restricted_words, similarity, restricted_type):
    """Fuzzy search function that uses the 'Levenshtein Distance Algorithm' to find matches of given restricted words in an email body

    Args:
        input_string (str): String input of an email body
        restricted_words (list[str]): List of restricted words the search is based upon
        similarity (float): Max similarity score that dictates if a word is included in the search output or not
        restricted_type (str): What restricted list is being used
        
    Returns:
        pandas.DataFrame: Dataframe with the following columns -> ['matched_word', 'restricted_word', 'similarity']
    """
    
    # Get list of tokens
    content_list = input_string.replace('\n', ' ').split()
    
    # Init time
    t1 = time.time()

    # Get max word length of restricted list items
    restricted_words.sort(key=lambda x: len(x.split()), reverse=True)
    max_word_len = len(restricted_words[0].split())

    # Init dataframe
    col_names = ['matched_word', 'restricted_word', 'similarity']
    matches_df = pd.DataFrame(columns=col_names)

    while max_word_len > 0:
        # Use only the current length restricted words
        temp = [elem for elem in restricted_words if (len(elem.split()) == max_word_len)]
        
        if len(temp) > 0:
            
            # Get ngrams with the length of 'max_world_len' from the email body input
            ngrams = get_ngrams(content_list, max_word_len)
            
            # Get fuzzy matches
            current_matches = get_matches(ngrams, temp, similarity, restricted_type)

            # Add matches to dataframe ['matched_word', 'restricted_word', 'similarity']
            matches_df = pd.concat([matches_df, current_matches])
        
        max_word_len -= 1
        
    # Sort dataframe by similarity column
    matches_df = matches_df.sort_values(by=['similarity'], ascending=False)
    
    # Remove duplicates so we don't clutter the output
    matches_df = matches_df.drop_duplicates(subset=['matched_word'], keep='first').reset_index(drop=True)
    matches_df = matches_df.drop_duplicates(subset=['restricted_word'], keep='first').reset_index(drop=True)
    
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(matches_df)
    
    t = time.time() - t1
    print(f'{restricted_type.capitalize()} time: {t}')

    return matches_df


def main(email_body, json_data_issuer, json_data_ticker, char_list):
    """Main driver function that integrates the fuzzy search with highlighting the words in the email body

    Args:
        email_body_HTML (str): HTML string input of an email body
        json_data_issuer (dict[str: object]): Json dictionary for the Issuer restricted data
        json_data_ticker (dict[str: object]): Json dictionary for the Ticker restricted data
        char_list (list[str]): List of distinct characters found in the Restricted List strings

    Returns:
        str: HTML email body with highlighted words
    """
    
    # Init variables
    html_tag_re = re.compile(r'<(.|\n)*?>')
    result_HTML = '<html content=Word.Document><body><table width="100%"> \
                    <tr><th width="75%"></th></tr> \
                    <tr><td><span style="padding: 0; margin: 0">%EMAIL%</span></td> \
                    <td style="margin: 0; padding: 0"><span>%RESULTS%</span></td></tr></table></body></html>'
                    
    result_table = '<table border=1 frame=void rules=rows> \
                    <caption align=top style="padding-bottom: 12.5px; font-size: 16px; text-align: left"><span style="color: #FF4500; font-size: 25px; padding: 0px; margin: 0px">&#8226; </span> \
                    Red text is used for words that are matched but not highlighted.</caption> \
                    <tr style="background-color: #99C2FF"><th width="37.5%" style="padding-bottom: 7.5px; padding-top: 8.5px" align=left>Matched Word</th> \
                    <th width="37.5%" style="padding-bottom: 7.5px; padding-top: 8.5px" align=left>Restricted Word</th> \
                    <th width="25%" style="padding-bottom: 7.5px; padding-top: 8.5px" align=right>Match %</th></tr>'

    # Retrieve the body of the HTML email
    body_HTML = re.search('<body.*?>(.*?)<\/body>', email_body, flags=re.DOTALL|re.IGNORECASE).group(1)
    updated_body_HTML = body_HTML
    body_string_content = html.unescape(re.sub(html_tag_re, ' ', body_HTML))

    # Clean data before processing
    cleaned_content = clean_input(body_string_content, char_list)

    # Get matches
    matches_df_issuer = fuzzy_search(cleaned_content, json_data_issuer['restricted_words'], float(json_data_issuer['similarity_ratio']), 'issuer')
    matches_df_ticker = fuzzy_search(cleaned_content, json_data_ticker['restricted_words'], float(json_data_ticker['similarity_ratio']), 'ticker')
    matches_df = pd.concat([matches_df_issuer, matches_df_ticker]).reset_index(drop=True)
    
    # Build matches table
    for idx, row in matches_df.iterrows():
        
        if idx == 0 and len(matches_df_issuer.index) > 0:
            result_table = f'{result_table}<tr><center><td colspan="3" style="text-align: center; padding: 5px"><b>Issuer Names</b></td></center></tr>' 
        elif idx == len(matches_df_issuer.index) and len(matches_df_ticker.index) > 0:
            result_table = f'{result_table}<tr><center><td colspan="3" style="text-align: center; padding: 5px"><b>Tickers</b></td></center></tr>' 
        
        word, restricted_word_match, max_ratio = row['matched_word'], row['restricted_word'], row['similarity']
        
        # These type of matches will give too much noise while highlighting them
        # So we just skip, but still keep them in the output table with the color red
        # Or it just could not be highlighted because of the cleaning process
        if (len(word) < 3 and (not word.isalnum() or word.isdigit())) or len(word) == 1:
            result_table = f'{result_table}<tr><center><td style="color: #FF4500">{word}</td><td style="color: #FF4500">{restricted_word_match}</td><td style="color: #FF4500" align=right>{(max_ratio / 1 * 100):.2f}</td></center></tr>'
            continue
        
        # Build regex used for highlighting
        word_sub_re = re.escape(word).replace('\\ ', '[\\n| ]*')
        updated_body_HTML, subs_made = re.subn(word_sub_re, f'<span style="background-color: #FFFF00">{word}</span>', updated_body_HTML)
        
        # If the match could not be highlighted because of mismatches caused by the cleaning process of the string
        if subs_made == 0:
            result_table = f'{result_table}<tr><center><td style="color: #FF4500">{word}</td><td style="color: #FF4500">{restricted_word_match}</td><td style="color: #FF4500" align=right>{(max_ratio / 1 * 100):.2f}</td></center></tr>'
            continue
            
        result_table = f'{result_table}<tr><center><td>{word}</td><td>{restricted_word_match}</td><td align=right>{(max_ratio / 1 * 100):.2f}</td></center></tr>'
        
    # Build output email to be sent to the business
    email_body = email_body.replace(body_HTML, updated_body_HTML)
    result_table = result_table + '</table>'
    result_HTML = result_HTML.replace('%EMAIL%', email_body).replace('%RESULTS%', result_table)

    return result_HTML

        
if __name__ == '__main__':
    
    # Read input HTML file
    with open('input.html', encoding='utf-8') as h:
        content = h.read()
        
    input_path_issuer = "jsonInputIssuer.json"
    input_path_ticker = "jsonInputTicker.json"
    
    # Read input json file that contains the similarity score and the restricted list for Issuers
    with open(input_path_issuer,'r', encoding='utf-8') as j:
        json_data_issuer = json.load(j)
        print('Issuer Json File read successfully')
    
    # Read input json file that contains the similarity score and the restricted list for Tickers
    with open(input_path_ticker,'r', encoding='utf-8') as j:
        json_data_ticker = json.load(j)
        print('Ticker Json File read successfully')
        
    # Get list of characters from json files to use for cleaning
    char_list = get_list_of_chars(json_data_ticker, json_data_issuer)
        
    # Clean restricted words of unnecessary spaces
    json_data_issuer['restricted_words'] = [re.sub('\s\s+', ' ', x.strip()) for x in json_data_issuer['restricted_words']]
    
    # Call main driver function
    html_content = main(content, json_data_issuer, json_data_ticker, char_list)

    # Write to output HTML file 
    with open('output.html', "w", encoding='utf-8') as h:
        h.write(html_content)
