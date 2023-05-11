# Payments Analyst Candidate Challenge 💸

This project analyzes a given dataset of transaction records to identify potentially fraudulent transactions. The analysis is based on several rules, such as the transaction amount, user's historical data, and chargebacks.
It is a requirement for the Payments Analyst - Selection Process

## Requirements ✔️

- Python 3.8 or later

## Installation 💽

1. Clone the repository:

```
git clone git@github.com:rogerconsul/PaymentsAnalystRogerC.git
cd PaymentsAnalystRogerC/
```
2. Create a virtual environment:
```
python -m venv venv
```
3. Activate the virtual environment:

- For Windows:
```
venv\Scripts\activate
```
- For macOS and Linux:
```
source venv/bin/activate
```
4. Install the required packages:
```
pip install -r requirements.txt
```

## How to use 🖥

To run the transaction analysis, execute the following command:
```
python transaction-analysis.py
```
Follow the prompts to either analyze an individual transaction or all transactions. If you choose to analyze all transactions, a JSON will be created with all the denied transactions and with the reason for each one.
If you need to simulate a new transaction, select "Create a Transaction". You should provide an User ID and transaction value.

All the questions for the rest of the challenge are included in a PDF file inside. Don't forget to download it and read it as well 😉

