import torch
import torch.nn as nn
import torch.optim as optim

class GraphNNPredictor(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.node_embedding = nn.Linear(input_dim, 64)
        self.edge_weight = nn.Parameter(torch.randn(64, 64))
        self.gnn_layer1 = nn.Linear(64, 64)
        self.gnn_layer2 = nn.Linear(64, 32)
        self.classifier = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = torch.relu(self.node_embedding(x))
        
        adjacency = torch.sigmoid(torch.matmul(x, self.edge_weight))
        x = torch.matmul(adjacency, x)
        
        x = torch.relu(self.gnn_layer1(x))
        x = self.dropout(x)
        x = torch.relu(self.gnn_layer2(x))
        
        output = self.classifier(x)
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