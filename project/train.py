import pickle
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

# Load dataset
data = load_breast_cancer()
X = data.data
y = data.target

# Split data
X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = SVC(kernel='linear', probability=True)
model.fit(X_train, Y_train)

# Evaluate
preds = model.predict(X_test)
print("Accuracy:", accuracy_score(Y_test, preds))

# Save model
with open("model/model.sav", "wb") as f:
    pickle.dump(model, f)

print("Model saved successfully to model/model.sav")
