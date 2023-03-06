import csv
from decimal import Decimal
import time
import traceback
import sqlite3
from sqlite3 import Error

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

FIELDNAMES = ['school_name', 'country', 'oversea_course',
              'oversea_code', 'ust_course', 'ust_code', 'credit', 'ref']
TERM = "2022-23 Spring"
COUNTRY = "Any"
NAME = "Any"
COURSE_CODE = "COMP"
COURSE = "Any"

FILENAME = f"{TERM}_{COUNTRY}_{COURSE_CODE}"


def get_url(
    n): return f"https://registry.hkust.edu.hk/useful-tools/credit-transfer/database-institution/results-institution?admission_term={'+'.join(TERM.split())}&country_institution={COUNTRY}&institution_name={NAME}&hkust_course_code={COURSE_CODE}&hkust_subject={COURSE}&form_build_id=form-YNkfBITcgeGJuyJbhEkCB2Lf305x-aQPsXw-2PKV9Uw&form_id=institution_results_form&op=Search&page={n}"


def get_page_data(driver, url):
    driver.get(url)

    institution_results = WebDriverWait(driver, 999, poll_frequency=2).until(
        EC.presence_of_element_located((By.ID, "institution-results")))
    results = institution_results.find_elements(
        By.CSS_SELECTOR, ".result-items")
    result_count = institution_results.find_elements(
        By.CSS_SELECTOR, ".result-count-results__num")
    showing = result_count[0].text.strip().split("-")
    total = result_count[1].text.strip()

    return results, (int(showing[0]), int(showing[1]), int(total))


def get_result_obj(result):
    from re import findall
    def get_course_obj(item):
        oversea_course = item.find_element(
            By.CSS_SELECTOR,
            ".tile-transfer__subject").text.strip()
        oversea_code = item.find_element(
            By.CSS_SELECTOR,
            ".tile-transfer__ust-course-code").text.strip()
        ust_course = item.find_element(
            By.CSS_SELECTOR,
            ".tile-transfer__course-title").text.strip()
        ust_code = item.find_element(
            By.CSS_SELECTOR,
            ".tile-transfer__course-code").text.strip()
        credit = item.find_element(
            By.CSS_SELECTOR,
            ".tile-transfer__credit").text.strip()
        ref = item.find_element(
            By.CSS_SELECTOR,
            ".tile__ref__number").text.strip()
        return {"oversea_course": oversea_course, "oversea_code": oversea_code, "ust_course": ust_course, "ust_code": ust_code, "credit": int(findall(r'\d+', credit)[0]), "ref": ref}

    country = result.find_element(
        By.CSS_SELECTOR,
        ".category__text").text.strip()
    school_name = result.find_element(
        By.CSS_SELECTOR,
        "div.result-item__qualification__non-ust").text.strip()
    items = result.find_elements(By.CSS_SELECTOR, ".result-items__item")
    courses = [get_course_obj(item) for item in items]
    return {"school_name": school_name, "country": country, "courses": courses}


def write_csv():
    with open(FILENAME+".csv", 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()


def append_csv(data):
    with open(FILENAME+".csv", 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        name = data["school_name"]
        country = data["country"]
        for course in data["courses"]:
            writer.writerow(
                {"school_name": name, "country": country, **course})

def conn_db(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn
  
def create_table_if_not_exists(conn, tableName):
    try:
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS '{tableName}' ( school_name TEXT, country TEXT, oversea_course TEXT, oversea_code TEXT, ust_course TEXT, ust_code TEXT, credit INTEGER, ref TEXT)")
    except Error as e:
        print(e)

def insert_data(conn, tableName, data):
    try:
        c = conn.cursor()
        
        for course in data["courses"]:
          variable = (data["school_name"], data["country"], course["oversea_course"], course["oversea_code"], course["ust_course"], course["ust_code"], course["credit"], course["ref"])
          c.execute(f"INSERT INTO '{tableName}' VALUES (?,?,?,?,?,?,?,?)", variable)
    except Error as e:
        print(e)

def search(conn, tableName, school_name=None, country=None, oversea_course=None, oversea_code=None, ust_course=None, ust_code=None, credit=None, ref=None):
    try:
        c = conn.cursor()
        query = {
          "school_name": school_name,
          "country": country,
          "oversea_course": oversea_course,
          "oversea_code": oversea_code,
          "ust_course": ust_course,
          "ust_code": ust_code,
          "credit": credit,
          "ref": ref
        }
        def make_query_str(key, value):
          if type(value) == str:
            return f"{key}='{value}'"
          elif type(value) == int:
            return f"{key}={value}"
          else:
            return f"UNIMPLEMENTED TYPE {type(value)}"

        query_str = " AND ".join([make_query_str(key, value) for key, value in query.items() if value is not None])
        
        return c.execute(f"SELECT * FROM '{tableName}'" + (f"WHERE {query_str}" if len(query_str) > 0 else "")).fetchall()
    except Error as e:
        print(e)

def main():
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--start-maximized")
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=options)

    db_conn = conn_db("credit_transfer.db")
    if (db_conn is None):
      print("Error! cannot create the database connection. Skip for now.")
    
    create_table_if_not_exists(db_conn, FILENAME)

    write_csv()
    i = 1
    cumulative_count = 0
    try:
        while True:
            t_start = time.perf_counter()

            results, result_count = get_page_data(driver, get_url(i))
            item_start, item_end, total = result_count
            cumulative_count += item_end-item_start + 1

            for result in results:
                append_csv(get_result_obj(result))
                insert_data(db_conn, FILENAME, get_result_obj(result))
                db_conn.commit()

            t_end = time.perf_counter()

            # print statistics
            print(
                f"Scrapped page {i} ({cumulative_count}/{total} courses recorded). Used {t_end - t_start:0.4f} seconds")
            if (item_end == total):
                break
            i += 1
    except:
        traceback.print_exc()
    finally:
        if db_conn:
            db_conn.close()
        driver.quit()
        print(f"Scrapped {cumulative_count}. Exit now.")


if __name__ == '__main__':
    main()
