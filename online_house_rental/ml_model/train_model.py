import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import os
import numpy as np

def train_rental_model():
    # Load the data
    data = pd.read_csv('rental_data.csv')
    
    # Initialize label encoders for categorical variables
    district_encoder = LabelEncoder()
    city_encoder = LabelEncoder()
    property_type_encoder = LabelEncoder()
    
    # Encode categorical variables
    data['district_encoded'] = district_encoder.fit_transform(data['district'])
    data['city_encoded'] = city_encoder.fit_transform(data['city'])
    data['property_type_encoded'] = property_type_encoder.fit_transform(data['property_type'])
    
    # Feature selection and target variable
    X = data[['area', 'bedrooms', 'bathrooms', 'district_encoded', 
              'city_encoded', 'property_type_encoded']]
    y = data['price']
    
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train the Random Forest model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Model Performance Metrics:")
    print(f"Mean Absolute Error: {mae:.2f}")
    print(f"Root Mean Squared Error: {np.sqrt(mse):.2f}")
    print(f"R² Score: {r2:.2f}")
    
    # Create a dictionary with the model and encoders
    model_artifacts = {
        'model': model,
        'district_encoder': district_encoder,
        'city_encoder': city_encoder,
        'property_type_encoder': property_type_encoder
    }
    
    # Ensure the directory exists
    model_dir = 'ml_models'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    
    # Save the model and encoders
    with open(f'{model_dir}/rental_price_model.pkl', 'wb') as file:
        pickle.dump(model_artifacts, file)

if __name__ == "__main__":
    train_rental_model()
