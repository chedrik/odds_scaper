from recordtype import recordtype
from dateutil.parser import parse
import pytz


def generate_url(sport):
    """
    :param sport: string of sport type, supported options MLB, NFL, CFB, NBA, NHL, SCR (soccer)
    :return: url of webpage to scrape, None if unsupported
    """
    url_dict = {
        "MLB": "https://www.bovada.lv/sports/baseball/mlb",
        "NFL": "https://www.bovada.lv/sports/football/nfl",
        "CFB": "https://www.bovada.lv/sports/football/college-football",
        "CBB": "https://www.bovada.lv/sports/basketball/college-basketball",
        "NBA": "https://www.bovada.lv/sports/basketball/nba",
        "NHL": "https://www.bovada.lv/sports/hockey/nhl",
        # "SCR": "https://www.sportsbookreview.com/betting-odds/soccer/"  # TODO: what level of soccer to support
    }
    sport = sport.upper()
    url = url_dict.get(sport, None)

    return url


# TODO: error checking, needed? or reduce current amount
def get_game_datetime(game_tag):
    """
    :param game_tag: game_container from beautiful soup, to be parsed
    :return: datetime object in UTC time
    """
    date_ob = None
    date_tag = game_tag.find('span', class_='period')
    if date_tag:
        date = date_tag.contents[0].strip()
        clock_tag = date_tag.find('time', class_='clock')
        if clock_tag:
            clock_time = clock_tag.string.strip()
            date_ob = parse(date + ' ' + clock_time)
        else:
            date_ob = parse(date)
        date_ob = pytz.timezone('US/Pacific').localize(date_ob).astimezone(pytz.utc)

    return date_ob


def get_team_names(game_tag):
    """
    :param game_tag: game_container from beautiful soup, to be parsed
    :return: full name of away team, full name of home team, ranks of away, home  (empty string if not ranked)
    """
    away_team, home_team, away_rank, home_rank = None, None, None, None
    team_tags = game_tag.find_all('span', class_='name')
    if team_tags and len(team_tags) == 2:
        away_text = team_tags[0].text
        home_text = team_tags[1].text
        if '(' in away_text:
            split = away_text.strip().split(' (#')
            away_team = split[0]
            away_rank = split[:-1]
        else:
            away_team = away_text.strip()
            away_rank = ''

        if '(' in home_text:
            split = home_text.strip().split(' (#')
            home_team = split[0]
            home_rank = split[:-1]
        else:
            home_team = home_text.strip()
            home_rank = ''

    return away_team, home_team, away_rank, home_rank


def get_moneyline(lines):
    """
    :param lines: recordtype with all prices [away_sprd, home_sprd, away_ml, home_ml, over, under] and other line info
    :return: price of away team, price of home team, with even odds converted to + 100.0
    """
    away_price, home_price = None, None
    if lines.has_moneyline:
        away_price_text = lines.prices[2].strip()
        home_price_text = lines.prices[3].strip()
        if away_price_text == 'EVEN':
            away_price = 100.0
        else:
            away_price = float(away_price_text)
        if home_price_text == 'EVEN':
            home_price = 100.0
        else:
            home_price = float(home_price_text)
    return away_price, home_price


def get_game_spread(lines):
    """
    :param lines: recordtype with all prices [away_sprd, home_sprd, away_ml, home_ml, over, under] and other line info
    :return: tuples for away team, home team of form (spread, price) with even converted to 100.0 and pickem -> TBD
    """
    # TODO: Deal with 'pickem'
    away_spread, home_spread, away_price, home_price = None, None, None, None

    if lines.has_spread:
        away_spread = float(lines.spread[0].text)
        away_price_text = lines.prices[0].strip()
        if away_price_text == 'EVEN':
            away_price = 100
        else:
            away_price = float(away_price_text)

        home_spread = float(lines.spread[1].text)
        home_price_text = lines.prices[1].strip()
        if home_price_text == 'EVEN':
            home_price = 100
        else:
            home_price = float(home_price_text)

    away_tuple = (away_spread, away_price)
    home_tuple = (home_spread, home_price)

    return away_tuple, home_tuple


def get_game_total(lines):
    """
    :param lines: recordtype with all prices [away_sprd, home_sprd, away_ml, home_ml, over, under] and other line info
    :return: tuples for over, under of form (spread, price) with even converted to 100.0
    """
    over, under, over_price, under_price = None, None, None, None
    if lines.has_total:
        over = float(lines.total[1].text)
        under = float(lines.total[3].text)
        over_price_text = lines.prices[4].strip()
        under_price_text = lines.prices[5].strip()
        if over_price_text == 'EVEN':
            over_price = 100.0
        else:
            over_price = float(over_price_text)
        if under_price_text == 'EVEN':
            under_price = 100.0
        else:
            under_price = float(under_price_text)

    over_tuple = (over, over_price)
    under_tuple = (under, under_price)

    return over_tuple, under_tuple


def check_has_lines(game_tag):  # TODO: This is ugly.  Come up with better way to handle this?
    """
    :param game_tag: game_container from beautiful soup, to be parsed
    :return: recordtpe containing all parsed line information
    """
    # check whether all lines are there or not and return the found tag if so
    # TODO: move this out of function
    Lines = recordtype('Lines', 'spread moneyline total prices has_spread has_moneyline has_total')
    lines = Lines(spread=None, moneyline=None, total=None, prices=None, has_spread=False, has_moneyline=False,
                  has_total=False)

    lines.spread = game_tag.find_all('span', class_='market-line bet-handicap')
    lines.total = game_tag.find_all('span', class_='market-line bet-handicap both-handicaps')
    lines.prices = game_tag.find_all('span', class_='bet-price')
    # TODO: more elegant solution for this?
    for k in range(len(lines.prices)):
        price = lines.prices[k].text
        if '(' in price:
            for char in ['(', ')']:
                price = price.replace(char, '')
        lines.prices[k] = price

    num_prices = len(lines.prices)
    if num_prices == 6:
        lines.has_spread, lines.has_moneyline, lines.has_total = True, True, True
    elif num_prices == 4:
        if lines.spread:
            lines.has_spread = True
        if lines.total:
            lines.has_total = True
        if not lines.has_total or not lines.has_spread:
            lines.has_moneyline = True
    elif num_prices == 2:
        if lines.spread:
            lines.has_spread = True
        if lines.total:
            lines.has_total = True
        if not lines.has_total and not lines.has_spread:
            lines.has_moneyline = True

    # Pad lines.prices for indexing purposes
    if not lines.has_spread:
        lines.prices.insert(0, '')
        lines.prices.insert(0, '')
    if not lines.has_moneyline:
        lines.prices.insert(2, '')
        lines.prices.insert(2, '')
    return lines


def make_game_object(game_tag):
    """
    :param game_tag: game_container from beautiful soup, to be parsed
    :return: game recordtype containing all information parsed, ready to be added to DB
    """
    # main parser wrapper.... for now
    game_datetime = get_game_datetime(game_tag)
    away_team, home_team, away_rank, home_rank = get_team_names(game_tag)
    game_lines = check_has_lines(game_tag)
    away_spread, home_spread = get_game_spread(game_lines)
    away_ml, home_ml = get_moneyline(game_lines)
    over, under = get_game_total(game_lines)

    game_id = (game_datetime, home_team, away_team)
    # TODO: move this out of function
    Game = recordtype('Game', 'game_id away_spread home_spread away_ml home_ml over under ranks')
    game = Game(game_id=game_id, away_spread=away_spread, home_spread=home_spread,
                away_ml=away_ml, home_ml=home_ml, over=over, under=under, ranks=[home_rank, away_rank])
    return game


def check_game_in_progress(game_tag):
    """
    :param game_tag: game_container from beautiful soup, to be parsed
    :return: Boolean whether game is currently in progress. If it is, it will have live game tag
    """
    if 'live-game' in game_tag.parent.attrs['class'] or get_game_datetime(game_tag) is None:
        return True
    else:
        return False


def make_odds_pretty(odds):
    """
    Convert odds for display by adding +/- and rounding
    :param odds: float of game odds
    :return: odds string of odds for display
    """
    if odds is None:
        return odds
    if (odds / 1.0).is_integer():  # hack to convert int -> float
        odds = int(odds)
    if odds > 0:
        return '+' + str(odds)
    else:
        return str(odds)
