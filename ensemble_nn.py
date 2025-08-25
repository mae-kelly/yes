import torch
import torch.nn as nn
import torch.optim as optim

class EnsembleNNPredictor(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.model1 = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8)
        )
        self.model2 = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 8)
        )
        self.model3 = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 16),
            nn.ReLU(),
            nn.Linear(16, 8)
        )
        self.combiner = nn.Sequential(
            nn.Linear(24, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        out1 = self.model1(x)
        out2 = self.model2(x)
        out3 = self.model3(x)
        combined = torch.cat([out1, out2, out3], dim=1)
        output = self.combiner(combined)
        return output.squeeze()
    
    def train_model(self, X_train, y_train, X_val, y_val, epochs=30):
        optimizer = optim.Adam(self.parameters(), lr=0.001)
        criterion = nn.BCELoss()
        
        for epoch in range(epochs):
            self.train()
            optimizer.zero_grad()
            outputs = self.forward(X_train)
            loss = criterion(outputs, y_train)
            loss.backward()
            optimizer.step()
    
    def predict(self, X):
        self.eval()
        with torch.no_grad():
            return self.forward(X)