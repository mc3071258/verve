# wad2-group-project
Coursework repository for WAD2 group web application project.

## Verve

Verve is a social, text-based party game platform which allows users to select
between different games: Truth or Dare, Never Have I Ever and Would You Rather.
They may browse, create or interact with user submitted prompts.
Guests and registered users are able to play games by viewing prompts and
navigating through them. Registered users can also contribute their own prompts,
follow other users and manage their profile.
This platform is designed as a scalable prompt based system, which means that
new games can easily be added without having to alter underlying structure. All
games operate using the same data model with text based prompts linked to a
specific game, ensuring they are all consistent.
Verve allows its user to vote for their favourite prompts and it is intended to be
used recreationally, to allow users to engage with entertaining games, whether
solo or with a larger group.

## Tech stack
- Backend: Django
- Frontend: Bootstrap

## Prerequisites
- Python 3.12 
- pip

## Run locally
Clone the project
~~~bash
git clone https://github.com/mc3071258/verve.git
~~~
Go to the project directory
~~~bash 
cd verve
~~~

Create and activate a virtual environment
~~~bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
~~~

Install dependencies 
~~~bash
pip install -r requirements.txt   
~~~

Database setup
~~~bash
python manage.py migrate
~~~

Optioanlly test
~~~          
python manage.py check
python manage.py test
~~~

Run server 
~~~bash
python manage.py runserver
~~~

## External sources
- *Tango with Django 2* (Azzopardi & Maxwell) - learning patterns and “progress tests” style used in book.

- Django docs (Models): https://docs.djangoproject.com/en/5.2/topics/db/models/
- Django docs (Model field reference, e.g., ForeignKey, blank/null, etc.): https://docs.djangoproject.com/en/5.2/ref/models/fields/
- Django docs (Model constraints, UniqueConstraint/CheckConstraint + conditions): https://docs.djangoproject.com/en/5.2/ref/models/constraints/
- Django docs (Database transactions, transaction.atomic, TestCase isolation): https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- Django docs (Testing overview): https://docs.djangoproject.com/en/5.2/topics/testing/overview/
- Django docs (Auth customization, AUTH_USER_MODEL + get_user_model): https://docs.djangoproject.com/en/5.2/topics/auth/customizing/
- Django docs (Deprecation, CheckConstraint `check=` removal): https://docs.djangoproject.com/en/5.2/internals/deprecation/
