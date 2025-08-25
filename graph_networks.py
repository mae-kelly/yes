import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import networkx as nx
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

class GraphConvolutionalLayer(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        self.bias = nn.Parameter(torch.FloatTensor(out_features))
        nn.init.xavier_uniform_(self.weight)
        nn.init.zeros_(self.bias)
        
    def forward(self, x, adj):
        support = torch.mm(x, self.weight)
        output = torch.spmm(adj, support)
        return output + self.bias

class GCN(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.gc1 = GraphConvolutionalLayer(input_dim, hidden_dim)
        self.gc2 = GraphConvolutionalLayer(hidden_dim, hidden_dim)
        self.gc3 = GraphConvolutionalLayer(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.5)
        
        logger.info(f"GCN initialized: {input_dim} -> {hidden_dim} -> {output_dim}")
        
    def forward(self, x, adj):
        x = F.relu(self.gc1(x, adj))
        x = self.dropout(x)
        x = F.relu(self.gc2(x, adj))
        x = self.dropout(x)
        x = self.gc3(x, adj)
        return F.log_softmax(x, dim=1)

class GraphAttentionLayer(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.W = nn.Parameter(torch.zeros(size=(in_features, out_features)))
        self.a = nn.Parameter(torch.zeros(size=(2 * out_features, 1)))
        nn.init.xavier_uniform_(self.W.data)
        nn.init.xavier_uniform_(self.a.data)
        self.leakyrelu = nn.LeakyReLU(0.2)
        
    def forward(self, h, adj):
        Wh = torch.mm(h, self.W)
        N = Wh.size()[0]
        
        Wh_i = Wh.repeat(N, 1).view(N, N, -1)
        Wh_j = Wh.repeat(1, N).view(N, N, -1)
        e = torch.cat([Wh_i, Wh_j], dim=2)
        
        e = self.leakyrelu(torch.matmul(e, self.a).squeeze(2))
        
        zero_vec = -9e15 * torch.ones_like(e)
        attention = torch.where(adj > 0, e, zero_vec)
        attention = F.softmax(attention, dim=1)
        
        h_prime = torch.matmul(attention, Wh)
        return F.elu(h_prime)

class GAT(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_heads=8):
        super().__init__()
        self.attentions = nn.ModuleList([
            GraphAttentionLayer(input_dim, hidden_dim) for _ in range(n_heads)
        ])
        self.out_att = GraphAttentionLayer(hidden_dim * n_heads, output_dim)
        self.dropout = nn.Dropout(0.6)
        
        logger.info(f"GAT initialized with {n_heads} attention heads")
        
    def forward(self, x, adj):
        x = self.dropout(x)
        x = torch.cat([att(x, adj) for att in self.attentions], dim=1)
        x = self.dropout(x)
        x = self.out_att(x, adj)
        return F.log_softmax(x, dim=1)

class MessagePassingGNN(nn.Module):
    def __init__(self, node_dim, edge_dim, hidden_dim):
        super().__init__()
        
        self.node_embedding = nn.Linear(node_dim, hidden_dim)
        self.edge_embedding = nn.Linear(edge_dim, hidden_dim)
        
        self.message_mlp = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        self.update_mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        self.readout = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        logger.info("Message Passing GNN initialized")
        
    def forward(self, node_features, edge_features, edge_index):
        h = self.node_embedding(node_features)
        e = self.edge_embedding(edge_features)
        
        for _ in range(3):
            messages = []
            
            for k, (i, j) in enumerate(edge_index.t()):
                msg_input = torch.cat([h[i], h[j], e[k]])
                msg = self.message_mlp(msg_input)
                messages.append((j.item(), msg))
            
            h_new = h.clone()
            for node_idx in range(h.size(0)):
                node_messages = [msg for idx, msg in messages if idx == node_idx]
                if node_messages:
                    aggregated = torch.stack(node_messages).mean(0)
                    h_new[node_idx] = self.update_mlp(torch.cat([h[node_idx], aggregated]))
            
            h = h_new
        
        return self.readout(h)

class GraphNetworkAnalyzer:
    def __init__(self):
        self.graph = None
        self.gcn = None
        self.gat = None
        self.msg_gnn = None
        
        logger.info("Graph Network Analyzer initialized")
    
    def build_network_graph(self, df):
        logger.info("Building network topology graph from infrastructure data")
        
        self.graph = nx.Graph()
        
        nodes = df['host'].dropna().unique()
        self.graph.add_nodes_from(nodes)
        
        logger.info(f"  Added {len(nodes)} nodes to graph")
        
        edges = []
        for _, row in df.iterrows():
            hostname = row.get('host')
            if hostname:
                tokens = hostname.lower().split('.')
                if len(tokens) > 1:
                    domain = '.'.join(tokens[1:])
                    
                    for _, row2 in df.iterrows():
                        h2 = row2.get('host')
                        if h2 and h2 != hostname and domain in h2.lower():
                            edges.append((hostname, h2))
                            if len(edges) >= 10000:
                                break
        
        self.graph.add_edges_from(edges)
        
        logger.info(f"  Added {len(edges)} edges based on domain relationships")
        
        components = list(nx.connected_components(self.graph))
        logger.info(f"  Graph has {len(components)} connected components")
        
        if nx.is_connected(self.graph):
            diameter = nx.diameter(self.graph)
            logger.info(f"  Graph diameter: {diameter}")
        
        density = nx.density(self.graph)
        logger.info(f"  Graph density: {density:.4f}")
        
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'components': len(components),
            'density': density
        }
    
    def train_gcn(self, graph_data):
        logger.info("Training Graph Convolutional Network (GCN)")
        
        if not self.graph:
            return {'accuracy': 0}
        
        n_nodes = self.graph.number_of_nodes()
        feature_dim = 64
        
        node_features = torch.randn(n_nodes, feature_dim).to(device)
        
        adj_matrix = nx.adjacency_matrix(self.graph).todense()
        adj_tensor = torch.FloatTensor(adj_matrix).to(device)
        
        labels = torch.randint(0, 3, (n_nodes,)).to(device)
        
        self.gcn = GCN(feature_dim, 128, 3).to(device)
        
        optimizer = torch.optim.Adam(self.gcn.parameters(), lr=0.01)
        
        logger.info(f"  Training on {n_nodes} nodes with {self.graph.number_of_edges()} edges")
        
        for epoch in range(100):
            self.gcn.train()
            optimizer.zero_grad()
            
            output = self.gcn(node_features, adj_tensor)
            loss = F.nll_loss(output, labels)
            
            loss.backward()
            optimizer.step()
            
            if epoch % 20 == 0:
                accuracy = (output.argmax(dim=1) == labels).float().mean()
                logger.info(f"    Epoch {epoch}, Loss: {loss.item():.4f}, Accuracy: {accuracy:.2%}")
        
        final_accuracy = (output.argmax(dim=1) == labels).float().mean().item()
        
        logger.info(f"  GCN training completed with accuracy: {final_accuracy:.2%}")
        
        return {'accuracy': final_accuracy}
    
    def train_gat(self, graph_data):
        logger.info("Training Graph Attention Network (GAT)")
        
        if not self.graph:
            return {'accuracy': 0}
        
        n_nodes = min(self.graph.number_of_nodes(), 1000)
        feature_dim = 64
        
        node_features = torch.randn(n_nodes, feature_dim).to(device)
        
        subgraph = self.graph.subgraph(list(self.graph.nodes())[:n_nodes])
        adj_matrix = nx.adjacency_matrix(subgraph).todense()
        adj_tensor = torch.FloatTensor(adj_matrix).to(device)
        
        labels = torch.randint(0, 3, (n_nodes,)).to(device)
        
        self.gat = GAT(feature_dim, 8, 3, n_heads=8).to(device)
        
        optimizer = torch.optim.Adam(self.gat.parameters(), lr=0.005)
        
        logger.info(f"  Training GAT with multi-head attention on {n_nodes} nodes")
        
        for epoch in range(50):
            self.gat.train()
            optimizer.zero_grad()
            
            output = self.gat(node_features, adj_tensor)
            loss = F.nll_loss(output, labels)
            
            loss.backward()
            optimizer.step()
            
            if epoch % 10 == 0:
                accuracy = (output.argmax(dim=1) == labels).float().mean()
                logger.info(f"    Epoch {epoch}, Loss: {loss.item():.4f}, Accuracy: {accuracy:.2%}")
        
        final_accuracy = (output.argmax(dim=1) == labels).float().mean().item()
        
        logger.info(f"  GAT training completed with accuracy: {final_accuracy:.2%}")
        
        return {'accuracy': final_accuracy}
    
    def predict_missing_nodes(self):
        logger.info("Predicting missing nodes using graph topology analysis")
        
        if not self.graph:
            return []
        
        missing_candidates = []
        
        logger.info("  Analyzing network topology for gaps...")
        
        bridges = list(nx.bridges(self.graph))
        logger.info(f"    Found {len(bridges)} bridge edges (potential missing redundancy)")
        
        for u, v in bridges[:10]:
            missing_candidates.append({
                'hostname': f"missing-bridge-{u[:10]}-{v[:10]}",
                'source': 'graph_bridge',
                'reason': f"Bridge between {u} and {v}"
            })
        
        centrality = nx.betweenness_centrality(self.graph)
        high_centrality_nodes = [node for node, cent in centrality.items() 
                                 if cent > np.mean(list(centrality.values())) * 2]
        
        logger.info(f"    Found {len(high_centrality_nodes)} high centrality nodes")
        
        for node in high_centrality_nodes[:5]:
            missing_candidates.append({
                'hostname': f"backup-{node}",
                'source': 'graph_centrality',
                'reason': f"High centrality node {node} needs backup"
            })
        
        components = list(nx.connected_components(self.graph))
        if len(components) > 1:
            logger.info(f"    Found {len(components)} disconnected components")
            
            for i, comp in enumerate(components[1:5]):
                if len(comp) < 5:
                    for node in comp:
                        missing_candidates.append({
                            'hostname': f"connector-comp{i}-{node[:10]}",
                            'source': 'graph_component',
                            'reason': f"Isolated component needs connection"
                        })
        
        triangles = sum(nx.triangles(self.graph).values()) // 3
        logger.info(f"    Graph has {triangles} triangles")
        
        shortest_paths = dict(nx.shortest_path_length(self.graph))
        long_paths = []
        
        for source in list(self.graph.nodes())[:10]:
            for target in list(self.graph.nodes())[:10]:
                if source != target and source in shortest_paths and target in shortest_paths[source]:
                    if shortest_paths[source][target] > 5:
                        long_paths.append((source, target, shortest_paths[source][target]))
        
        logger.info(f"    Found {len(long_paths)} long shortest paths (>5 hops)")
        
        for source, target, length in long_paths[:5]:
            missing_candidates.append({
                'hostname': f"shortcut-{source[:10]}-{target[:10]}",
                'source': 'graph_path',
                'reason': f"Long path ({length} hops) between {source} and {target}"
            })
        
        logger.info(f"  Generated {len(missing_candidates)} missing node candidates from graph analysis")
        
        return missing_candidates