# selenium-scraping
### setup 
#### chromedriver installation
```shell script
CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
sudo unzip chromedriver_linux64.zip -d /usr/bin
sudo chmod +x /usr/bin/chromedriver
```

#### conda environment
```shell script
conda create -n scraping python=3.8 -y
conda activate scraping
pip install -r requirements.txt
```
### corteconstitucional
* [server](https://www.corteconstitucional.gov.co) seems to be down at (colombian) nights for maintenance
* [__buscador de tutela__](corte_constitucional.py): scraping ids from the `Buscador de tutela` found at [secretaria](https://www.corteconstitucional.gov.co/secretaria/)
* [edictos](https://www.corteconstitucional.gov.co/secretaria/edictos/)

### use google account
* very tricky cause google does not like it
    * found working "work-around" in this [git-issue](https://gist.github.com/ikegami-yukino/51b247080976cb41fe93#gistcomment-3455633)
```
Hey! After researching into this to find the most practical way for a very long time, I think I've got it!

I use the following link:
https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?redirect_uri=https%3A%2F%2Fdevelopers.google.com%2Foauthplayground&prompt=consent&response_type=code&client_id=407408718192.apps.googleusercontent.com&scope=email&access_type=offline&flowName=GeneralOAuthFlow

This link comes from the oauth playground, which is an official tool Google provides to test oauth applications.
No GET parameter should expire in the URL.

It worked for me as of Tuesday, September 15th, 2020 with a Canadian account and IP. tada
```
#### howto
1. run (in debug mode) [automate_youtube.py](automate_youtube.py) or some other script that creates that opens up a chrome-browser using a chromedriver ([see](#user-content-chromedriver-installation)
2. while browser opened by chromedriver do login via this [link](https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?redirect_uri=https%3A%2F%2Fdevelopers.google.com%2Foauthplayground&prompt=consent&response_type=code&client_id=407408718192.apps.googleusercontent.com&scope=email&access_type=offline&flowName=GeneralOAuthFlow)
  (mentioned in the quote above)
3. install adblockers or whatever addons to chrome
### [automate_youtube.py](automate_youtube.py)
* __setup__: see [use google account](#user-content-use-google-account) 
* one has to adjust the `user_data_dir` variable: enter `chrome://version` in chrome-browser and copy-paste the `Profile Path`; but if there is a `Default` at the end, cut it away
* currently just to demonstrate the `search_strings` variable contains some example searches; -> one might want to read these from some file
    * -> TODO: where to get keywords/search-strings from?
    
### prevent getting blocked
* [scrapehero](https://www.scrapehero.com/how-to-prevent-getting-blacklisted-while-scraping/)
* [dev.to](https://dev.to/sonyarianto/user-agent-string-difference-in-puppeteer-headless-and-headful-4aoh)
* [making-chrome-headless-undetectable](https://intoli.com/blog/making-chrome-headless-undetectable/)