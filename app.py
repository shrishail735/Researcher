import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import *
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from firebase_admin import credentials, firestore, initialize_app, auth
import os
from apscheduler.schedulers.background import BackgroundScheduler
# from pyrebase import pyrebase
# from Crypto.Cipher import AES
# firestore settings
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()
interests_db = db.collection('interests')
users = db.collection("users")

sender_email = 'vaisht1411@gmail.com'
sender_password = 'gynxewqukdrsvlpc'
# Function to send an email

scheduler = BackgroundScheduler()


def send_email(sender_email, sender_password, receiver_email, subject, message):
    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Create an SMTP session
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

# Function to fetch research papers based on user's interests


# schedule.every(10).seconds.do(job)  # Everyday at 10: 30
# schedule.every(5)
#   .seconds.do(job) # # # Every 5 seconds
# #schedule.every()
#   .sunday.at("10:30")
#   .do(job) # # # Every Sunday at 10: 30


def fetch_research_papers(interests):
    papers = []

    # Loop through the websites and search for papers based on interests
    for website in ['https://www.sciencedirect.com']:
        # Perform a search query on the website using the interests
        search_url = f"{website}/search?qs={'+'.join(interests)}"
        # print(search_url)
        driver = webdriver.Chrome()
        driver.get(search_url)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.CLASS_NAME, 'result-item-content')))
        except TimeoutException:
            print('Page timed out after 10 secs.')
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        # response = requests.get(search_url)
        # soup = BeautifulSoup(response.text, 'html.parser')
        # print(search_url)
        # Extract the paper details from the search results
        results = soup.find_all('div', class_="result-item-content")
        # print(results)

        for result in results:
            title = result.find('h2').text.strip()
            authors = result.find('ol', class_='Authors').text.strip()
            abstract = result.find('a', class_='download-link')
            if(abstract):
                abstract = website+abstract['href']
            paper = {
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'website': website
            }
            papers.append(paper)

    return papers


app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route('/')
def man():
    return render_template('./test.html', error='')


@app.route('/interests')
def interest():
    if 'email' in session:
        email = session['email']
        user_data = interests_db.document(email).get().to_dict()

        interests = user_data['interests']
        return render_template('./interest.html', interestsD=interests)
    else:
        return redirect('/')


@app.route('/interests', methods=['POST'])
def inter():
    interests = request.json['data']
    send = request.json['send']
    print(send)
    email = session['email']
    data = {
        "interests": interests,
        "email": email
    }
    interests_db.document(email).set(data, merge=True)
    user_data = interests_db.document(email).get().to_dict()

    interests = user_data['interests']
    return render_template('./interest.html', interestsD=interests)


@app.route('/sendpapers', methods=['POST'])
def paper():
    interests = request.json['data']
    email = session['email']
    receiver_email = email
    subject = 'Recommended Research Papers'
    # interests = ['machinelearning', 'datascience']

    # Fetch research papers based on user's interests
    papers = fetch_research_papers(interests)

    # Prepare the email message
    if len(papers) > 0:
        message = f"Dear User,\n\nHere are some recommended research papers based on your interests:\n\n"
        for paper in papers:
            message += f"Title: {paper['title']}\n"
            message += f"Authors: {paper['authors']}\n"
            message += f"PDF Link: {paper['abstract']}\n"
            message += f"Website: {paper['website']}\n\n"

        # Send the email
        send_email(sender_email, sender_password,
                   receiver_email, subject, message)
        return "Mail sent !!"
    else:
        return "Some error occured!"


@app.route('/login')
def login():
    return render_template('./login.html')


@app.route('/login', methods=['POST'])
def log():
    email = request.form['email']
    password = request.form['password']
    user_avail = users.where('Email', "==", email).stream()
    user_avail = list(user_avail)
    lens = len(user_avail)

    if lens >= 1:
        user = user_avail[0]
        passw = user.to_dict()['Password']
        if password == passw:
            print("correct")
            session['email'] = email
            user_data = interests_db.document(email).get().to_dict()
            # user_data = list(user_data)
            interests = user_data['interests']
            print(interests)
            return redirect('interests')
        print("incorrect")
        return render_template('./login.html', error="incorrect password!!")
    else:
        return render_template('./login.html', error="user not exist")

    # try:
    #     users.document().set(data)
    #     return render_template('./interest.html')
    # except:

    #     return "There is error while registering... try again later.."


@app.route('/register', methods=['POST'])
def reg():
    email = request.form['email']
    password = request.form['password']
    user_avail = users.where('Email', "==", email).stream()
    if len(list(user_avail)) > 0:
        return render_template('./test.html', error="User already exists!!")
    data = {
        "Email": email,
        "Password": password
    }
    try:
        users.document().set(data)
        session['email'] = email
        return render_template('./interest.html', interestsD=[])
    except:

        return "There is error while registering... try again later.."


def job():
    print("hello")
    all_users = interests_db.stream()
    all_users = list(all_users)
    for user in all_users:
        interests = user.to_dict()['interests']
        email = user.to_dict()['email']
        receiver_email = email
        subject = 'Recommended Research Papers'
        # interests = ['machinelearning', 'datascience']

        # Fetch research papers based on user's interests
        papers = fetch_research_papers(interests)

        # Prepare the email message
        if len(papers) > 0:
            message = f"Dear User,\n\nHere are some recommended research papers based on your interests:\n\n"
            for paper in papers:
                message += f"Title: {paper['title']}\n"
                message += f"Authors: {paper['authors']}\n"
                message += f"PDF Link: {paper['abstract']}\n"
                message += f"Website: {paper['website']}\n\n"

            # Send the email
            send_email(sender_email, sender_password,
                       receiver_email, subject, message)
        else:
            message = f"Dear User,\n\nUnfortunately we are unable to fetch papers based on your interests:\n\n"
            send_email(sender_email, sender_password,
                       receiver_email, subject, message)


# job()
jobd = scheduler.add_job(job, 'interval', days=6)
scheduler.start()
# jobd.remove()
if __name__ == "__main__":
    app.run(debug=True)
# Example usage
# sender_email = 'vaisht1411@gmail.com'
# sender_password = 'gynxewqukdrsvlpc'
# receiver_email = 'vaishnavi.thakur2000@gmail.com'
# subject = 'Recommended Research Papers'
# interests = ['machinelearning', 'datascience']

# Fetch research papers based on user's interests
# papers = fetch_research_papers(interests)

# Prepare the email message
# message = f"Dear User,\n\nHere are some recommended research papers based on your interests:\n\n"
# for paper in papers:
#     message += f"Title: {paper['title']}\n"
#     message += f"Authors: {paper['authors']}\n"
#     message += f"PDF Link: {paper['abstract']}\n"
#     message += f"Website: {paper['website']}\n\n"

# # Send the email
# send_email(sender_email, sender_password, receiver_email, subject, message)
# print(sender_email, sender_password, receiver_email, subject, message)
