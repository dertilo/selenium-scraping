# selenium-scraping

* chrome driver installation
```shell script
CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
sudo unzip chromedriver_linux64.zip -d /usr/bin
sudo chmod +x /usr/bin/chromedriver
```

* setup
```shell script
conda create -n scraping python=3.8 -y
conda activate scraping
pip install -r requirements.txt
```
### corteconstitucional
* [server](https://www.corteconstitucional.gov.co) seems to be down at (colombian) nights for maintenance
* [__buscador de tutela__](corte_constitucional.py): scraping ids from the `Buscador de tutela` found at [secretaria](https://www.corteconstitucional.gov.co/secretaria/)
* [edictos](https://www.corteconstitucional.gov.co/secretaria/edictos/)

### prevent getting blocked
* [scrapehero](https://www.scrapehero.com/how-to-prevent-getting-blacklisted-while-scraping/)
* [dev.to](https://dev.to/sonyarianto/user-agent-string-difference-in-puppeteer-headless-and-headful-4aoh)
* [making-chrome-headless-undetectable](https://intoli.com/blog/making-chrome-headless-undetectable/)