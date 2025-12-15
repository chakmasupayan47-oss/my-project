from model import train_model

if __name__ == '__main__':
    print("Starting model training...")
    model, scaler, feature_importance = train_model()
    print("Model training completed!")