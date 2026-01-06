import json
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self, filename='data.json'):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return {}
    
    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def get_user_data(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {
                'salary': 0,
                'credits': [],
                'debits': [],
                'borrowed': [],
                'lent': []
            }
            self.save_data()
        return self.data[user_id]
    
    def add_credit(self, user_id, amount, description=''):
        user_data = self.get_user_data(user_id)
        transaction = {
            'amount': amount,
            'description': description,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'credit'
        }
        user_data['credits'].append(transaction)
        self.save_data()
        return transaction
    
    def add_debit(self, user_id, amount, description=''):
        user_data = self.get_user_data(user_id)
        transaction = {
            'amount': amount,
            'description': description,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'debit'
        }
        user_data['debits'].append(transaction)
        self.save_data()
        return transaction
    
    def add_borrow(self, user_id, amount, from_whom, description=''):
        user_data = self.get_user_data(user_id)
        transaction = {
            'amount': amount,
            'from': from_whom,
            'description': description,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'returned': False
        }
        user_data['borrowed'].append(transaction)
        self.save_data()
        return transaction
    
    def add_lend(self, user_id, amount, to_whom, description=''):
        user_data = self.get_user_data(user_id)
        transaction = {
            'amount': amount,
            'to': to_whom,
            'description': description,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'received': False
        }
        user_data['lent'].append(transaction)
        self.save_data()
        return transaction
    
    def mark_borrow_returned(self, user_id, index):
        user_data = self.get_user_data(user_id)
        if 0 <= index < len(user_data['borrowed']):
            user_data['borrowed'][index]['returned'] = True
            self.save_data()
            return True
        return False
    
    def mark_lend_received(self, user_id, index):
        user_data = self.get_user_data(user_id)
        if 0 <= index < len(user_data['lent']):
            user_data['lent'][index]['received'] = True
            self.save_data()
            return True
        return False
    
    def get_balance(self, user_id):
        user_data = self.get_user_data(user_id)
        total_credits = sum(t['amount'] for t in user_data['credits'])
        total_debits = sum(t['amount'] for t in user_data['debits'])
        return total_credits - total_debits
    
    def get_last_30_days_transactions(self, user_id):
        user_data = self.get_user_data(user_id)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        all_transactions = []
        
        for credit in user_data['credits']:
            trans_date = datetime.strptime(credit['date'], '%Y-%m-%d %H:%M:%S')
            if trans_date >= thirty_days_ago:
                all_transactions.append(credit)
        
        for debit in user_data['debits']:
            trans_date = datetime.strptime(debit['date'], '%Y-%m-%d %H:%M:%S')
            if trans_date >= thirty_days_ago:
                all_transactions.append(debit)
        
        all_transactions.sort(key=lambda x: x['date'], reverse=True)
        return all_transactions
    
    def get_yesterday_stats(self, user_id):
        user_data = self.get_user_data(user_id)
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        yesterday_credits = sum(
            t['amount'] for t in user_data['credits']
            if datetime.strptime(t['date'], '%Y-%m-%d %H:%M:%S').date() == yesterday
        )
        
        yesterday_debits = sum(
            t['amount'] for t in user_data['debits']
            if datetime.strptime(t['date'], '%Y-%m-%d %H:%M:%S').date() == yesterday
        )
        
        savings = yesterday_credits - yesterday_debits
        
        return {
            'income': yesterday_credits,
            'expense': yesterday_debits,
            'savings': savings
        }
    
    def get_pending_borrows(self, user_id):
        user_data = self.get_user_data(user_id)
        return [b for b in user_data['borrowed'] if not b['returned']]
    
    def get_pending_lends(self, user_id):
        user_data = self.get_user_data(user_id)
        return [l for l in user_data['lent'] if not l['received']]
