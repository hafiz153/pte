from pymongo import MongoClient

def migrate():
    client = MongoClient('mongodb://localhost:27017/')
    db = client.pte_project

    # Create 'scores' collection if it doesn't exist
    if 'scores' not in db.list_collection_names():
        db.create_collection('scores')
        print("Collection 'scores' created.")
    else:
        print("Collection 'scores' already exists.")

    client.close()

if __name__ == '__main__':
    migrate()