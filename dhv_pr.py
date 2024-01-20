import requests                 # Simpler HTTP requests 
from bs4 import BeautifulSoup   # Python package for pulling data out of HTML and XML files
import pandas as pd             # Python package for data manipulation and analysis
import re                       # regular expressions
from tqdm import tqdm           # python for displaying progressbar 
from datetime import datetime   # python package to retireve DateTime

url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'              # IMDb Top 250 list link
url_text = requests.get(url).text                    # Get the session text for the link
url_soup = BeautifulSoup(url_text, 'html.parser')   # Get data from the HTML

template = 'https://www.imdb.com%s'

# Get the title links for all the pages
title_links = [template % a.attrs.get('href') for a in url_soup.select('td.titleColumn a')]

imdb_movie_list = []
# Getting the various fields and creating a list of objects with details
#   - ranking | movie_name | url | year | rating | vote_count | summary | production | director | writer_1 | writer_2
#   - genre_1 | genre_2 | genre_3 | genre_4 | release date | censor_rating | movie_length | country | language
#   - budget | gross_worldwide | gross_usa | opening_week_usa

for i in tqdm(range(0, len(title_links)), desc="Movies processed", ncols=100):
    page_url = title_links[i]
    page_text = requests.get(page_url).text
    print(page_text)
    page_soup = BeautifulSoup(page_text, 'html.parser')

    # ------------------------------------------------------------------------------------------
    # Getting movie name, year, rating and number of votes
    movie_name = (page_soup.find("div",{"class":"title_wrapper"}).get_text(strip=True).split('|')[0]).split('(')[0]
    year = ((page_soup.find("div",{"class":"title_wrapper"}).get_text(strip=True).split('|')[0]).split('(')[1]).split(')')[0]
    rating = page_soup.find("span",{"itemprop":"ratingValue"}).text
    vote_count = page_soup.find("span",{"itemprop":"ratingCount"}).text

    # ------------------------------------------------------------------------------------------
    # Getting censor rating, movie length, genre list, rlease date and 
    # country from the subtext
    subtext= page_soup.find("div",{"class":"subtext"}).get_text(strip=True).split('|')
    
    if len(subtext) < 4:
        # Setting values when the movie is unrated
        censor_rating = "No rating"
        movie_length = subtext[0]
        genre_list = subtext[1].split(',')

        while len(genre_list) < 4: genre_list.append(' ')
        genre_1, genre_2, genre_3, genre_4 = genre_list
        
        release_date_and_country = subtext[2].split('(')
        release_date = movie_length_and_country[0]
    else: 
        censor_rating = subtext[0]
        movie_length = subtext[1]
        genre_list = subtext[2].split(',')

        while len(genre_list) < 4: genre_list.append(' ')

        movie_length_and_country = subtext[3].split('(')
        release_date = movie_length_and_country[0]

    # ------------------------------------------------------------------------------------------
    # Getting the movie summary
    summary = page_soup.find("div",{"class":"summary_text"}).get_text(strip=True).strip()
    
    # ------------------------------------------------------------------------------------------
    # Getting the credits for the director and writers
    credit_summary = []
    for summary_item in page_soup.find_all("div",{"class":"credit_summary_item"}):
        credit_summary.append(re.split(',|:|\|',summary_item.get_text(strip=True)))
    
    stars = credit_summary.pop()[1:4]
    writers = credit_summary.pop()[1:3]
    director = credit_summary.pop()[1:]
    
    while len(writers) < 2: writers.append(" ")
    writer_1, writer_2 = writers
    writer_1 = writer_1.split('(')[0]
    writer_2 = writer_2.split('(')[0]

    while len(stars) < 3: stars.append(" ")

    # ------------------------------------------------------------------------------------------
    # Getting the box office details for language, budget, Opening Weekend USA, 
    # Gross income worldwide and USA, and production company
    box_office_details = []
    box_office_dictionary = {'Country':'','Language':'','Budget':'', 'Opening Weekend USA':'','Gross USA':'','Cumulative Worldwide Gross':'','Production Co':''}
    for details in page_soup.find_all("div",{"class":"txt-block"}):
        detail = details.get_text(strip=True).split(':')
        if detail[0] in box_office_dictionary:
            box_office_details.append(detail)
    
    for detail in box_office_details: 
        if detail[0] in box_office_dictionary: 
            box_office_dictionary.update({detail[0] : detail[1]}) 

    country = box_office_dictionary['Country'].split("|")
    while len(country) < 4: country.append(' ')

    language = box_office_dictionary['Language'].split("|")
    while len(language) < 5: language.append(' ')

    budget = box_office_dictionary['Budget'].split('(')[0]

    opening_week_usa = ','.join((box_office_dictionary['Opening Weekend USA'].split(' ')[0]).split(',')[:-1])

    gross_usa = box_office_dictionary['Gross USA']
    gross_worldwide = box_office_dictionary['Cumulative Worldwide Gross'].split(' ')[0]
    
    production_list = box_office_dictionary['Production Co'].split('See more')[0]
    production = production_list.split(',')
    while len(production) < 4: production.append(" ")

    # ------------------------------------------------------------------------------------------
    # Getting the poster link
    poster_div = page_soup.find("div", {"class": "poster"})
    poster_image = poster_div.find("img")['src']

    movie_dict = { 'ranking': i+1, 'movie_name': movie_name, 'url': page_url, 'year': year,
        'rating': rating, 'vote_count': vote_count, 'summary': summary, 'production': production,
        'director': director, 'writers': [writer_1, writer_2], 'stars':stars, 'genres': genre_list, 'release_date': release_date,
        'censor_rating': censor_rating, 'movie_length': movie_length, 'country': country,
        'language': language, 'budget': budget, 'gross_worldwide': gross_worldwide,
        'gross_usa': gross_usa,'opening_week_usa': opening_week_usa, "poster_image": poster_image }

    imdb_movie_list.append(movie_dict)

timestamp =  datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
imdb_list = {
    "timestamp" : timestamp,
    "imdb_movies" : imdb_movie_list
}
print(len(imdb_movie_list))
