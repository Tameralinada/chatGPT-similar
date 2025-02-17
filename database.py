import peewee as pw
from datetime import datetime
import os
from contextlib import contextmanager

# Get the directory where the database file will be stored
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DB_DIR, 'chat_history.db')

# Database connection management
db = pw.SqliteDatabase(DB_FILE, pragmas={
    'journal_mode': 'wal',  # Write-Ahead Logging for better concurrency
    'cache_size': -1024 * 64,  # 64MB cache
    'foreign_keys': 1,  # Enable foreign key support
    'ignore_check_constraints': 0,
    'synchronous': 0  # Reduce disk I/O
})

@contextmanager
def db_connection():
    """Context manager for database connections"""
    try:
        db.connect(reuse_if_open=True)
        yield db
    finally:
        if not db.is_closed():
            db.close()

class BaseModel(pw.Model):
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super(BaseModel, self).save(*args, **kwargs)
    
    class Meta:
        database = db

class Messages(BaseModel):
    id = pw.AutoField()
    question = pw.TextField(index=True)
    answer = pw.TextField()
    timestamp = pw.DateTimeField(default=datetime.now, index=True)
    chat_id = pw.CharField(default='default', index=True)
    
    class Meta:
        table_name = 'messages'
        indexes = (
            (('chat_id', 'timestamp'), True),  # Composite index
        )

def initialize_database():
    """Initialize the database with proper error handling"""
    with db_connection():
        db.create_tables([Messages], safe=True)

def save_message(question, answer, chat_id='default'):
    """Save a message pair to the database."""
    try:
        with db_connection():
            Messages.create(
                question=question,
                answer=answer,
                chat_id=chat_id,
                timestamp=datetime.now()
            )
        return True
    except Exception as e:
        print(f"Error saving message: {str(e)}")
        return False

def get_chat_history(chat_id=None, limit=50):
    """Get recent chat history with proper connection handling."""
    try:
        with db_connection():
            query = (Messages
                    .select()
                    .order_by(Messages.timestamp.desc()))
            if chat_id:
                query = query.where(Messages.chat_id == chat_id)
            return list(query.limit(limit))  # Materialize the query within the connection
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return []

def delete_chat(chat_id):
    """Delete all messages from a specific chat with proper connection handling."""
    try:
        with db_connection():
            return (Messages
                    .delete()
                    .where(Messages.chat_id == chat_id)
                    .execute() > 0)
    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        return False

def get_chat_folders():
    """Get list of unique chat folders with proper connection handling."""
    try:
        with db_connection():
            # Get the first message (question) for each chat_id along with the last message timestamp
            subquery = (Messages
                       .select(
                           Messages.chat_id,
                           Messages.question,
                           Messages.timestamp
                       )
                       .order_by(Messages.timestamp)
                       .group_by(Messages.chat_id))
            
            return list(Messages
                       .select(
                           Messages.chat_id,
                           Messages.question,
                           pw.fn.MAX(Messages.timestamp).alias('last_message')
                       )
                       .group_by(Messages.chat_id)
                       .order_by(pw.SQL('last_message').desc()))
    except Exception as e:
        print(f"Error getting chat folders: {str(e)}")
        return []

def search_messages(query, limit=10):
    """Search messages by content."""
    try:
        with db_connection():
            return list(Messages
                       .select()
                       .where(
                           (Messages.question.contains(query)) |
                           (Messages.answer.contains(query))
                       )
                       .order_by(Messages.timestamp.desc())
                       .limit(limit))
    except Exception as e:
        print(f"Error searching messages: {str(e)}")
        return []

# Initialize the database
initialize_database()
