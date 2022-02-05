import csv
import time
import traceback
import sys
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.utils import ChromeType

FIELDNAMES = ['school_name', 'country', 'oversea_course',
              'oversea_code', 'ust_course', 'ust_code', 'credit', 'ref']
COUNTRY = "Any"
NAME = "Any"
COURSE_CODE = "COMP"
COURSE = "Any"


def get_url(
    n): return f"https://registry.hkust.edu.hk/useful-tools/credit-transfer/database-institution/results-institution?admission_term=2022-23+Spring&country_institution={COUNTRY}&institution_name={NAME}&hkust_course_code={COURSE_CODE}&hkust_subject={COURSE}&form_build_id=form-YNkfBITcgeGJuyJbhEkCB2Lf305x-aQPsXw-2PKV9Uw&form_id=institution_results_form&op=Search&page={n}"


def get_page_data(driver, url):
    driver.get(url)

    institution_results = WebDriverWait(driver, 999, poll_frequency=2).until(
        EC.presence_of_element_located((By.ID, "institution-results")))
    results = institution_results.find_elements(
        By.CSS_SELECTOR, ".result-items")
    result_count = institution_results.find_elements(
        By.CSS_SELECTOR, ".result-count-results__num")
    current = result_count[0].text.strip().split("-")[1]
    end = result_count[1].text.strip()
    isEnd = current == end
    try:
        pageNext = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "li.pager__item.pager__item--next > a"))).get_attribute("data-page")
    except TimeoutException:
        print("end")
        raise TimeoutException

    return results, isEnd


def get_result_obj(result):

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
        return {"oversea_course": oversea_course, "oversea_code": oversea_code, "ust_course": ust_course, "ust_code": ust_code, "credit": credit, "ref": ref}

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
    with open('courses.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()


def append_csv(data):
    with open('courses.csv', 'a') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        name = data["school_name"]
        country = data["country"]
        for course in data["courses"]:
            writer.writerow(
                {"school_name": name, "country": country, **course})


def main():
    options = webdriver.ChromeOptions()
    #options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.headless = True
    # driver = webdriver.Chrome(service=Service(
     #   ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
    write_csv()
    i = 1
    try:
        while True:
            start = time.perf_counter()
            results, end = get_page_data(driver, get_url(i))
            for result in results:
                append_csv(get_result_obj(result))
            end = time.perf_counter()
            print(
                f"Scrapped page {i} for {len(results)} institutions. Used {end - start:0.4f} seconds")
            if end:
                break
            i += 1
    except:
        traceback.print_exc()
    finally:
        print("finally")
        driver.quit()


if __name__ == '__main__':
    main()
