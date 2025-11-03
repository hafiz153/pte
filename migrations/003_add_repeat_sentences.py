from pymongo import MongoClient

def migrate():
    client = MongoClient('mongodb://localhost:27017/')
    db = client.pte_project

    sentences = [
        "The lecture will be held in the main auditorium.",
        "The advanced biology course is scheduled for next semester.",
        "Please submit your assignments before the end of the week.",
        "The research project requires extensive data analysis.",
        "The university provides a wide range of academic programs.",
        "Students are encouraged to participate in extracurricular activities.",
        "The library offers numerous resources for academic research.",
        "The professor will provide feedback on your essays next Tuesday.",
        "The campus facilities are open to all registered students.",
        "The final exam will cover all topics discussed in the lectures.",
        "Effective communication is crucial in academic and professional settings.",
        "The seminar focuses on the impact of technology on modern society.",
        "The career services office assists students with job placements.",
        "The enrollment deadline for the summer session is approaching.",
        "The guest speaker will discuss the latest trends in artificial intelligence."
    ]

    for i, sentence_text in enumerate(sentences):
        sentence_id = str(db.pte_sentences.count_documents({}) + 1 + i)
        db.pte_sentences.insert_one({"id": sentence_id, "text": sentence_text})
    print(f"Added {len(sentences)} repeat sentences to the database.")

if __name__ == '__main__':
    migrate()