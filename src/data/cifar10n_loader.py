"""
CIFAR-10N Data Loader
Provides CIFAR-10 with noisy labels for noise filtering experiments.

CIFAR-10N is a dataset with human-annotated noisy labels.
Reference: https://github.com/UCSC-REAL/cifar-10-100n
"""

import torch
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Dataset
import os
import pickle


class CIFAR10NDataset(Dataset):
    """
    CIFAR-10 with noisy labels.
    
    This dataset wraps CIFAR-10 and provides access to both clean and noisy labels.
    """
    
    def __init__(self, root='./data/cifar10', noise_type='worse_label', 
                 train=True, transform=None, download=True):
        """
        Initialize CIFAR-10N dataset.
        
        Args:
            root: Root directory for CIFAR-10 data
            noise_type: Type of noise ('worse_label', 'aggre_label', 'random_label1', etc.)
            train: Whether to use training set
            transform: Transforms to apply
            download: Whether to download CIFAR-10 if not present
        """
        self.root = root
        self.noise_type = noise_type
        self.train = train
        self.transform = transform
        
        # Load base CIFAR-10 dataset
        self.cifar10 = datasets.CIFAR10(
            root=root,
            train=train,
            download=download,
            transform=None  # We'll apply transform in __getitem__
        )
        
        # Load noisy labels if available
        self.noisy_labels = None
        self.noise_mask = None
        self.noise_rate = 0.0
        
        if train:
            self._load_noisy_labels()
    
    def _load_noisy_labels(self):
        """Load noisy labels from CIFAR-10N dataset."""
        noise_file = os.path.join(self.root, 'cifar-10-batches-py', f'CIFAR-10_human.pt')
        
        if not os.path.exists(noise_file):
            print(f"Warning: CIFAR-10N noise file not found at {noise_file}")
            print("Using clean labels. To use noisy labels, download CIFAR-10N from:")
            print("https://github.com/UCSC-REAL/cifar-10-100n")
            return
        
        try:
            # Load noise data
            # CIFAR-10N stores numpy-backed objects inside the .pt file.
            # On PyTorch >= 2.6 we must disable `weights_only` for trusted data files.
            noise_data = torch.load(noise_file, map_location='cpu', weights_only=False)
            
            # Get noisy labels for specified noise type
            if self.noise_type in noise_data:
                self.noisy_labels = np.array(noise_data[self.noise_type])
                
                # Calculate noise mask (where noisy != clean)
                clean_labels = np.array(self.cifar10.targets)
                self.noise_mask = (self.noisy_labels != clean_labels)
                self.noise_rate = self.noise_mask.mean()
                
                print(f"Loaded CIFAR-10N with {self.noise_type}: {self.noise_rate*100:.2f}% noise")
            else:
                print(f"Warning: Noise type '{self.noise_type}' not found in CIFAR-10N data")
                print(f"Available types: {list(noise_data.keys())}")
        except Exception as e:
            print(f"Error loading CIFAR-10N: {e}")
    
    def __len__(self):
        return len(self.cifar10)
    
    def __getitem__(self, index):
        """
        Get item with both clean and noisy labels.
        
        Returns:
            image: Transformed image
            noisy_label: Noisy label (or clean if noise not available)
            clean_label: Clean label
            is_noisy: Boolean indicating if label is noisy
        """
        image, clean_label = self.cifar10[index]
        
        if self.transform is not None:
            image = self.transform(image)
        
        # Use noisy label if available, otherwise use clean
        if self.noisy_labels is not None and self.noise_mask is not None:
            noisy_label = int(self.noisy_labels[index])
            is_noisy = bool(self.noise_mask[index])
        else:
            noisy_label = clean_label
            is_noisy = False
        
        return image, noisy_label, clean_label, is_noisy
    
    def get_noisy_samples(self):
        """Get indices of noisy samples."""
        if self.noise_mask is not None:
            return np.where(self.noise_mask)[0]
        return np.array([])
    
    def get_clean_samples(self):
        """Get indices of clean samples."""
        if self.noise_mask is not None:
            return np.where(~self.noise_mask)[0]
        return np.arange(len(self))


class CIFAR10NLabelView(Dataset):
    """
    Wrapper to present CIFAR10NDataset as (image, label) for compatibility.
    """
    
    def __init__(self, cifar10n_dataset, label_mode='noisy'):
        """
        Args:
            cifar10n_dataset: CIFAR10NDataset instance
            label_mode: 'noisy' or 'clean' - which label to return
        """
        self.dataset = cifar10n_dataset
        self.label_mode = label_mode
    
    def __len__(self):
        return len(self.dataset)
    
    def __getitem__(self, index):
        image, noisy_label, clean_label, is_noisy = self.dataset[index]
        label = noisy_label if self.label_mode == 'noisy' else clean_label
        return image, label


class CIFAR10NLoader:
    """Convenience wrapper for CIFAR-10N data loading."""
    
    def __init__(self, root='./data/cifar10', noise_type='worse_label', download=True):
        """
        Initialize CIFAR-10N loader.
        
        Args:
            root: Root directory for dataset
            noise_type: Type of noise to use
            download: Whether to download CIFAR-10 if not present
        """
        self.root = root
        self.noise_type = noise_type
        self.download = download
    
    def get_train_transform(self, augment=True):
        """Get training transforms."""
        if augment:
            return transforms.Compose([
                transforms.RandomCrop(32, padding=4),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.4914, 0.4822, 0.4465), 
                                   (0.2023, 0.1994, 0.2010))
            ])
        else:
            return transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize((0.4914, 0.4822, 0.4465), 
                                   (0.2023, 0.1994, 0.2010))
            ])
    
    def get_test_transform(self):
        """Get test transforms."""
        return transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), 
                               (0.2023, 0.1994, 0.2010))
        ])
    
    def get_train_loader(self, batch_size=128, augment=True, num_workers=4, shuffle=True):
        """
        Get training data loader with noisy labels.
        
        Returns:
            loader: DataLoader
            dataset: CIFAR10NDataset (for accessing noise info)
        """
        transform = self.get_train_transform(augment)
        train_dataset = CIFAR10NDataset(
            root=self.root,
            noise_type=self.noise_type,
            train=True,
            transform=transform,
            download=self.download
        )
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            pin_memory=True
        )
        
        return train_loader, train_dataset
    
    def get_test_loader(self, batch_size=128, num_workers=4):
        """Get test data loader (clean labels)."""
        transform = self.get_test_transform()
        test_dataset = CIFAR10NDataset(
            root=self.root,
            noise_type=self.noise_type,
            train=False,
            transform=transform,
            download=self.download
        )
        
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True
        )
        
        return test_loader, test_dataset




def get_cifar10n_loaders(root='./data/cifar10', noise_type='worse_label', 
                         batch_size=128, download=True, num_workers=4):
    """
    Convenience function to get both train and test loaders.
    
    Args:
        root: Root directory for dataset
        noise_type: Type of noise to use
        batch_size: Batch size
        download: Whether to download if not present
        num_workers: Number of data loading workers
        
    Returns:
        train_loader, train_dataset, test_loader, test_dataset
    """
    loader = CIFAR10NLoader(root=root, noise_type=noise_type, download=download)
    train_loader, train_dataset = loader.get_train_loader(
        batch_size=batch_size, num_workers=num_workers
    )
    test_loader, test_dataset = loader.get_test_loader(
        batch_size=batch_size, num_workers=num_workers
    )
    return train_loader, train_dataset, test_loader, test_dataset

# Made with Bob
