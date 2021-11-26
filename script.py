from modules.scraper import scrape
from modules.cliargs import parse_cliargs
import os
if __name__ == "__main__":
    os.environ['PATH']=os.environ['PATH']+r";C:\Users\uid11047\Downloads\chromedriver_win32"
    args = parse_cliargs()
    scrape(args)


