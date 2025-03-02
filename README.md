# CarbonIQ - Travel Carbon Footprint Tracker

## Overview
CarbonIQ is a web application designed to help individuals track their carbon footprint from travel activities. It provides insights into carbon emissions and promotes sustainable travel habits.

## Tech Stack
- *Backend:* Django
- *Frontend:* HTML, CSS, JavaScript
- *Database:* PostgreSQL
- *APIs Used:*
  - Ola Maps API (for route mapping and distance calculations)
  - Gemini AI API (for intelligent insights and recommendations)
- *ML Algorithm*
  - Random Forest Regressor (For predicting carbon footprint)

## Features
- *User Authentication:* Secure login and profile management
- *Trip Logging:* Log travel details and calculate carbon footprint
- *Leaderboard:* Compare carbon footprint with other users
- *Challenges:* Participate in sustainability challenges
- *Insights:* AI-powered recommendations for reducing carbon footprint
- *Reward:* Get rewards for the tokens you earn by completing challenges

## Installation & Setup
### Prerequisites
Ensure you have the following installed:
- Python (>=3.8)
- PostgreSQL
- Django

### Steps to Run Locally
1. *Clone the repository:*
   <br>```git clone https://github.com/Mayank-711/CarboniQ_Codeverse.git```
   <br>```cd CarbonIQ_Codeverse```
   

3. *Set up the virtual environment:*
   <br>```python -m venv env```
   <br>```source env/bin/activate  # On Windows use `env\Scripts\activate```
   

4. *Install dependencies:*
   <br>```pip install -r requirements.txt```
   

5. *Set up the database:*
   <br>```psql -U postgres```
   <br>```CREATE DATABASE carboniq;```
   <br>```ALTER USER your_user WITH PASSWORD 'your_password';```
   
    Update DATABASES in settings.py accordingly.

6. *Run migrations:*
   <br>```python manage.py migrate```
   

7. *Run the development server:*
   <br>```python manage.py runserver```
   

8. *Access the application:*
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Contribution Guidelines
We welcome contributions! Follow these steps:
1. *Fork the repository* on GitHub.
2. *Create a new branch* for your feature:
   <br>```git checkout -b feature-branch```
   
3. *Make your changes* and commit them:
   <br>```git commit -m "Add new feature"```
   
4. *Push to your branch:*
   <br>```git push origin feature-branch```
   
5. *Submit a Pull Request (PR)* for review.

## License
This project is licensed under the MIT License.

## Contact
For any queries or collaborations, reach out to [@Mayank](https://github.com/Mayank-711).
