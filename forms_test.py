import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

genai.configure(api_key="AIzaSyBgmgGSiz92muo0dQM-h-K9NSCJi-q_tHE")
model = genai.GenerativeModel('gemini-3-flash-preview')

options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

url = "https://docs.google.com/forms/d/e/1FAIpQLSeVg6XrUAEY-2qtQS6jcYGHIAalPohskILb1yxSq1D-qDQtVQ/viewform"
driver.get(url)
time.sleep(3.5)

soup = BeautifulSoup(driver.page_source, 'html.parser')
questions = soup.find_all("div", role="listitem")
d = {}
a = {}

for idx, question in enumerate(questions):
    title = question.find("div", role="heading")
    
    if title:
        question_text = title.get_text(strip=True)
        print("Question:", question_text)

        sp = question.find_all("span", dir="auto")
        l = []

        for s in sp:
            option_text = s.get_text(strip=True)
            if option_text and option_text != question_text and option_text not in l:
                print("Option:", option_text)
                l.append(option_text)

        d[idx] = {
            "question": question_text,
            "options": l
        }

for idx, data in d.items():
    q_text = data["question"]
    options = data["options"]

    prompt = f"Question: {q_text}\nOptions: {', '.join(options)}\n\n"
    prompt += "Identify the correct answer from the options provided. Provide only the text of the correct option."

    response = model.generate_content(prompt)
    response = model.generate_content(prompt)
    answer = response.text.strip()
    print(f"Q: {q_text}")
    print(f"AI Answer: {answer}")
    print("-" * 20)

    a[idx] = answer

question_to_answer = {}
sorted_d_keys = sorted(d.keys())

for consecutive_idx, idx in enumerate(sorted_d_keys):
    correct_answer = None
    if idx in a:
        correct_answer = a[idx]
    elif consecutive_idx in a:
        correct_answer = a[consecutive_idx]
        
    if correct_answer:
        clean_q = d[idx]["question"].replace("*", "").strip().lower()
        question_to_answer[clean_q] = correct_answer

question_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")

for q_element in question_elements:
    headings = q_element.find_elements(By.CSS_SELECTOR, "div[role='heading']")
    if not headings:
        continue
    
    q_text = headings[0].text.replace("*", "").strip().lower()
    if q_text not in question_to_answer:
        continue
        
    correct_answer = question_to_answer[q_text]
    
    options = q_element.find_elements(By.CSS_SELECTOR, "div[role='radio'], div[role='checkbox']")
    clicked = False
    
    for opt in options:
        label = opt.get_attribute("aria-label") or opt.text or ""
        label = label.strip()
        
        if correct_answer.lower() in label.lower() or (correct_answer.lower() == "other:" and "other" in label.lower()):
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", opt)
            time.sleep(0.3)
            try:
                opt.click()
            except Exception:
                driver.execute_script("arguments[0].click();", opt)
            clicked = True
            print(f"Clicked: '{label}' for question: '{headings[0].text.strip()}'")
            break
            
    if not clicked:
        inputs = q_element.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
        for inp in inputs:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inp)
            time.sleep(0.5)
            
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.common.keys import Keys
            
            try:
                driver.execute_script("arguments[0].focus();", inp)
                time.sleep(0.2)
                
                actions = ActionChains(driver)
                actions.move_to_element(inp).click()
                actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE)
                actions.send_keys(correct_answer)
                actions.perform()
                print(f"Filled Text: '{correct_answer}' for question: '{headings[0].text.strip()}'")
            except Exception as e:
                print(f"Fallback direct input for question: '{headings[0].text.strip()}' due to: {e}")
                inp.clear()
                inp.send_keys(correct_answer)
            break

time.sleep(5)