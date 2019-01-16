from odds_scraper import *
from selenium import webdriver
from database import *
import time


def open_web_interface():
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    prefs = {'profile.managed_default_content_settings.images': 2}  # Load without images
    options.add_experimental_option("prefs", prefs)
    web_driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=options)  # TODO Deal with path nastiness
    return web_driver


def extract_game_containers(web_driver, sport='NBA'):
    retry_count = 0
    num_games = 0
    while num_games == 0 and retry_count <= 10:
        url_to_scrape = generate_url(sport)
        web_driver.get(url_to_scrape)
        web_driver.implicitly_wait(5)  # TODO: Trim/Extend this time
        big_soup = BeautifulSoup(web_driver.page_source, 'html.parser')
        game_containers = big_soup.find_all('section',
                                            class_='coupon-content more-info')  # TODO: find out if this deals with live games
        retry_count += 1
        num_games = len(game_containers)
    return game_containers


def cleanup_web_interface(driver):
    driver.quit()


def main_loop(database, sport='NBA'):
    web_driver = open_web_interface()
    game_containers = extract_game_containers(web_driver, sport)
    for k in range(len(game_containers)):
        game = make_game_object(game_containers[k])
        result = add_game_to_database(game, select_collection(database, sport))
        string = 'Added ' + str(game.game_id) + ' at time: ' + str(datetime.datetime.now()) + ' with result: '
        print string
        print result
    print ' '
    cleanup_web_interface(web_driver)


from multiprocessing import Pool
def multi_process_test():
    pool = Pool(2)
    sports = ['NBA', 'NHL']

    test = pool.map(test_extract, sports)
    pool.close()
    pool.join()
    #return test

from multiprocessing.pool import ThreadPool
def thread_test():
    pool = ThreadPool(2)
    sports = ['NBA', 'NHL']

    test = pool.map(test_extract, sports)
    pool.close()
    pool.join()
    #return test

def test_extract(sport):
    client, db = initialize_databases()

    retry_count = 0
    num_games = 0
    url_to_scrape = generate_url(sport)
    game = None
    result = []
    while num_games == 0 and retry_count <= 10:
        web_driver.get(url_to_scrape)
      #  web_driver.implicitly_wait(5)  # TODO: Trim/Extend this time
        big_soup = BeautifulSoup(web_driver.page_source, 'html.parser')
        game_containers = big_soup.find_all('section',
                                            class_='coupon-content more-info')  # TODO: find out if this deals with live games
        retry_count += 1
        num_games = len(game_containers)
    for k in range(len(game_containers)):
        game = make_game_object(game_containers[k])
        result.append(add_game_to_database(game, select_collection(db, sport)))
        # string = 'Added ' + str(game.game_id) + ' at time: ' + str(datetime.datetime.now()) + ' with result: '
        # print string
    return result#game_containers#num_games #big_soup.text


if __name__ == '__main__':
    from multiprocessing import Pool
    # import concurrent.futures
    # import threading

    web_driver = open_web_interface()
    t1 = time.time()
    multi_process_test()
    print time.time() - t1
    print ' '
    print ' '
    #print len(poop[0]), len(poop[1])
    #test_extract('NHL')
    web_driver.quit()

    web_driver = open_web_interface()

    t3 = time.time()
    thread_test()
    print time.time() - t3
    print ' '
    print ' '
    web_driver.quit()



    web_driver = open_web_interface()
    t2 = time.time()
    dumb = test_extract('NBA')
    # for k in range(len(dumb)):
    #     game = make_game_object(dumb[k])
    #     add_game_to_database(game, select_collection(db, 'NBA'))
    #     string = 'Added ' + str(game.game_id) + ' at time: ' + str(datetime.datetime.now()) + ' with result: '
    #     print string
    dumb2 = test_extract('NHL')
    # for k in range(len(dumb)):
    #     game = make_game_object(dumb[k])
    #    # add_game_to_database(game, select_collection(db, 'NHL'))
    #   #  string = 'Added ' + str(game.game_id) + ' at time: ' + str(datetime.datetime.now()) + ' with result: '
    #     print string
    print time.time() - t2
    web_driver.quit()



    # while True:
    #     client, db = initialize_databases()
    #     main_loop(db)
    #     time.sleep(300)
