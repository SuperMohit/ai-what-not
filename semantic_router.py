from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_distances



model = SentenceTransformer('all-MiniLM-L6-v2')

THRESHOLD = 0.5

# define the routes and their references
routes = [
    {
        'name': 'greeting',
        'priority': 1,
        'references': [
            'Hello!',
            'Hi there!',
            'Greetings!',
            'Good morning',
            'Good evening',
        ]
    },
    {
        'name': 'farewell',
        'priority': 2,
        'references': [
            'Goodbye',
            'See you later',
            'Farewell',
            'Take care',
            'Bye!',
        ]
    },
    {
        'name': 'weather',
        'priority': 3,
        'references': [
            'What is the weather like?',
            'Tell me the weather forecast',
            'Is it going to rain today?',
            'Weather update',
            'How is the weather?',
        ]
    }
]

# cache the reference embeddings
for route in routes:
    route['reference_embeddings'] = [model.encode([reference]) for reference in route['references']]
    


def semantic_router(query):
    query_embedding = model.encode([query])

    route_scores = []

    for route in routes:
        reference_embeddings = route['reference_embeddings']
        # Calculate cosine distances between the query and each reference
        distances = []
        
        for reference_embedding in reference_embeddings:
            distances.append (cosine_distances(query_embedding, reference_embedding))


        # Aggregate the distances (take the average)
        min_distance = np.min(distances)
        #print(average_distance)
        # Check against the threshold
        if min_distance < THRESHOLD:
            route_scores.append({
                'name': route['name'],
                'priority': route['priority'],
                'min_distance': min_distance
            })

    if not route_scores:
        return None

    # Sort the routes based on priority and average distance
    route_scores.sort(key=lambda x: (x['priority'], x['min_distance']))

    return route_scores[0]



if __name__ == "__main__":
    test_queries = [
        "Hey, how are you?",
        "See you soon!",
        "Will it be sunny tomorrow?",
        "What's the meaning of life?"
    ]

    for query in test_queries:
        result = semantic_router(query)
        if result:
            print(f"Query: '{query}'\nMatched Route: {result['name']}, Priority: {result['priority']}, Min Distance: {result['min_distance']:.4f}\n")
        else:
            print(f"Query: '{query}'\nNo matching route found.\n")
