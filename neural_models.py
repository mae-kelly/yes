import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import logging
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

logger.info(f"Neural models using device: {device}")

class BiLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=256, num_layers=3, dropout=0.3):
        super().__init__()
        self.embedding = nn.Linear(input_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers, 
                           batch_first=True, bidirectional=True, dropout=dropout)
        self.attention = nn.MultiheadAttention(hidden_size * 2, num_heads=8)
        self.fc1 = nn.Linear(hidden_size * 2, hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()
        
        logger.info(f"BiLSTM initialized: {num_layers} layers, hidden_size={hidden_size}")
        
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        x = self.embedding(x)
        lstm_out, (hidden, cell) = self.lstm(x)
        
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        combined = lstm_out + attn_out
        
        x = self.fc1(combined[:, -1, :])
        x = self.dropout(x)
        x = self.fc2(x)
        return self.sigmoid(x)

class TransformerModel(nn.Module):
    def __init__(self, input_size, d_model=512, nhead=8, num_layers=6, dropout=0.3):
        super().__init__()
        self.embedding = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, 
            dim_feedforward=2048, dropout=dropout,
            activation='gelu', batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        
        self.fc1 = nn.Linear(d_model, d_model // 2)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(d_model // 2, 1)
        
        logger.info(f"Transformer initialized: {num_layers} layers, {nhead} heads, d_model={d_model}")
        
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        x = self.embedding(x)
        x = self.pos_encoder(x)
        x = self.transformer_encoder(x)
        
        x = x.mean(dim=1)
        
        x = self.fc1(x)
        x = torch.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return torch.sigmoid(x)

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)
        
    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class NeuralNetworkSuite:
    def __init__(self):
        self.lstm_model = None
        self.transformer_model = None
        self.scaler = StandardScaler()
        self.feature_dim = 100
        
        logger.info("Neural Network Suite initialized")
        
    def extract_features(self, hostname):
        features = []
        
        if not hostname:
            return np.zeros(self.feature_dim)
        
        h = hostname.lower()
        
        features.extend([
            len(h),
            h.count('.'), h.count('-'), h.count('_'),
            len([c for c in h if c.isdigit()]),
            len([c for c in h if c.isalpha()]),
            1 if h[0].isdigit() else 0,
            1 if h[-1].isdigit() else 0
        ])
        
        for i in range(min(20, len(h))):
            features.append(ord(h[i]) / 128.0)
        
        while len(features) < 30:
            features.append(0)
        
        keywords = ['srv', 'server', 'web', 'www', 'db', 'database', 'app', 'prod', 
                   'dev', 'test', 'stage', 'uat', 'fw', 'firewall', 'lb', 'proxy',
                   'dns', 'mail', 'backup', 'vm', 'docker', 'k8s', 'aws', 'azure',
                   'gcp', 'cloud', '1dc', '2dc', 'north', 'south', 'east', 'west']
        
        for kw in keywords:
            features.append(1.0 if kw in h else 0.0)
        
        ngrams = []
        for n in [2, 3, 4]:
            if len(h) >= n:
                grams = [h[i:i+n] for i in range(len(h)-n+1)]
                ngrams.append(len(set(grams)) / len(grams) if grams else 0)
            else:
                ngrams.append(0)
        features.extend(ngrams)
        
        while len(features) < self.feature_dim:
            features.append(0)
        
        return np.array(features[:self.feature_dim])
    
    def prepare_data(self, df):
        logger.info(f"Preparing data from {len(df)} records")
        
        X = []
        y = []
        
        for _, row in df.iterrows():
            features = self.extract_features(row.get('host', ''))
            X.append(features)
            
            label = 0.0
            if row.get('present_in_cmdb') == 'yes':
                label += 0.4
            if row.get('logging_in_splunk') == 'yes':
                label += 0.3
            if row.get('logging_in_gso') == 'yes':
                label += 0.15
            if row.get('edr_coverage') and row.get('edr_coverage') != 'none':
                label += 0.15
            
            y.append(min(label, 1.0))
        
        X = np.array(X)
        y = np.array(y)
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        X_train = self.scaler.fit_transform(X_train)
        X_val = self.scaler.transform(X_val)
        
        logger.info(f"Data prepared: {len(X_train)} training, {len(X_val)} validation samples")
        
        return X_train, X_val, y_train, y_val
    
    def train_lstm(self, df):
        logger.info("Training Bidirectional LSTM with attention mechanism")
        
        X_train, X_val, y_train, y_val = self.prepare_data(df)
        
        self.lstm_model = BiLSTM(self.feature_dim).to(device)
        
        optimizer = optim.AdamW(self.lstm_model.parameters(), lr=0.001, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
        criterion = nn.BCELoss()
        
        batch_size = 512 if device.type != 'cpu' else 64
        epochs = 50
        
        logger.info(f"Training for {epochs} epochs with batch size {batch_size}")
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        import time
        start_time = time.time()
        
        for epoch in range(epochs):
            self.lstm_model.train()
            train_loss = 0
            
            for i in range(0, len(X_train), batch_size):
                batch_X = torch.FloatTensor(X_train[i:i+batch_size]).to(device)
                batch_y = torch.FloatTensor(y_train[i:i+batch_size]).unsqueeze(1).to(device)
                
                optimizer.zero_grad()
                outputs = self.lstm_model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                
                torch.nn.utils.clip_grad_norm_(self.lstm_model.parameters(), 1.0)
                
                optimizer.step()
                train_loss += loss.item()
            
            self.lstm_model.eval()
            val_loss = 0
            correct = 0
            
            with torch.no_grad():
                for i in range(0, len(X_val), batch_size):
                    batch_X = torch.FloatTensor(X_val[i:i+batch_size]).to(device)
                    batch_y = torch.FloatTensor(y_val[i:i+batch_size]).unsqueeze(1).to(device)
                    
                    outputs = self.lstm_model(batch_X)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()
                    
                    predicted = (outputs > 0.5).float()
                    correct += (predicted == batch_y).sum().item()
            
            accuracy = correct / len(X_val)
            avg_val_loss = val_loss / (len(X_val) / batch_size)
            
            scheduler.step(avg_val_loss)
            
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
            else:
                patience_counter += 1
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}/{epochs}, Val Loss: {avg_val_loss:.4f}, Accuracy: {accuracy:.2%}")
            
            if patience_counter >= 10:
                logger.info(f"Early stopping at epoch {epoch}")
                break
        
        training_time = time.time() - start_time
        
        logger.info(f"LSTM training completed in {training_time:.1f}s, final accuracy: {accuracy:.2%}")
        
        return {'accuracy': accuracy, 'time': training_time, 'val_loss': best_val_loss}
    
    def train_transformer(self, df):
        logger.info("Training Transformer model with multi-head attention")
        
        X_train, X_val, y_train, y_val = self.prepare_data(df)
        
        self.transformer_model = TransformerModel(self.feature_dim).to(device)
        
        optimizer = optim.AdamW(self.transformer_model.parameters(), lr=0.0001, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=30)
        criterion = nn.BCELoss()
        
        batch_size = 256 if device.type != 'cpu' else 32
        epochs = 30
        
        logger.info(f"Training Transformer for {epochs} epochs")
        
        best_accuracy = 0
        
        for epoch in range(epochs):
            self.transformer_model.train()
            
            for i in range(0, len(X_train), batch_size):
                batch_X = torch.FloatTensor(X_train[i:i+batch_size]).to(device)
                batch_y = torch.FloatTensor(y_train[i:i+batch_size]).unsqueeze(1).to(device)
                
                optimizer.zero_grad()
                outputs = self.transformer_model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                
                torch.nn.utils.clip_grad_norm_(self.transformer_model.parameters(), 1.0)
                
                optimizer.step()
            
            scheduler.step()
            
            self.transformer_model.eval()
            correct = 0
            
            with torch.no_grad():
                for i in range(0, len(X_val), batch_size):
                    batch_X = torch.FloatTensor(X_val[i:i+batch_size]).to(device)
                    batch_y = torch.FloatTensor(y_val[i:i+batch_size]).unsqueeze(1).to(device)
                    
                    outputs = self.transformer_model(batch_X)
                    predicted = (outputs > 0.5).float()
                    correct += (predicted == batch_y).sum().item()
            
            accuracy = correct / len(X_val)
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
            
            if epoch % 10 == 0:
                logger.info(f"Transformer epoch {epoch}/{epochs}, Accuracy: {accuracy:.2%}")
        
        logger.info(f"Transformer training completed, best accuracy: {best_accuracy:.2%}")
        
        return {'accuracy': best_accuracy}
    
    def predict(self, hostname):
        if not self.lstm_model or not self.transformer_model:
            return {'error': 'Models not trained'}
        
        features = self.extract_features(hostname)
        features_scaled = self.scaler.transform([features])
        features_tensor = torch.FloatTensor(features_scaled).to(device)
        
        self.lstm_model.eval()
        self.transformer_model.eval()
        
        with torch.no_grad():
            lstm_score = self.lstm_model(features_tensor).cpu().item()
            transformer_score = self.transformer_model(features_tensor).cpu().item()
        
        return {
            'lstm_score': lstm_score,
            'transformer_score': transformer_score,
            'ensemble_score': (lstm_score + transformer_score) / 2
        }