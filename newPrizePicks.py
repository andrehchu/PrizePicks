from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import argparse 
import pandas as pd
import requests
from bs4 import BeautifulSoup

def wait_for_clickable(driver, delay, selector, selector_type=By.CLASS_NAME):
    element = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((selector_type, selector)))
    element.click()
    time.sleep(2)  

def wait_for_visibility(driver, delay, selector, selector_type=By.CLASS_NAME):
    return WebDriverWait(driver, delay).until(EC.visibility_of_element_located((selector_type, selector)))

def find_and_click(driver, text):
    driver.find_element(By.XPATH, f"//div[text()='{text}']").click()

def get_projections(driver):
    return WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".projection")))

def get_player_data(projection):
    names = projection.find_element(By.XPATH, './/div[@class="name"]').text
    points = projection.find_element(By.XPATH, './/div[@class="presale-score"]').get_attribute('innerHTML')
    text = projection.find_element(By.XPATH, './/div[@class="text"]').text.replace('\n', '')

    return {'Name': names, 'Line': points, 'Prop': text}

def scrape_prizepicks_data(driver):
    wait_for_clickable(driver, 30, "close")

    wait_for_clickable(driver, 10, "//div[@class='name'][normalize-space()='NBA']", By.XPATH)

    stat_container = wait_for_visibility(driver, 10, "stat-container")

    categories = driver.find_element(By.CSS_SELECTOR, ".stat-container").text.split('\n')

    nbaPlayers = []

    for stat in categories:
        find_and_click(driver, stat)

        projections = get_projections(driver)

        for projection in projections:
            player = get_player_data(projection)
            nbaPlayers.append(player)

    driver.quit()

    return pd.DataFrame(nbaPlayers)

def get_player_id(player_name):
    search_url = 'https://www.basketball-reference.com/search/search.fcgi'
    params = {
        'search': player_name,
        'search_type': 'players'
    }

    response = requests.get(search_url, params=params)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the first search result
    search_results = soup.find('div', class_='search-item-name')
    if search_results:
        player_id = search_results.find('a')['href'].split('/')[-1].split('.')[0]
        return player_id

    return None

def lastFive(player_name, stat):
    player_id = get_player_id(player_name)

    if player_id:
        player_url = f'https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html'
        player_response = requests.get(player_url)
        page = player_response.text

        soup = BeautifulSoup(page, features="lxml")  # Specify the HTML parser explicitly

        last5_table = soup.find('table', id='last5')

        df = pd.read_html(str(last5_table))[0]
        selected_columns = ['FG', 'FGA', '3P', '3PA', 'TRB', 'AST', 'STL', 'TOV', 'PF', 'PTS']

        if stat == 'ALL':
            # Print all valid stats in the last 5 games with their values
            valid_stats = [col for col in selected_columns if col in df.columns]
            print('\n')
            print(f"Last 5 Games for {player_name} - All Stats:")
            for valid_stat in valid_stats:
                values = df[valid_stat].tolist()
                print(f"{valid_stat}: {values}")

            # Additional statistics calculations
            print("Additional Statistics:")
            if 'PTS' in valid_stats and 'TRB' in valid_stats:
                pts_trb = df['PTS'] + df['TRB']
                print(f"PTS + TRB: {pts_trb.tolist()}")
            if 'PTS' in valid_stats and 'AST' in valid_stats:
                pts_ast = df['PTS'] + df['AST']
                print(f"PTS + AST: {pts_ast.tolist()}")
            if 'TRB' in valid_stats and 'AST' in valid_stats:
                trb_ast = df['TRB'] + df['AST']
                print(f"TRB + AST: {trb_ast.tolist()}")
            if 'PTS' in valid_stats and 'TRB' in valid_stats and 'AST' in valid_stats:
                pts_trb_ast = df['PTS'] + df['TRB'] + df['AST']
                print(f"PTS + TRB + AST: {pts_trb_ast.tolist()}")

        elif stat in selected_columns:
            df = df[[stat]]
            print('\n')
            print(f"Last 5 Games for {player_name} - {stat}")
            print(df)
        else:
            print(f"Invalid stat: {stat}")
    else:
        print(f"Player '{player_name}' not found.")

def main():
    myParser = argparse.ArgumentParser(description='PrizePicks Program')
    myParser.add_argument('-n', '--name', type=str)
    myParser.add_argument('-s', '--stat', type=str)
    inputArgs = myParser.parse_args()

    driver = webdriver.Chrome()
    driver.get("https://app.prizepicks.com/")

    # Call the function and store the scraped data in a variable
    scraped_data = scrape_prizepicks_data(driver)

    filtered_data = scraped_data[scraped_data['Name'].str.contains(inputArgs.name)]

    # Print the filtered data
    print(filtered_data)

    driver.quit()

    lastFive(inputArgs.name, inputArgs.stat)

if __name__ == "__main__":
    main()
