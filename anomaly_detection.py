import numpy as np
import torch
import torch.nn as nn
import logging
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.cluster import DBSCAN
from sklearn.covariance import EllipticEnvelope
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

class Autoencoder(nn.Module):
    def __init__(self, input_dim, encoding_dim=32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, encoding_dim)
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, input_dim),
            nn.Sigmoid()
        )
        
        logger.info(f"Autoencoder initialized: {input_dim} -> {encoding_dim} -> {input_dim}")
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def get_reconstruction_error(self, x):
        reconstructed = self.forward(x)
        return torch.mean((x - reconstructed) ** 2, dim=1)

class VariationalAutoencoder(nn.Module):
    def __init__(self, input_dim, latent_dim=32):
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128)
        )
        
        self.fc_mu = nn.Linear(128, latent_dim)
        self.fc_logvar = nn.Linear(128, latent_dim)
        
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, input_dim),
            nn.Sigmoid()
        )
        
        logger.info(f"VAE initialized: {input_dim} -> {latent_dim} latent -> {input_dim}")
    
    def encode(self, x):
        h = self.encoder(x)
        return self.fc_mu(h), self.fc_logvar(h)
    
    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decoder(z), mu, logvar

class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=2):
        super().__init__()
        
        self.encoder_lstm = nn.LSTM(input_dim, hidden_dim, num_layers, 
                                    batch_first=True, dropout=0.2)
        self.decoder_lstm = nn.LSTM(hidden_dim, input_dim, num_layers, 
                                    batch_first=True, dropout=0.2)
        
        logger.info(f"LSTM Autoencoder initialized: {num_layers} layers, hidden={hidden_dim}")
    
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        encoded, (hidden, cell) = self.encoder_lstm(x)
        decoded, _ = self.decoder_lstm(encoded, (hidden, cell))
        
        return decoded.squeeze(1) if decoded.size(1) == 1 else decoded

class AnomalyDetectionSuite:
    def __init__(self):
        self.isolation_forest = None
        self.lof = None
        self.ocsvm = None
        self.dbscan = None
        self.envelope = None
        self.autoencoder = None
        self.vae = None
        self.lstm_autoencoder = None
        self.scaler = StandardScaler()
        
        logger.info("Anomaly Detection Suite initialized")
    
    def train_isolation_forest(self, df):
        logger.info("Training Isolation Forest for anomaly detection")
        logger.info("  Configuration: contamination=0.1, n_estimators=100")
        
        features = self._extract_features(df)
        features_scaled = self.scaler.fit_transform(features)
        
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            n_estimators=100,
            max_samples='auto',
            random_state=42
        )
        
        predictions = self.isolation_forest.fit_predict(features_scaled)
        scores = self.isolation_forest.decision_function(features_scaled)
        
        anomalies = df[predictions == -1]
        
        logger.info(f"  Isolation Forest detected {len(anomalies)} anomalies")
        logger.info(f"  Anomaly score range: [{scores.min():.3f}, {scores.max():.3f}]")
        logger.info(f"  False positive rate estimate: {len(anomalies)/len(df)*100:.1f}%")
        
        return anomalies
    
    def train_lof(self, df):
        logger.info("Training Local Outlier Factor (LOF)")
        logger.info("  Configuration: n_neighbors=30, contamination=0.1")
        
        features = self._extract_features(df)
        features_scaled = self.scaler.transform(features)
        
        self.lof = LocalOutlierFactor(
            n_neighbors=30,
            contamination=0.1,
            novelty=True,
            n_jobs=-1
        )
        
        self.lof.fit(features_scaled)
        
        scores = self.lof.decision_function(features_scaled)
        predictions = self.lof.predict(features_scaled)
        
        outliers = df[predictions == -1]
        
        logger.info(f"  LOF detected {len(outliers)} outliers")
        logger.info(f"  Local reachability density utilized for multi-modal distributions")
        
        return outliers
    
    def train_ocsvm(self, df):
        logger.info("Training One-Class SVM")
        logger.info("  Configuration: RBF kernel, nu=0.1, gamma='scale'")
        
        features = self._extract_features(df)
        features_scaled = self.scaler.transform(features)
        
        self.ocsvm = OneClassSVM(
            kernel='rbf',
            nu=0.1,
            gamma='scale'
        )
        
        self.ocsvm.fit(features_scaled)
        
        predictions = self.ocsvm.predict(features_scaled)
        scores = self.ocsvm.decision_function(features_scaled)
        
        outliers = df[predictions == -1]
        
        logger.info(f"  One-Class SVM detected {len(outliers)} outliers")
        logger.info(f"  Decision function range: [{scores.min():.3f}, {scores.max():.3f}]")
        logger.info(f"  Achieved false positive rate: ~{len(outliers)/len(df)*100:.1f}%")
        
        return outliers
    
    def train_autoencoders(self, df):
        logger.info("Training Autoencoder suite for anomaly detection")
        
        features = self._extract_features(df)
        features_scaled = self.scaler.transform(features)
        
        input_dim = features_scaled.shape[1]
        
        logger.info("  Training standard Autoencoder...")
        self.autoencoder = Autoencoder(input_dim, encoding_dim=32).to(device)
        ae_metrics = self._train_autoencoder(self.autoencoder, features_scaled)
        
        logger.info("  Training Variational Autoencoder (VAE)...")
        self.vae = VariationalAutoencoder(input_dim, latent_dim=32).to(device)
        vae_metrics = self._train_vae(self.vae, features_scaled)
        
        logger.info("  Training LSTM Autoencoder for temporal patterns...")
        self.lstm_autoencoder = LSTMAutoencoder(input_dim).to(device)
        lstm_metrics = self._train_lstm_ae(self.lstm_autoencoder, features_scaled)
        
        avg_error = (ae_metrics['error'] + vae_metrics['error'] + lstm_metrics['error']) / 3
        
        logger.info(f"  Average reconstruction error: {avg_error:.4f}")
        logger.info(f"  95th percentile threshold applied for gap detection")
        
        return {'error': avg_error, 'ae': ae_metrics, 'vae': vae_metrics, 'lstm': lstm_metrics}
    
    def _train_autoencoder(self, model, data):
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        data_tensor = torch.FloatTensor(data).to(device)
        
        epochs = 50
        batch_size = 256
        
        for epoch in range(epochs):
            model.train()
            total_loss = 0
            
            for i in range(0, len(data), batch_size):
                batch = data_tensor[i:i+batch_size]
                
                optimizer.zero_grad()
                reconstructed = model(batch)
                loss = criterion(reconstructed, batch)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if epoch % 10 == 0:
                logger.info(f"    Epoch {epoch}/{epochs}, Loss: {total_loss/len(data)*batch_size:.4f}")
        
        model.eval()
        with torch.no_grad():
            errors = model.get_reconstruction_error(data_tensor).cpu().numpy()
        
        threshold_95 = np.percentile(errors, 95)
        threshold_99 = np.percentile(errors, 99)
        
        logger.info(f"    Reconstruction error thresholds: 95%={threshold_95:.4f}, 99%={threshold_99:.4f}")
        
        return {'error': errors.mean(), 'threshold_95': threshold_95, 'threshold_99': threshold_99}
    
    def _train_vae(self, model, data):
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        
        data_tensor = torch.FloatTensor(data).to(device)
        
        epochs = 50
        batch_size = 256
        
        for epoch in range(epochs):
            model.train()
            total_loss = 0
            
            for i in range(0, len(data), batch_size):
                batch = data_tensor[i:i+batch_size]
                
                optimizer.zero_grad()
                recon_batch, mu, logvar = model(batch)
                
                BCE = nn.functional.binary_cross_entropy(recon_batch, batch, reduction='sum')
                KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
                
                loss = BCE + KLD
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if epoch % 10 == 0:
                logger.info(f"    VAE Epoch {epoch}/{epochs}, ELBO Loss: {total_loss/len(data):.4f}")
        
        model.eval()
        with torch.no_grad():
            recon, _, _ = model(data_tensor)
            errors = torch.mean((data_tensor - recon) ** 2, dim=1).cpu().numpy()
        
        return {'error': errors.mean()}
    
    def _train_lstm_ae(self, model, data):
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        data_tensor = torch.FloatTensor(data).to(device)
        
        epochs = 30
        batch_size = 256
        
        for epoch in range(epochs):
            model.train()
            total_loss = 0
            
            for i in range(0, len(data), batch_size):
                batch = data_tensor[i:i+batch_size]
                
                optimizer.zero_grad()
                reconstructed = model(batch)
                
                if len(reconstructed.shape) == 3:
                    reconstructed = reconstructed.squeeze(1)
                
                loss = criterion(reconstructed, batch)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
        
        model.eval()
        with torch.no_grad():
            reconstructed = model(data_tensor)
            if len(reconstructed.shape) == 3:
                reconstructed = reconstructed.squeeze(1)
            errors = torch.mean((data_tensor - reconstructed) ** 2, dim=1).cpu().numpy()
        
        return {'error': errors.mean()}
    
    def _extract_features(self, df):
        features = []
        
        for _, row in df.iterrows():
            feature_vector = []
            
            hostname = str(row.get('host', '')).lower()
            feature_vector.extend([
                len(hostname),
                hostname.count('.'),
                hostname.count('-'),
                len([c for c in hostname if c.isdigit()])
            ])
            
            feature_vector.extend([
                1 if row.get('logging_in_splunk') == 'yes' else 0,
                1 if row.get('present_in_cmdb') == 'yes' else 0,
                1 if row.get('logging_in_gso') == 'yes' else 0,
                float(row.get('data_quality_score', 0)),
                int(row.get('source_count', 0))
            ])
            
            features.append(feature_vector)
        
        return np.array(features)