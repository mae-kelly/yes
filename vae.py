import torch
import torch.nn as nn
import torch.optim as optim

class VAEPredictor(nn.Module):
    def __init__(self, input_dim, latent_dim=16):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc2_mu = nn.Linear(64, latent_dim)
        self.fc2_logvar = nn.Linear(64, latent_dim)
        self.fc3 = nn.Linear(latent_dim, 64)
        self.fc4 = nn.Linear(64, input_dim)
        self.classifier = nn.Sequential(
            nn.Linear(latent_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid()
        )
        
    def encode(self, x):
        h = torch.relu(self.fc1(x))
        return self.fc2_mu(h), self.fc2_logvar(h)
    
    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def decode(self, z):
        h = torch.relu(self.fc3(z))
        return self.fc4(h)
    
    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        decoded = self.decode(z)
        classification = self.classifier(z)
        return decoded, mu, logvar, classification.squeeze()
    
    def train_model(self, X_train, y_train, X_val, y_val, epochs=30):
        optimizer = optim.Adam(self.parameters(), lr=0.001)
        
        for epoch in range(epochs):
            self.train()
            optimizer.zero_grad()
            decoded, mu, logvar, classification = self.forward(X_train)
            
            BCE = nn.functional.binary_cross_entropy_with_logits(decoded, X_train, reduction='sum')
            KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
            class_loss = nn.functional.binary_cross_entropy(classification, y_train, reduction='sum')
            
            loss = BCE + KLD + class_loss
            loss.backward()
            optimizer.step()
    
    def predict(self, X):
        self.eval()
        with torch.no_grad():
            _, _, _, classification = self.forward(X)
            return classification