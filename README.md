
[//]: # ( challenge tech stack: streamlit )

[//]: # ( challenge instructions )

Let's create our own website ! 🔥

We are going to use **Streamlit** which will allow us to create a website very easily and without any web development skills.

## First, let's create another website project

We will create a new project directory for the code of our website.

Again, this directory will be located inside our *projects directory*: `~/code/<user.github_nickname>`.

Create a new project directory named `taxifare-website`.

```bash
cd ~/code/<user.github_nickname>
mkdir taxifare-website
cd taxifare-website
```

Initialise a new git repository:

```bash
git init
```

Create a corresponding repository on your **GitHub** account:

``` bash
gh repo create taxifare-website --private --source=. --remote=origin
```

Go to the GitHub repo to make sure that everything is ok:

``` bash
gh browse
```

The repository is empty, which is normal since we have not pushed any code yet...

We are now all set!

## Create a new python virtual environment

For our website, we will create **a new python virtual environment**.

### Why?

<details>
<summary markdown='span'>❓Think about it, and then read this:</summary>

**In the previous unit, we created an API** for our taxi-fare model. This API can be used by anyone. We used it from the browser for example, without any code. So, to use the API, we don't need data science libraries like Tensorflow anymore. Tensorflow is used **inside** our API, but **outside** users don't need it. That's why we created an API in the first place...

In this unit, **we are creating a website**. We are doing that using Python, because we are by now pretty comfortable using this little 🐍. If our product is succesful, we will ask web developers to create a fancy front-end for us. And they might do that in Python, or in Ruby or JavaScript, whatever they like. One thing is sure: they are not data scientists, and won't work with our data science packages.

**Long story short: we don't need our data science packages for our website.**
</details>
<br>

### Let's create the python environment

We'll follow the same procedure we used to create the `taxifare-env` environment, or the `lewagon` environment ages ago during setup day.

In your terminal, execute the following commands:

```bash
# Create a new virtual environment
pyenv virtualenv <YOUR_PYTHON_VERSION> taxifare-web

# Make this the default virtual environment for this repository
pyenv local taxifare-web

# Create a new requirements.txt for our project
touch requirements.txt

# Open our new project in VS Code
code .
```

Now, in VS Code, add to `requirements.txt` the packages we need for our frontend... Think a minute about what you will need.

<details>
<summary markdown='span'>So, what do you need❓</summary>

Well, it turns out we don't need anything but `streamlit` in our `requirements.txt`!

As we said before, we don't need any data science packages. We just need to be able to launch `streamlit`, and to make requests to our API.

To make requests, we need the `requests` package, but `streamlit` will already install that for us.

⚠️ **Don't include any of the [modules from base Python](https://docs.python.org/3/py-modindex.html)** or Streamlit Cloud will throw an error when deploying! For example, we'll need `datetime` later on, but that one comes out of the box with Python, so we don't add it to `requirements.txt`.

So, in your requirements.txt, just write:

```
streamlit
```

Save your file, and let's install everything (well, it's just `streamlit` actually) with:

```bash
pip install -r requirements.txt
```

All good? Now, let's create our website.
</details>



## Create a streamlit website

First, we need an `app.py` file inside of our project. The file will contain the code for our page.

``` bash
touch app.py
```

Then, let's copy the `Makefile` that you will find in the challenge folder. It will allow us to run useful commands like:
- `make install_requirements`: install dependencies.
- `make streamlit`: run the **Streamlit** web server in order to see what our website looks like on our local machine.


``` bash
cp ~/code/<user.github_nickname>/{{local_path_to('07-ML-Ops/05-User-interface/02-Taxifare-website')}}/Makefile ~/code/<user.github_nickname>/taxifare-website/
```

You project should look like this now:

``` bash
.
├── Makefile
├── app.py
└── requirements.txt
```

Not too overwhelming, right ? 😉

Well ... this is half the work.

Lets add some content to our website in `app.py`:

``` python
import streamlit as st

'''
# TaxiFareModel front
'''

st.markdown('''
Remember that there are several ways to output content into your web page...

Either as with the title by just creating a string (or an f-string). Or as with this paragraph using the `st.` functions
''')

'''
## Here we would like to add some controllers in order to ask the user to select the parameters of the ride

1. Let's ask for:
- date and time
- pickup longitude
- pickup latitude
- dropoff longitude
- dropoff latitude
- passenger count
'''

'''
## Once we have these, let's call our API in order to retrieve a prediction

See ? No need to load a `model.joblib` file in this app, we do not even need to know anything about Data Science in order to retrieve a prediction...

🤔 How could we call our API ? Off course... The `requests` package 💡
'''

url = 'https://taxifare.lewagon.ai/predict'

if url == 'https://taxifare.lewagon.ai/predict':

    st.markdown('Maybe you want to use your own API for the prediction, not the one provided by Le Wagon...')

'''

2. Let's build a dictionary containing the parameters for our API...

3. Let's call our API using the `requests` package...

4. Let's retrieve the prediction from the **JSON** returned by the API...

## Finally, we can display the prediction to the user
'''
```

Let's run the **Streamlit** web server and see what our website looks like:

``` bash
make streamlit
```

We have a website of our own running on our machine 🎉

## Now we want to plug our API to the website

... So that users can actually make some predictions!

👉 Let's follow the instructions inside the web page and replace the content with some `requests` package magic and a call to our API!

👉 Again, alternatively, you may use this Le Wagon **Prediction API URL** if you do not have one in production: https://taxifare.lewagon.ai/

Let's inspect `app.py` and check what is being done inside...

Replace the URL to the prediction API with your own API (if you have one running from the previous unit) and update the code to actually make a request and display the result.

Now let's get crazy with the page content 🎉

Maybe add some map 🗺

Once we are satisfied, let's push the code to production! 🔥


## Deploy

Let's setup the project for **Streamlit Cloud**.

❓ **What do we need to deploy our website to Streamlit Cloud ?**

We need to push our repository to GitHub

<details>
  <summary markdown='span'><strong> 💡 Hint </strong></summary>

``` bash
cd ~/code/<user.github_nickname>/taxifare-website && git add .
git commit -m 'My first website'
git push origin master
```

</details>
<br>

We also need a requirements file for our project with all the packages we need: that is the `requirements.txt` we already created before.

Let's make sure we only include packages we actually need 😉

<details>
  <summary markdown='span'><strong> 💡 Want to double check your project structure❓ </strong></summary>

The project should now look like this:

``` bash
.
├── Makefile
├── app.py
└── requirements.txt
```
</details>
<br>

Now it's time to deploy our website on **Streamlit Cloud**...

Go to [Streamlit Cloud](https://share.streamlit.io/) and create an account.
You can use any authentication method you want but using your GitHub account is the most efficient one as you will need access to your repository anyway 😉

Once signed in, you can create a new app following the steps shown during the lecture (feel free to take a look at the slides again).

❓ **How to update your app ?**

Your GitHub repository is the source for the app: each time you push an update to the `master/main` branch of your repo you will see it in the app in almost real time. Try it out!

🧠 If you make any changes to your `requirements.txt` and push those changes, Streamlit will automatically detect it and install the new packages!

😮 You can setup your own subdomain name in the settings of your app! Check the [documentation](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app#your-app-url).

That's it, your website is online ! 🚀

Feel free to explore all the possibilities of Streamlit and enhance your app !
➡️ Take a look at the [documentation](https://docs.streamlit.io/)

**If you want to make another app (for example for your project)**

Streamlit Cloud supports unlimited public repos, but only **one private repo**. So if you want to make a second one, one of your apps will need to be public, or you have to delete the first one.
