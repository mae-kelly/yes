import torch
import torch.nn as nn
import torch.optim as optim

class AutoencoderPredictor(nn.Module):
    def __init__(self, input_dim, encoding_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, encoding_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )
        self.classifier = nn.Sequential(
            nn.Linear(encoding_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        classification = self.classifier(encoded)
        return decoded, classification.squeeze()
    
    def train_model(self, X_train, y_train, X_val, y_val, epochs=30):
        optimizer = optim.Adam(self.parameters(), lr=0.001)
        mse_loss = nn.MSELoss()
        bce_loss = nn.BCELoss()
        
        for epoch in range(epochs):
            self.train()
            optimizer.zero_grad()
            decoded, classification = self.forward(X_train)
            recon_loss = mse_loss(decoded, X_train)
            class_loss = bce_loss(classification, y_train)
            total_loss = recon_loss + class_loss
            total_loss.backward()
            optimizer.step()
    
    def predict(self, X):
        self.eval()
        with torch.no_grad():
            _, classification = self.forward(X)
            return classification