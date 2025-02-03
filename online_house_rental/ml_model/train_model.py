import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
import pickle
import os

def train_rental_model():
    # Load the data
    data = pd.read_csv('rental_data.csv')
    
    # Feature selection and target variable
    X = data[['area', 'bedrooms', 'bathrooms']]
    y = data['price']
    
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train the model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Model trained successfully! Mean Absolute Error: {mae}")
    
    # Ensure the directory exists
    model_dir = 'ml_models'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    
    # Save the model
    with open(f'{model_dir}/rental_price_model.pkl', 'wb') as file:
        pickle.dump(model, file)

# Train the model
train_rental_model()
