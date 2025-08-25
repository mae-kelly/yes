import torch
import torch.nn as nn
import torch.optim as optim

class ResidualBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.fc1 = nn.Linear(dim, dim)
        self.fc2 = nn.Linear(dim, dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, x):
        residual = x
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return self.relu(x + residual)

class ResidualPredictor(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.input_projection = nn.Linear(input_dim, 64)
        self.res_block1 = ResidualBlock(64)
        self.res_block2 = ResidualBlock(64)
        self.res_block3 = ResidualBlock(64)
        self.fc_out = nn.Linear(64, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        x = torch.relu(self.input_projection(x))
        x = self.res_block1(x)
        x = self.res_block2(x)
        x = self.res_block3(x)
        x = self.fc_out(x)
        return self.sigmoid(x).squeeze()
    
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