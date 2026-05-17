import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
import joblib

data = pd.read_csv("tickets.csv")

X = data["Ticket_Text"]

# Category Model
y_category = data["Category"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_category,
    test_size=0.2,
    random_state=42
)

category_model = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('classifier', MultinomialNB())
])

category_model.fit(X_train, y_train)

joblib.dump(
    category_model,
    "category_model.pkl"
)

# Priority Model

y_priority = data["Priority"]

X_train2, X_test2, y_train2, y_test2 = train_test_split(
    X,
    y_priority,
    test_size=0.2,
    random_state=42
)

priority_model = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('classifier', MultinomialNB())
])

priority_model.fit(X_train2, y_train2)

joblib.dump(
    priority_model,
    "priority_model.pkl"
)

print("Models created successfully")