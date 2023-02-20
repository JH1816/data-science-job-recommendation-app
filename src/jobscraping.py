from bs4 import BeautifulSoup
import json
import pandas as pd
import urllib.parse
import urllib.request
import re
from datetime import datetime, timedelta


def get_html(url=None,page=None):
    if url==None:
        url = "https://sg.jobsdb.com/j?sp=homepage&q=business+analytics&l="
        # change according to job title you want to scrape for
        if page!=0:
            url+="&p={}".format(page+1)

    # get page
    req = urllib.request.Request(url)
    # req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')
    req.add_header('User-Agent', "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36")

    # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)
    # Chrome/105.0.0.0 Safari/537.36"
    response = urllib.request.urlopen(req)
    html = response.read()
    return html


def change_date(df):

    if df[3] is None:
        d = None
    elif "hours" in df[3]:
        days_to_substract = 0
        d = datetime.today() - timedelta(days=days_to_substract)
        d = d.strftime("%d/%m/%Y")
    else:
        days_to_substract = int(re.findall(r'\d+', df[3])[0])
        d = datetime.today() - timedelta(days=days_to_substract)
        d = d.strftime("%d/%m/%Y")
    return d


def get_details(columns,urls):
    output = []
    for i,url in enumerate(urls):
        print("processing {} url".format(i))
        html = get_html(url)
        soup = BeautifulSoup(html, "html.parser")
        # if i==2:
        #     print(soup)
        # if i==0:
        #     print(soup)
        every_output = []
        for key, value in columns.items():
            if key=="url":
                every_output += [url]
            else:
                JD = soup.find_all(value[0], {"class": value[1]})
                if len(JD)==0:
                    break

                if key=="Job description":
                    elem = JD[-1].text.strip()
                    # print("-------------")
                    # print(JD[0])
                    # print("")
                    # print(JD[1])
                    # print(len(JD))
                else:
                    elem = JD[0].text.strip()

                every_output += [elem]
        every_output += [i+1]
        output.append( every_output )
    # print(output)
    df_output_frame = pd.DataFrame(
        output,
        columns = list(columns.keys())+["index"]
    )
    df_output_frame = df_output_frame.drop_duplicates(subset="url")

    df_output_frame['date'] = df_output_frame.apply(lambda x: change_date(x), axis=1)
    df_output_frame.drop(columns = ['datelisted','index'], inplace=True)
    print(df_output_frame)
    print(len(df_output_frame.index))
    return df_output_frame


if __name__ == '__main__':
    columns = {"job-title": ["h3", "job-title heading-xxlarge"],
               "company": ["span", "company"],
               "location": ["span", "location"],
               "datelisted": ["span", "listed-date"],
               "Job description": ["div", "-desktop-no-padding-top"],
               "url": None}
    page_number = 25  # specify number of pages you want to get
    urls = []
    for i in range(page_number):
        print("page {}".format(i))
        soup = BeautifulSoup(get_html(page=i), "html.parser")
        JD = soup.find_all("a", {"class": "job-link"})
        for every_info in JD:
            elem = every_info["href"]
            if elem.startswith("/job/rd/"):
                continue
            urls.append("https://sg.jobsdb.com"+elem)



    print(urls)
    print("urls number:", len(urls))
    data = get_details(columns,urls)

    with pd.ExcelWriter('BA_25.xlsx') as writer: # specify output file name
        data.to_excel(writer, index=False)








