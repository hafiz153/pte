from pymongo import MongoClient

def migrate():
    client = MongoClient('mongodb://localhost:27017/P1')
    db = client.pte_project
    sentences_collection = db.pte_sentences

    # Clear existing sentences (optional, for fresh migration)
    sentences_collection.delete_many({})

    # Generate 1000 placeholder PTE repeat sentences
    pte_sentences = []
    for i in range(1, 1001):
        pte_sentences.append({"id": str(i), "text": f"This is PTE repeat sentence number {i}. Please repeat it carefully."})

    sentences_collection.insert_many(pte_sentences)
    print(f"Inserted {len(pte_sentences)} PTE repeat sentences into MongoDB.")

    client.close()

if __name__ == '__main__':
    migrate()