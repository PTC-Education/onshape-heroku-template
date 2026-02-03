# onshape-heroku-template

## Overview

This repo explains the process for creating a Django app and hosting it on Heroku.  Most of the code is Python and I did all development on a Mac.  For local testing, I have an Onshape app extension with this Action URL:

`http://localhost:8000/oauthSignin?etype=partstudios&did={$documentId}&wvm={$workspaceOrVersion}&wvmid={$workspaceOrVersionId}&eid={$elementId}`

Once the app is on Heroku, the Action URL is:

`https://onshape-heroku-template-7c09166ec974.herokuapp.com/oauthSignin?did={$documentId}&wvm={$workspaceOrVersion}&wvmid={$workspaceOrVersionId}&eid={$elementId}`

The URL for the hosted Heroku app is in the Heroku dashboard under Settings -> Domains.

## Section 1 - Set Up the Django App

Create and empty repo in GitHub (I like to add a `README`, add a Python `.gitignore` and an MIT license.)

Clone the repo locally

Create a virtual environment and activate it:

```
python3 -m venv .venv
source .venv/bin/activate
````
Install Django

`pip install django`

Create Django project (use a suitable name)

`django-admin startproject onshape_oauth_project .` (with the period at the end)

This creates `manage.py` in your root folder and trhe `onshape_oauth_project/` folder with `settings.py`, `urls.py`, etc.

You should now have:
```
your-repo/
├── manage.py 
├── onshape_oauth_project/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── .gitignore
└── README.md
```

Now we're ready to make the app inside the Django project (that's the framework; a Django project with one ore more apps in it).

`python3 manage.py startapp onshape_app`

Now, you have

```
your-repo/
├── manage.py
├── onshape_oauth_project/    ← Project config (settings.py, urls.py)
├── onshape_app/              ← Your app (models.py, views.py)
├── venv/
├── .gitignore
├── README.md
└── LICENSE
```

Open `onshape_oauth_project/settings.py` and find the `INSTALLED_APPS` list.  Add `'onshape_app'` or whatever you called it (with the single quotes) at the end.

Next, we are going to create the framework to store Onshape users and their access tokens while they are using the app.  Using a Django database turned out to be easier than trying to store these things in session cookies.  

In `onshape_app/models.py` we create an `OnshapeUser` class (see actual code).  It creates the database structure for storing users with their OAuth tokens and other context variables.

Once `models.py` has been updated, we need to "migrate" the changes, meaning create/update the database.  

`python3 manage.py makemigrations` will create the instructions for what to build

`python3 manage.py migrate` will apply the changes.  You should now have a `db.sqlite3` file.

## Section 2 - Execute the OAuth Process

When the user opens the app, the app extension will call `oauthSignin`.  This request will be handled by the `oauth_signin` function in `views.py`.  Create that function now (see actual code).  

We also need to wire up the view so it's accessible as a view.  First, create `oauth_app/urls.py` and add the code to handle calls (see acutal code).

Next, update `onshape_oauth_project/urls.py` to connect the the app URLs to the main project (see actual code).

We are almost ready for the first test.  Open `settings.py` and add `X_FRAME_OPTIONS = 'ALLOWALL'` to the bottom.  This allows for local testing.

Next, we need to add environment variables.  If you haven't done so already, go to the Onshape Dev Portal and create your OAuth app for local testing.  You'll receive an OAuth client secret and key.  We need to create environment variables out of those.  In the Onshape OAuth tab, make sure the redirect URL is set to `http://localhost:8000/oauthRedirect`

In terminal run:
```
export OAUTH_URL=https://oauth.onshape.com
export OAUTH_CLIENT_ID=xxxxxxxxxxxxxxxxxxx
export OAUTH_CLIENT_SECRET=xxxxxxxxxxxxxxx
```
When the user opens the app, `oauth_signin` will use these variables to authenticate the user.  Then, `oauthRedirect` will be called.  You should have already added `path('oauthRedirect/', views.authorize, name='authorize')` to `urls.py` to handle this.

Add the following function to `views.py`

```python
def authorize(request: HttpRequest):
    code = request.GET.get('code')
    return HttpResponse(f"Authorization callback received! Code: {code}")
```

We're ready for our first test! Run this line:

`python3 manage.py runserver`

Then open the right-panel app.  You should see the successful authorization message.

The last step is to exchange the aurthorization code for tokens and store them.

First, you might need to 

`pip install requests`

Then, update the `authorize` function to handle and store the tokens (see actual code).

## Section 3 - Recirect to index.html

Inside the `onshape_app/` folder, create the following structure.  It's a little much to have all of these directories, but it's Django best practice.

```
onshape_app/
├── templates/
│   └── onshape_app/
│       └── index.html
```

The html can be something simple like:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Onshape OAuth App</title>
</head>
<body>
    <h1>Welcome to your Onshape App!</h1>
    <p>You're successfully authenticated.</p>
    <p>User ID: {{ user.os_user_id }}</p>
</body>
</html>
```

Add the `index` fucntion to `views.py` (make sure you are importing `render` from `django.shortcuts`)

```python
def index(request: HttpRequest):
    """
    Main app view - shown after successful OAuth
    """
    user = OnshapeUser.objects.first()
    return render(request, 'onshape_app/index.html', {'user': user})
```
Change the succeessful return statement in `authorize` to `return redirect('index')`

Add `path('', views.index, name='index')` to `urls.py`

## Section 4 - Prepate to Deploy to Heroku
Last step before moving to hosting: let's create `requirements.txt`.  This file is a list of all Python packages used by our project.  It can be used by anyone else replicating the project. Think of it as a shopping list of dependencies that makes your app portable and deployable 😃

Make sure virtual environment is activated then run `pip freeze > requirements.txt`

Install a couple of Heroku-specific packages:

`pip install gunicorn psycopg2-binary dj-database-url whitenoise`

Re-run `pip freeze > requirements.txt`

Create a new file in the project root (important) called `Procfile` and put one line in it.

`web: gunicorn onshape_oauth_project.wsgi`

This tells Heroku how to run our app.

In `settings.py`, do the following:

* Change `ALLOWED_HOSTS` to:

`ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.herokuapp.com']`

* Below the `DATABASES` add:

```python
# Use PostgreSQL on Heroku
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(conn_max_age=600)
```

* Add WhiteNoise to `MIDDLEWARE` right after `SecuirtyMiddleware` with this line 

`'whitenoise.middleware.WhiteNoiseMiddleware',`

* Add these lines to the bottom under `STATIC_URL`

```python
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

## Section 5 - Deploy to Heroku

* Log into Heroku
* Create new app
* Give it a name
* Create app
* Connect to GitHub
* Settings -> Reveal Config Vars.  Add these:
  * OAUTH_URL = https://oauth.onshape.com
  * OAUTH_CLIENT_ID = your client ID
  * OAUTH_CLIENT_SECRET = your client secret
* We need a db.  Go to Resources -> Add-on Services -> Search for Heroku Postgres
* Add the cheapest one.  It will take a minute or two to provision.
* Deploy -> Deploy Branch
* More -> Run console.  Run this: `python manage.py migrate`

You should be ready to test! 🚀

🍺