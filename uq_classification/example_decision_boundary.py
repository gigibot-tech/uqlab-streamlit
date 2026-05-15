"""Example usage of decision boundary visualization module.

This demonstrates how to use the visualization functions with different
types of models and data.
"""

import numpy as np
import matplotlib.pyplot as plt

# Import visualization functions
from decision_boundary_viz import (
    plot_decision_boundary,
    visualize_checkpoint,
    visualize_checkpoints_batch,
    reduce_dimensions,
)


def example_2d_data():
    """Example with 2D data (no dimensionality reduction needed)."""
    print("=== 2D Data Example ===")
    
    # Generate synthetic 2D data
    np.random.seed(42)
    n_samples = 200
    
    # Class 0: centered at (-2, -2)
    X_class0 = np.random.randn(n_samples // 2, 2) + np.array([-2, -2])
    
    # Class 1: centered at (2, 2)
    X_class1 = np.random.randn(n_samples // 2, 2) + np.array([2, 2])
    
    X = np.vstack([X_class0, X_class1])
    y = np.hstack([np.zeros(n_samples // 2), np.ones(n_samples // 2)])
    
    # Train a simple model (using scikit-learn for simplicity)
    try:
        from sklearn.linear_model import LogisticRegression
        
        model = LogisticRegression()
        model.fit(X, y)
        
        # Visualize decision boundary
        fig = plot_decision_boundary(
            model, X, y,
            reduce_dims=False,  # Already 2D
            title="2D Data - Logistic Regression",
            resolution=150
        )
        plt.savefig('example_2d_boundary.png', dpi=150, bbox_inches='tight')
        print("Saved: example_2d_boundary.png")
        plt.close()
        
    except ImportError:
        print("Scikit-learn not available. Skipping this example.")


def example_high_dimensional_data():
    """Example with high-dimensional data using t-SNE."""
    print("\n=== High-Dimensional Data Example ===")
    
    # Generate synthetic high-dimensional data
    np.random.seed(42)
    n_samples = 300
    n_features = 50
    
    # Create 3 classes with different means
    X_class0 = np.random.randn(n_samples // 3, n_features) + 0
    X_class1 = np.random.randn(n_samples // 3, n_features) + 2
    X_class2 = np.random.randn(n_samples // 3, n_features) + 4
    
    X = np.vstack([X_class0, X_class1, X_class2])
    y = np.hstack([
        np.zeros(n_samples // 3),
        np.ones(n_samples // 3),
        np.full(n_samples // 3, 2)
    ])
    
    # Split into train/test
    split = int(0.8 * n_samples)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    try:
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        
        # Visualize with t-SNE reduction
        fig = plot_decision_boundary(
            model, X_train, y_train,
            X_test=X_test, y_test=y_test,
            reduce_dims=True,
            reduction_method='tsne',
            title="High-Dimensional Data - Random Forest (t-SNE)",
            figsize=(14, 6)
        )
        plt.savefig('example_highdim_tsne.png', dpi=150, bbox_inches='tight')
        print("Saved: example_highdim_tsne.png")
        plt.close()
        
    except ImportError:
        print("Scikit-learn not available. Skipping this example.")


def example_pytorch_model():
    """Example with PyTorch model and checkpoint."""
    print("\n=== PyTorch Model Example ===")
    
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        # Generate data
        np.random.seed(42)
        torch.manual_seed(42)
        
        n_samples = 400
        X_class0 = np.random.randn(n_samples // 2, 2) + np.array([-1.5, -1.5])
        X_class1 = np.random.randn(n_samples // 2, 2) + np.array([1.5, 1.5])
        
        X = np.vstack([X_class0, X_class1]).astype(np.float32)
        y = np.hstack([np.zeros(n_samples // 2), np.ones(n_samples // 2)]).astype(np.float32)
        
        # Define simple neural network
        class SimpleNN(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = nn.Linear(2, 10)
                self.fc2 = nn.Linear(10, 1)
                self.relu = nn.ReLU()
                self.sigmoid = nn.Sigmoid()
            
            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.sigmoid(self.fc2(x))
                return x
        
        # Train model
        model = SimpleNN()
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y).unsqueeze(1)
        
        print("Training PyTorch model...")
        for epoch in range(100):
            optimizer.zero_grad()
            outputs = model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 20 == 0:
                print(f"Epoch {epoch+1}/100, Loss: {loss.item():.4f}")
        
        # Save checkpoint
        checkpoint_path = 'example_model.pt'
        torch.save({
            'model_state_dict': model.state_dict(),
            'epoch': 100
        }, checkpoint_path)
        print(f"Saved checkpoint: {checkpoint_path}")
        
        # Visualize decision boundary
        fig = plot_decision_boundary(
            model, X, y,
            reduce_dims=False,
            title="PyTorch Neural Network",
            cmap='coolwarm'
        )
        plt.savefig('example_pytorch_boundary.png', dpi=150, bbox_inches='tight')
        print("Saved: example_pytorch_boundary.png")
        plt.close()
        
        # Visualize from checkpoint
        fig, save_path = visualize_checkpoint(
            checkpoint_path,
            X, y,
            model=SimpleNN(),  # Provide model architecture
            save_dir='.',
            title="PyTorch Model from Checkpoint"
        )
        print(f"Saved checkpoint visualization: {save_path}")
        plt.close()
        
    except ImportError:
        print("PyTorch not available. Skipping this example.")


def example_dimensionality_reduction():
    """Example showing dimensionality reduction separately."""
    print("\n=== Dimensionality Reduction Example ===")
    
    # Generate high-dimensional data
    np.random.seed(42)
    X = np.random.randn(200, 50)
    
    try:
        # Apply t-SNE
        X_tsne = reduce_dimensions(X, method='tsne', random_state=42)
        print(f"Original shape: {X.shape}")
        print(f"Reduced shape (t-SNE): {X_tsne.shape}")
        
        # Visualize
        plt.figure(figsize=(8, 6))
        plt.scatter(X_tsne[:, 0], X_tsne[:, 1], alpha=0.6)
        plt.xlabel('Component 1')
        plt.ylabel('Component 2')
        plt.title('t-SNE Dimensionality Reduction')
        plt.grid(True, alpha=0.3)
        plt.savefig('example_tsne_reduction.png', dpi=150, bbox_inches='tight')
        print("Saved: example_tsne_reduction.png")
        plt.close()
        
    except ImportError as e:
        print(f"Required library not available: {e}")


def example_batch_checkpoints():
    """Example of batch checkpoint visualization."""
    print("\n=== Batch Checkpoint Visualization Example ===")
    
    try:
        import torch
        import torch.nn as nn
        import os
        
        # Create checkpoint directory
        os.makedirs('example_checkpoints', exist_ok=True)
        
        # Generate data
        np.random.seed(42)
        X = np.random.randn(200, 2)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        
        # Simple model
        class TinyModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc = nn.Linear(2, 1)
                self.sigmoid = nn.Sigmoid()
            
            def forward(self, x):
                return self.sigmoid(self.fc(x))
        
        # Train and save multiple checkpoints
        model = TinyModel()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
        criterion = nn.BCELoss()
        
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y).unsqueeze(1)
        
        checkpoint_paths = []
        for epoch in [10, 20, 30]:
            # Train for a few steps
            for _ in range(epoch):
                optimizer.zero_grad()
                outputs = model(X_tensor)
                loss = criterion(outputs, y_tensor)
                loss.backward()
                optimizer.step()
            
            # Save checkpoint
            checkpoint_path = f'example_checkpoints/model_epoch_{epoch}.pt'
            torch.save(model.state_dict(), checkpoint_path)
            checkpoint_paths.append(checkpoint_path)
            print(f"Saved: {checkpoint_path}")
        
        # Batch visualize all checkpoints
        image_paths = visualize_checkpoints_batch(
            'example_checkpoints/',
            X, y,
            model=TinyModel(),
            save_dir='example_visualizations',
            pattern='*.pt'
        )
        
        print(f"\nGenerated {len(image_paths)} visualizations:")
        for path in image_paths:
            print(f"  - {path}")
        
    except ImportError:
        print("PyTorch not available. Skipping this example.")


if __name__ == "__main__":
    print("Decision Boundary Visualization Examples\n")
    print("=" * 50)
    
    # Run examples
    example_2d_data()
    example_high_dimensional_data()
    example_pytorch_model()
    example_dimensionality_reduction()
    example_batch_checkpoints()
    
    print("\n" + "=" * 50)
    print("All examples completed!")
    print("\nGenerated files:")
    print("  - example_2d_boundary.png")
    print("  - example_highdim_tsne.png")
    print("  - example_pytorch_boundary.png")
    print("  - example_tsne_reduction.png")
    print("  - example_checkpoints/ (directory)")
    print("  - example_visualizations/ (directory)")

# Made with Bob