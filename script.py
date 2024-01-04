import pandas as pd
import requests
import bs4
import time
from pathlib import Path

class NBAScraper:
    def __init__(self):
        pass

    @staticmethod
    def allowed_by_robots_txt(url):
        """
        Returns a boolean value representing if a url is allowed 
        to be scraped, according to the site's robots.txt
        ---
        url: string representing url to scrape
        """
        # Get robots.txt
        url_split = url.split("/")
        robots_txt_url = url_split[0] + '//' + url_split[2] + '/robots.txt'

        response = requests.get(robots_txt_url)
        response.raise_for_status()

        lines = response.text.split('\n')

        user_agent_reached = False

        for line in lines:
            if line.strip() == 'User-agent: *':
                user_agent_reached = True
                
            if line.lower().startswith('disallow') and user_agent_reached:
                # Check if the URL is disallowed
                disallowed_path = line.split(':', 1)[1].strip()
                if disallowed_path == '/':
                    break
                if disallowed_path in url:
                    return False

        # If no specific rule is found, the URL is allowed
        return True

    @staticmethod
    def get_data(url):
        """
        Creates DataFrame containing a month's amount of data from url.
        ---
        url: string representing url to scrape
        """
        # Make request to site
        response = requests.get(url)
        
        # Check to see if response was successful
        if response.status_code == 200:
            html_content = response.text
        else:
            raise Exception(f"Error: Unable to fetch content. Status code: {response.status_code}.")
            
        # create soup object and get only 'tr' tags
        soup = bs4.BeautifulSoup(html_content, features='lxml')
        soup = (soup
                .find('body', class_='bbr')
                .find('div', {'id':'wrap'})
                .find('div', {'id':'content'})
                .find('div', {'id':'all_schedule'})
                .find('div', {'id':'div_schedule'})
                .find('tbody')
                .find_all('tr'))

        # collect data
        date, start, visitor, visitor_pts, home, home_pts, box_score, ot, attend, arena, notes = [], [], [], [], [], [], [], [], [], [], []
        for game in soup:
            date.append(game.find_all('th')[0].text)
            start.append(game.find_all('td')[0].text)
            visitor.append(game.find_all('td')[1].text)
            visitor_pts.append(game.find_all('td')[2].text)
            home.append(game.find_all('td')[3].text)
            home_pts.append(game.find_all('td')[4].text)
            box_score.append('https://www.basketball-reference.com/' + game.find_all('td')[5].find('a').get('href'))
            ot.append(game.find_all('td')[6].text)
            attend.append(game.find_all('td')[7].text)
            arena.append(game.find_all('td')[8].text)
            notes.append(game.find_all('td')[9].text)
        
        # create DataFrame
        data = {'Date': date, 
                'Start Time (ET)': start,
                'Visitor': visitor, 
                'Visitor Points': visitor_pts, 
                'Home': home, 
                'Home Points': home_pts, 
                'Box Score': box_score, 
                'Overtime': ot, 
                'Attendance': attend, 
                'Arena': arena, 
                'Notes': notes}
        return pd.DataFrame(data)

    def nba_season(self, year):
        """
        Creates DataFrame for a specific year.
        ---
        year: number representing what year to scrape
        """
        df = pd.DataFrame()
        months = ['october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']
        for month in months:
            url = f'https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html'
            try: 
                df = pd.concat([df, self.get_data(url)], ignore_index=True)
            except:
                pass
        return df

    def data_years(self, beginning=2013, end=2024):
        """
        Creates DataFrame that contains data from a specific range of years. Default
        values includes only the modern years of the NBA.
        ---
        beginning: first year to include (inclusive)
        end: last year to not include
        """
        df = pd.DataFrame()
        for i in range(beginning, end):
            temp_df = self.nba_season(i)
            df = pd.concat([df, temp_df], ignore_index=True)
            # sleep to comply with crawler traffic. https://www.sports-reference.com/bot-traffic.html
            time.sleep(35)
        return df
    
    def main():
        # Create an instance of NBAScraper
        nba_scraper = NBAScraper()

        # Call the method to fetch and concatenate data for a range of years
        nba_data = nba_scraper.data_years()

        # Save the DataFrame to a CSV file
        output_path = Path('data') / 'nba_data.csv'
        nba_data.to_csv(output_path, index=False)
        print(f"Data saved to: {output_path}")

    if __name__ == "__main__":
        main()