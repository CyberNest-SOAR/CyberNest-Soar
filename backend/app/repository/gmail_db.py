import psycopg2
from psycopg2.extras import Json
from typing import List, Dict, Optional, Any
import base64
from email.utils import parsedate_to_datetime
import re
from google_apis import create_service


class GmailStorageManager:
    
    def __init__(self, db_config: Dict[str, str], client_secret_file: str = "client_secret.json"):
        self.db_config = db_config
        self.client_secret_file = client_secret_file
        self.gmail_service = create_service(
            client_secret_file, 
            "gmail", 
            "v1", 
            ["https://mail.google.com/"]
        )
        self.conn = None
        
    def connect_db(self):
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(**self.db_config)
        return self.conn
    
    def close_db(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            
    def _clean_body(self, body: str) -> str:
        clean = re.sub(r'<[^>]+>', '', body)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def _parse_email_data(self, message: Dict) -> Dict[str, Any]:
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(
                        part['body'].get('data', '')
                    ).decode('utf-8', errors='ignore')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(
                message['payload']['body']['data']
            ).decode('utf-8', errors='ignore')
        
        date_str = headers.get('Date', '')
        try:
            date = parsedate_to_datetime(date_str) if date_str else None
        except:
            date = None
        
        return {
            'gmail_id': message['id'],
            'subject': headers.get('Subject', ''),
            'sender': headers.get('From', ''),
            'recipients': headers.get('To', ''),
            'snippet': message.get('snippet', ''),
            'body': self._clean_body(body),
            'has_attachments': any(
                'filename' in part and part['filename'] 
                for part in message['payload'].get('parts', [])
            ),
            'date': date,
            'is_starred': 'STARRED' in message.get('labelIds', []),
            'labels': message.get('labelIds', []),
            'raw_headers': headers
        }
    
    def fetch_and_store_emails(self, query: str = '', max_results: int = 100, folder_name: str = "INBOX") -> int:
        try:
            label_ids = None
            if folder_name:
                label_results = self.gmail_service.users().labels().list(userId='me').execute()
                labels = label_results.get('labels', [])
                folder_label_id = next(
                    (label['id'] for label in labels if label['name'].lower() == folder_name.lower()),
                    None
                )
                if folder_label_id:
                    label_ids = [folder_label_id]
            
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                labelIds=label_ids,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            stored_count = 0
            
            conn = self.connect_db()
            cursor = conn.cursor()
            
            for msg in messages:
                try:
                    full_msg = self.gmail_service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    email_data = self._parse_email_data(full_msg)
                    
                    cursor.execute("""
                        INSERT INTO emails (
                            gmail_id, subject, sender, recipients, snippet,
                            body, has_attachments, date, is_starred, labels, raw_headers
                        ) VALUES (
                            %(gmail_id)s, %(subject)s, %(sender)s, %(recipients)s,
                            %(snippet)s, %(body)s, %(has_attachments)s, %(date)s,
                            %(is_starred)s, %(labels)s, %(raw_headers)s
                        )
                        ON CONFLICT (gmail_id) DO UPDATE SET
                            subject = EXCLUDED.subject,
                            is_starred = EXCLUDED.is_starred,
                            labels = EXCLUDED.labels
                    """, {**email_data, 'raw_headers': Json(email_data['raw_headers'])})
                    
                    stored_count += 1
                    
                except Exception as e:
                    print(f"Error fetching message {msg['id']}: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            
            return stored_count
            
        except Exception as error:
            print(f"An error occurred: {error}")
            return 0
    
    def insert_email(self, email_data: Dict[str, Any]) -> Optional[int]:
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO emails (
                    gmail_id, subject, sender, recipients, snippet,
                    body, has_attachments, date, is_starred, labels, raw_headers
                ) VALUES (
                    %(gmail_id)s, %(subject)s, %(sender)s, %(recipients)s,
                    %(snippet)s, %(body)s, %(has_attachments)s, %(date)s,
                    %(is_starred)s, %(labels)s, %(raw_headers)s
                )
                RETURNING id
            """, {**email_data, 'raw_headers': Json(email_data.get('raw_headers', {}))})
            
            email_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            return email_id
            
        except psycopg2.IntegrityError:
            conn.rollback()
            cursor.close()
            print(f"Email with gmail_id {email_data.get('gmail_id')} already exists")
            return None
    
    def update_email(self, gmail_id: str, updates: Dict[str, Any]) -> bool:
        if not updates:
            return False
        
        set_clause = ", ".join([f"{key} = %({key})s" for key in updates.keys()])
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"""
                UPDATE emails
                SET {set_clause}
                WHERE gmail_id = %(gmail_id)s
            """, {**updates, 'gmail_id': gmail_id})
            
            success = cursor.rowcount > 0
            conn.commit()
            cursor.close()
            
            return success
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            print(f"Error updating email: {e}")
            return False
    
    def delete_email(self, gmail_id: str) -> bool:
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM emails WHERE gmail_id = %s", (gmail_id,))
            success = cursor.rowcount > 0
            conn.commit()
            cursor.close()
            
            return success
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            print(f"Error deleting email: {e}")
            return False
    
    def get_email(self, gmail_id: str) -> Optional[Dict]:
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM emails WHERE gmail_id = %s", (gmail_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            return dict(zip(columns, row))
        
        cursor.close()
        return None
    
    def search_emails(self, filters: Dict[str, Any], limit: int = 50) -> List[Dict]:
        conn = self.connect_db()
        cursor = conn.cursor()
        
        where_clauses = []
        params = {}
        
        for key, value in filters.items():
            if key in ['sender', 'subject', 'recipients']:
                where_clauses.append(f"{key} ILIKE %({key})s")
                params[key] = f"%{value}%"
            elif key == 'is_starred':
                where_clauses.append(f"{key} = %({key})s")
                params[key] = value
            elif key == 'has_label':
                where_clauses.append(f"%({key})s = ANY(labels)")
                params[key] = value
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f"""
            SELECT * FROM emails
            WHERE {where_clause}
            ORDER BY date DESC
            LIMIT %(limit)s
        """, {**params, 'limit': limit})
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        
        return results
    
    def sync_starred_status(self, gmail_id: str) -> bool:
        try:
            msg = self.gmail_service.users().messages().get(
                userId='me',
                id=gmail_id,
                format='minimal'
            ).execute()
            
            is_starred = 'STARRED' in msg.get('labelIds', [])
            return self.update_email(gmail_id, {'is_starred': is_starred})
            
        except Exception as e:
            print(f"Error syncing starred status: {e}")
            return False