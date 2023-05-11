import pandas as pd
import json
import subprocess


# rules to determine if a transaction is safe or not
time_threshold = 60 # 1 minute
transaction_count_threshold = 3
multiplier = 1.5 # percentage above average transaction value allowed.
time_period = 30


df = pd.read_csv("transactional-sample.csv")
df['transaction_date'] = pd.to_datetime(df['transaction_date'], format="%Y-%m-%dT%H:%M:%S.%f")
df['transaction_amount'] = pd.to_numeric(df['transaction_amount'])


def save_chargeback_users(df):
    """
    Save all user_id that had at least 1 chargeback to a CSV file, with no duplicate user_id, along with the date of their first chargeback.
    """
    chargeback_users = df.loc[df['has_cbk'] == True, ['user_id', 'transaction_date']]
    chargeback_users = chargeback_users.groupby('user_id').agg({'transaction_date': 'min'}).reset_index()
    chargeback_users.to_csv('chargeback_users.csv', index=False)


def too_many_transactions(user_id, time_threshold, transaction_count_threshold, df):
    user_transactions = df[df['user_id'] == user_id].copy()
    user_transactions.sort_values(by='transaction_date', inplace=True)

    count = 1
    for idx, row in enumerate(user_transactions[:-1].itertuples()):
        time_difference = (user_transactions.iloc[idx + 1].transaction_date - row.transaction_date).total_seconds()

        if time_difference <= time_threshold:
            count += 1
        else:
            count = 1

        if count >= transaction_count_threshold:
            return True

    return False


def high_value_transactions(user_id, transaction_amount, multiplier, df):
    time_period = '1500D'  # Hard code the time period here
    min_transactions = 3  # Hard code the minimum transactions here
    user_transactions = df[df['user_id'] == user_id]
    
    # Check if there are enough historical transactions for the user
    if len(user_transactions) < min_transactions:
        return False  # Return False if there's not enough history
    
    average_amount = user_transactions['transaction_amount'].mean()
    amount_threshold = average_amount * multiplier
    recent_transactions = user_transactions[user_transactions['transaction_date'] >= (pd.Timestamp.now() - pd.to_timedelta(time_period))]
    high_value_transactions = recent_transactions[recent_transactions['transaction_amount'] > amount_threshold]
    
    # Return True if there are any high value transactions, False otherwise
    return high_value_transactions.empty



def had_chargeback_before(user_id, transaction_date):
    chargeback_users_df = pd.read_csv('chargeback_users.csv')
    user_cbk = chargeback_users_df.loc[chargeback_users_df['user_id'] == user_id]
    
    # Check if user has any chargebacks before transaction date
    if not user_cbk.empty:
        earliest_cbk_date = user_cbk['transaction_date'].min()
        return pd.to_datetime(earliest_cbk_date) < pd.to_datetime(transaction_date)

    return False


def analyze_individual_transaction(transaction_id, time_threshold, transaction_count_threshold, multiplier, time_period, df):
    """
    Analyze a single transaction and return a dictionary with the decision and reason for that transaction.
    """
    transaction_rows = df.loc[df['transaction_id'] == transaction_id]
    
    if transaction_rows.empty:  # Check if the transaction_id is not found
        return {'transaction_id': transaction_id, 'error': 'Transaction not found'}

    transaction = transaction_rows.iloc[0]
    user_id = transaction['user_id']
    transaction_amount = transaction['transaction_amount']
    transaction_date = pd.to_datetime(transaction['transaction_date'])
 
    # Check if the user has made too many transactions in a row
    too_many = too_many_transactions(user_id, time_threshold, transaction_count_threshold, df)

    # Check if the transaction amount is too high compared to the user's historical data
    high_value = high_value_transactions(user_id, transaction_amount, multiplier, df)

    # Check if the user has had a chargeback before
    chargeback = had_chargeback_before(user_id, transaction_date)

    # Make a decision based on the rules
    if too_many:
        decision = 'denied'
        reason = 'Too many transactions in a row'
    elif high_value:  # Check if high_value is True
        decision = 'denied'
        reason = 'Transaction amount is too high compared to the user\'s historical data'
    elif chargeback:
        decision = 'denied'
        reason = 'User has had a chargeback before'
    else:
        decision = 'approved'
        reason = 'N/A'
     
    # Create a dictionary with the decision and reason for this transaction
    transaction_decision = {'transaction_id': transaction_id, 'decision': decision, 'reason': reason}
 
    return transaction_decision



def analyze_all_transactions(df, time_threshold, transaction_count_threshold, multiplier, time_period):
    denied_transactions = []
    for transaction_id in df['transaction_id']:
        decision = analyze_individual_transaction(transaction_id, time_threshold, transaction_count_threshold, multiplier, time_period, df)
        if decision['decision'] == 'denied':
            denied_transactions.append({'transaction_id': transaction_id, 'rejected': True, 'reason': decision['reason']})
    return denied_transactions


def create_transaction(user_id, transaction_amount):
    df = pd.read_csv("transactional-sample.csv")
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format="%Y-%m-%dT%H:%M:%S.%f")
    df['transaction_amount'] = pd.to_numeric(df['transaction_amount'])

    # Get the highest transaction id
    last_transaction_id = df['transaction_id'].max()

    # Create new transaction id
    new_transaction_id = last_transaction_id + 1

    # Define merchant_id, card_number and device_id as 'undefined' or a suitable numeric value
    merchant_id = -1  # using -1 to signify 'undefined' for integer column
    card_number = 'undefined'  
    device_id = -1.0  # using -1.0 to signify 'undefined' for float column

    # Get current date for transaction_date
    transaction_date = pd.to_datetime('today').strftime("%Y-%m-%dT%H:%M:%S.%f")

    # Check if user had chargeback before
    has_cbk = had_chargeback_before(int(user_id), transaction_date)

    # Create new transaction
    new_transaction = {'transaction_id': int(new_transaction_id), 
                       'merchant_id': merchant_id, 
                       'user_id': int(user_id), 
                       'card_number': card_number, 
                       'transaction_date': pd.to_datetime(transaction_date), 
                       'transaction_amount': float(transaction_amount), 
                       'device_id': device_id, 
                       'has_cbk': bool(has_cbk)}
    
    # Convert the new transaction to a DataFrame
    new_transaction_df = pd.DataFrame([new_transaction])

    # Concatenate the new transaction DataFrame to the existing DataFrame
    df = pd.concat([df, new_transaction_df], ignore_index=True)

    # Save the updated DataFrame to the CSV file
    df.to_csv('transactional-sample.csv', index=False)

    print(f'Transaction {new_transaction_id} has been created.')

    # Analyze the new transaction
    decision = analyze_individual_transaction(new_transaction_id, time_threshold, transaction_count_threshold, multiplier, time_period, df)
    print(decision)

    script = ['rm', 'transactional-sample.csv']
    script2 = ['cp', './utils/transactional-sample.csv', '.']

    subprocess.run(script)
    subprocess.run(script2)


def main():
    # Load data
    df = pd.read_csv('transactional-sample.csv')

    # Convert 'transaction_date' column to datetime objects
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # Set initial status to 'approved'
    df['status'] = 'approved'

    # Save users with chargebacks
    print('Saving users with chargebacks...')
    save_chargeback_users(df)

    # Prompt user for action
    action = input('What do you want to do?\n1 - Analyze individual transaction\n2 - Analyze all transactions\n3 - Create a Transaction\n')

    # Analyze individual transaction
    if action == '1':
        transaction_id = input('Enter transaction ID: ')
        decision = analyze_individual_transaction(int(transaction_id), time_threshold, transaction_count_threshold, multiplier, time_period, df)
        print(decision)
        return

    # Analyze all transactions
    if action == '2':
        denied_transactions = analyze_all_transactions(df, time_threshold, transaction_count_threshold, multiplier, time_period)

        # Write denied transactions to a JSON file
        with open('denied_transactions.json', 'w') as f:
            json.dump(denied_transactions, f)

        print(f'{len(denied_transactions)} transactions were denied')
        return

    # Create a transaction
    if action == '3':
        user_id = input('Enter User ID: ')
        transaction_amount = input('Enter Transaction Amount: ')
        # Here you would call the function to create a transaction
        create_transaction(user_id, transaction_amount)
        return

    print('Invalid input')


if __name__ == "__main__":
    main()
