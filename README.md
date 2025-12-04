# Czech Election Scraper 2017

## Project Description

This Python script automatically downloads the results of the 2017 Czech Chamber of Deputies elections for all regions and their individual municipalities, and saves each region's results into a separate CSV file.  
The script scrapes the data directly from the official election website: https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ

## Installation of required libraries

Install the required libraries from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Running the Project

Run the script:

```bash
python script.py 
```
For each region, a CSV file will be created. When a file is saved successfully, the program prints: "Saved <output.csv>"
