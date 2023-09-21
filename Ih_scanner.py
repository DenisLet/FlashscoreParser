import asyncio
import requests
import re
import os
import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from notifiers import get_notifier
from nice_all import  get_status
from IH_cases import check_scores_and_odds

token = "xxx"
id = "xxx"


def bet_siska(data):
    telegram = get_notifier('telegram')
    info = "\n".join([i for i in data])
    telegram.notify(token=token,chat_id = id,message = info)
    print("MSG HAS BEEN SENT")


sport_url_soc = 'https://www.soccer24.com/'
sport_url_bb = 'https://www.basketball24.com/'
sport_url_ih = 'https://www.icehockey24.com/'   # ih = ice hockey

async def get_current_matches(page):
    await page.goto(sport_url)
    await page.locator('.filters__text--short').get_by_text('LIVE').click()
    current_matches = await page.locator("[id^='g_4']").element_handles()
    return current_matches


def get_champ(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        heading = soup.find('meta', attrs={'name': 'og:description'})
        text_value = heading['content']
        return text_value

    return None


async def extract_match_data(match_handle):
    id = await match_handle.get_attribute('id')
    current_link = f"{sport_url_ih}match/{id[4:]}"
    champ = 'Unknown (no condition)'


    match_time = await (await match_handle.query_selector('.event__stage--block')).inner_text()
    try:
        t1p1 = await (
                await match_handle.query_selector('.event__part.event__part--home.event__part--1')).inner_text()
        t2p1 = await (
                await match_handle.query_selector('.event__part.event__part--away.event__part--1')).inner_text()
    except AttributeError:
        t1p1 = t2p1 = 0

    try:
        t1p2 = await (
                await match_handle.query_selector('.event__part.event__part--home.event__part--2')).inner_text()
        t2p2 = await (
                await match_handle.query_selector('.event__part.event__part--away.event__part--2')).inner_text()
    except AttributeError:
        t1p2 = t2p2 = 0

    try:
        t1p3 = await (
                await match_handle.query_selector('.event__part.event__part--home.event__part--3')).inner_text()
        t2p3 = await (
                await match_handle.query_selector('.event__part.event__part--away.event__part--3')).inner_text()
    except AttributeError:
        t1p3= t2p3 = 0

    team1_coef = await (await match_handle.query_selector('.odds__odd.event__odd--odd1')).inner_text()
    team2_coef = await (await match_handle.query_selector('.odds__odd.event__odd--odd2')).inner_text()
    real_coef1 = float(team1_coef) if bool(re.match(r'\d+(?:\.\d+)?$', team1_coef)) else 0
    real_coef2 = float(team2_coef) if bool(re.match(r'\d+(?:\.\d+)?$', team2_coef)) else 0
    time_line = match_time.split()
    print(time_line)
    if time_line[0] in ['Finished', 'Overtime', 'Penalties', 'After', 'Awaiting']:
        period = 0
        minute = 0
    else:
        try:

            if 'Break' in time_line:
                period = 0.5    # if any brak time then period = 0.5
                minute = 0
            else:
                period = int(time_line[0][0])
                minute = int(time_line[-1])
        except:
            raise 'Any bullshit in parsing current period and minute'
            period = minute = 0
    if period not in [1, 0.5] and minute > 5:
        champ = get_champ(current_link)
    champ = get_champ(current_link)

    return {
        'champ': champ,
        'link': current_link,
        't1_p1': int(t1p1),
        't2_p1': int(t2p1),
        't1_p2': int(t1p2),
        't2_p2': int(t2p2),
        't1_p3': int(t1p3),
        't2_p3': int(t2p3),
        'coef1': real_coef1,
        'coef2': real_coef2,
        'period': period,
        'minute': minute
    }

period1 = set()
period1_start = set()
period1_more = set()
period2 = set()
period2_start = set()
period2_more = set()
period3 = set()
period3_start = set()
period3_more = set()
ind1_after1 = set()
ind1_after2 = set()
ind2_after1 = set()
ind2_after2 = set()

reloader = 0
async def main():
    while True:
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=False, args=["--mute-audio"])
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto(sport_url_ih)
                await page.locator('.filters__text--short').get_by_text('LIVE').click()

                while True:
                    try:
                        current_matches = await page.locator("[id^='g_4']").element_handles()
                        for num, match_handle in enumerate(current_matches):
                            match_data = await extract_match_data(match_handle)
                            print(match_data)
                            where, status = get_status(match_data['coef1'], match_data['coef2'])
                            quarter = match_data['period']
                            minute = match_data['minute']
                            score = f"{match_data['t1_p1'] + match_data['t1_p2'] + match_data['t1_p3']}:{match_data['t2_p1'] + match_data['t2_p2'] + match_data['t2_p3']}"
                            file = f"{match_data['champ'].split('-')[0].strip()}.txt"
                            if match_data['period'] == 0:
                                continue



                            if os.path.isfile(os.path.join('leaguesIH', file)) == False:
                                continue
                            else:
                                print('Our client')



                            '''   period 1 '''

                            if match_data['period'] == 1 and match_data['minute'] >= 10\
                                    and match_data['t1_p1'] == 0 and match_data['t2_p1'] == 0:
                                if match_data['link'] in period1:
                                    continue
                                print('OP')
                                print(f"leaguesIH/{match_data['champ']}.txt")
                                period1.add(match_data['link'])
                                bet_period1 = check_scores_and_odds(
                                    f"leaguesIH/{file}",
                                    match_data['period'],
                                    match_data['minute'],
                                    match_data['t1_p1'],
                                    match_data['t2_p1'],
                                    match_data['t1_p2'],
                                    match_data['t2_p2'],
                                    match_data['t1_p3'],
                                    match_data['t2_p3'],
                                    match_data['coef1'],
                                    match_data['coef2']
                                )
                                print('PERIOD1 :', bet_period1)
                                if bet_period1 is not None:
                                    bet1 = bet_period1 + (f"minute: {match_data['minute']}", score, match_data['link'],)
                                    print(bet1)
                                    bet_siska(bet1)


                            # if match_data['period'] == 1 and match_data['t1_p1'] == 0 and match_data['t2_p1'] == 0 and minute < 11:
                            #     if match_data['link'] in period1_start:
                            #         continue
                            #     print('OP')
                            #     print(f"leaguesIH/{match_data['champ']}.txt")
                            #     period1_start.add(match_data['link'])
                            #     bet_period1_start = check_scores_and_odds(
                            #         f"leaguesIH/{file}",
                            #         match_data['period'],
                            #         match_data['minute'],
                            #         match_data['t1_p1'],
                            #         match_data['t2_p1'],
                            #         match_data['t1_p2'],
                            #         match_data['t2_p2'],
                            #         match_data['t1_p3'],
                            #         match_data['t2_p3'],
                            #         match_data['coef1'],
                            #         match_data['coef2']
                            #     )
                            #     print('PERIOD1 :', bet_period1_start)
                            #     if bet_period1_start is not None:
                            #         bet1_start = bet_period1_start + (f"minute: {match_data['minute']}", score, match_data['link'],)
                            #         print(bet1_start)
                            #         bet_siska(bet1_start)




                            # if match_data['period'] == 1 and (match_data['t1_p1'] != 0 or match_data['t2_p1'] != 0) and 6<match_data['minute']<14:
                            #     if match_data['link'] in period1_more:
                            #         continue
                            #     print('OP')
                            #     print(f"leaguesIH/{match_data['champ']}.txt")
                            #     period1_more.add(match_data['link'])
                            #     bet_period1_more = check_scores_and_odds(
                            #         f"leaguesIH/{match_data['champ']}.txt",
                            #         match_data['period'],
                            #         match_data['minute'],
                            #         match_data['t1_p1'],
                            #         match_data['t2_p1'],
                            #         match_data['t1_p2'],
                            #         match_data['t2_p2'],
                            #         match_data['t1_p3'],
                            #         match_data['t2_p3'],
                            #         match_data['coef1'],
                            #         match_data['coef2']
                            #     )
                            #     print('PERIOD1 :', bet_period1_more)
                            #     if bet_period1_more is not None:
                            #         bet1_start = bet_period1_more + (f"minute: {match_data['minute']}",match_data['link'],)
                            #         print(bet1_more)
                            #         bet_siska(bet1_more)



                            ''' period 2  '''

                            if match_data['period'] == 2 and match_data['minute'] >= 15\
                                    and match_data['t1_p2'] == 0 and match_data['t2_p2'] == 0:
                                if match_data['link'] in period2:
                                    continue
                                print('OP')
                                print(f"leaguesIH/{match_data['champ']}.txt")
                                period2.add(match_data['link'])
                                bet_period2 = check_scores_and_odds(
                                    f"leaguesIH/{file}",
                                    match_data['period'],
                                    match_data['minute'],
                                    match_data['t1_p1'],
                                    match_data['t2_p1'],
                                    match_data['t1_p2'],
                                    match_data['t2_p2'],
                                    match_data['t1_p3'],
                                    match_data['t2_p3'],
                                    match_data['coef1'],
                                    match_data['coef2']
                                )
                                print('PERIOD2 :', bet_period2)
                                if bet_period2 is not None:
                                    bet2 = bet_period2 + (f"minute: {match_data['minute']}",score, match_data['link'],)
                                    print(bet2)
                                    bet_siska(bet2)

                            # if match_data['period'] == 2 and match_data['t1_p2'] == 0 and match_data['t2_p2'] == 0 and minute < 11:
                            #     if match_data['link'] in period2_start:
                            #         continue
                            #     print('OP')
                            #     print(f"leaguesIH/{match_data['champ']}.txt")
                            #     period2_start.add(match_data['link'])
                            #     bet_period2_start = check_scores_and_odds(
                            #         f"leaguesIH/{file}",
                            #         match_data['period'],
                            #         match_data['minute'],
                            #         match_data['t1_p1'],
                            #         match_data['t2_p1'],
                            #         match_data['t1_p2'],
                            #         match_data['t2_p2'],
                            #         match_data['t1_p3'],
                            #         match_data['t2_p3'],
                            #         match_data['coef1'],
                            #         match_data['coef2']
                            #     )
                            #     print('PERIOD2 :', bet_period2_start)
                            #     if bet_period2_start is not None:
                            #         bet2_start = bet_period2_start + (
                            #         f"minute: {match_data['minute']}",score, match_data['link'],)
                            #         print(bet2_start)
                            #         bet_siska(bet2_start)

                            # if match_data['period'] == 2 and (
                            #         match_data['t1_p2'] != 0 or match_data['t2_p2'] != 0) and 6 < match_data[
                            #     'minute'] < 14:
                            #     if match_data['link'] in period2_more:
                            #         continue
                            #     print('OP')
                            #     print(f"leaguesIH/{match_data['champ']}.txt")
                            #     period1_more.add(match_data['link'])
                            #     bet_period2_more = check_scores_and_odds(
                            #         f"leaguesIH/{match_data['champ']}.txt",
                            #         match_data['period'],
                            #         match_data['minute'],
                            #         match_data['t1_p1'],
                            #         match_data['t2_p1'],
                            #         match_data['t1_p2'],
                            #         match_data['t2_p2'],
                            #         match_data['t1_p3'],
                            #         match_data['t2_p3'],
                            #         match_data['coef1'],
                            #         match_data['coef2']
                            #     )
                            #     print('PERIOD2 :', bet_period2_more)
                            #     if bet_period2_more is not None:
                            #         bet2_more = bet_period2_more + (
                            #         f"minute: {match_data['minute']}", match_data['link'],)
                            #         print(bet2_more)
                            #         bet_siska(bet2_more)


                            """  period 3  """

                            if match_data['period'] == 3 and match_data['minute'] >= 15\
                                    and match_data['t1_p3'] == 0 and match_data['t2_p3'] == 0:
                                if match_data['link'] in period3:
                                    continue
                                print('OP')
                                print(f"leaguesIH/{match_data['champ']}.txt")
                                period3.add(match_data['link'])
                                bet_period3 = check_scores_and_odds(
                                    f"leaguesIH/{file}",
                                    match_data['period'],
                                    match_data['minute'],
                                    match_data['t1_p1'],
                                    match_data['t2_p1'],
                                    match_data['t1_p2'],
                                    match_data['t2_p2'],
                                    match_data['t1_p3'],
                                    match_data['t2_p3'],
                                    match_data['coef1'],
                                    match_data['coef2']
                                )
                                print('PERIOD3 :', bet_period3)
                                if bet_period3 is not None:
                                    bet3 = bet_period3 + (f"minute: {match_data['minute']}",score, match_data['link'],)
                                    print(bet3)
                                    bet_siska(bet3)


                            # if match_data['period'] == 3 and match_data['t1_p3'] == 0 and match_data['t2_p3'] == 0 and match_data['minute'] <11:
                            #     if match_data['link'] in period3_start:
                            #         continue
                            #     print('OP')
                            #     print(f"leaguesIH/{match_data['champ']}.txt")
                            #     period3_start.add(match_data['link'])
                            #     bet_period3_start = check_scores_and_odds(
                            #         f"leaguesIH/{file}",
                            #         match_data['period'],
                            #         match_data['minute'],
                            #         match_data['t1_p1'],
                            #         match_data['t2_p1'],
                            #         match_data['t1_p2'],
                            #         match_data['t2_p2'],
                            #         match_data['t1_p3'],
                            #         match_data['t2_p3'],
                            #         match_data['coef1'],
                            #         match_data['coef2']
                            #     )
                            #     print('PERIOD2 :', bet_period3_start)
                            #     if bet_period3_start is not None:
                            #         bet3_start = bet_period3_start + (
                            #         f"minute: {match_data['minute']}",score, match_data['link'],)
                            #         print(bet3_start)
                            #         bet_siska(bet3_start)


                            ''' individual '''

                            if match_data['period'] == 2 and match_data['t1_p1'] == 0 and match_data['t1_p2'] == 0:
                                if match_data['link'] in ind1_after1:
                                    continue
                                print('OP')
                                print(f"leaguesIH/{match_data['champ']}.txt")
                                ind1_after1.add(match_data['link'])
                                ind1_05 = check_scores_and_odds(
                                    f"leaguesIH/{match_data['champ']}.txt",
                                    match_data['period'],
                                    match_data['minute'],
                                    match_data['t1_p1'],
                                    match_data['t2_p1'],
                                    match_data['t1_p2'],
                                    match_data['t2_p2'],
                                    match_data['t1_p3'],
                                    match_data['t2_p3'],
                                    match_data['coef1'],
                                    match_data['coef2'],
                                    case = 'ind1'
                                )
                                print('IND 1:', ind1_05)
                                if ind1_05 is not None:
                                    ind1 = ind1_05 + (
                                    f"minute: {match_data['minute']}", match_data['link'],)
                                    print(ind1)
                                    bet_siska(ind1)


                            if match_data['period'] == 2 and match_data['t2_p1'] == 0 and match_data['t2_p2'] == 0:
                                if match_data['link'] in ind2_after1:
                                    continue
                                print('OP')
                                print(f"leaguesIH/{match_data['champ']}.txt")
                                ind2_after1.add(match_data['link'])
                                ind2_05 = check_scores_and_odds(
                                    f"leaguesIH/{match_data['champ']}.txt",
                                    match_data['period'],
                                    match_data['minute'],
                                    match_data['t1_p1'],
                                    match_data['t2_p1'],
                                    match_data['t1_p2'],
                                    match_data['t2_p2'],
                                    match_data['t1_p3'],
                                    match_data['t2_p3'],
                                    match_data['coef1'],
                                    match_data['coef2'],
                                    case = 'ind2'
                                )
                                print('IND 2:', ind2_05)
                                if ind2_05 is not None:
                                    ind1 = ind2_05 + (
                                    f"minute: {match_data['minute']}", match_data['link'],)
                                    print(ind2)
                                    bet_siska(ind2)






                    except:
                        True

                    # now = datetime.datetime.now()
                    # if (now.hour == 8 or now.hour == 12) and now.minute == range(2) and now.second in range(8):
                    #     await browser.close()
                    #     break
                    # await asyncio.sleep(20)
                    # continue

        except Exception as e:

            print(f"An error occurred: {e}")

            await asyncio.sleep(1)
            continue


if __name__ == "__main__":
    asyncio.run(main())