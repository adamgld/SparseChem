# Copyright (c) 2020 KU Leuven
from torch.utils.data import Dataset
import torch
import scipy.sparse
import numpy as np

class SparseDataset(Dataset):
    def __init__(self, x, y):
        '''
        Args:
            X (sparse matrix):  input [n_sampes, features_in]
            Y (sparse matrix):  output [n_samples, features_out]
            task_weights (vec): task weights [features_out]
        '''
        assert x.shape[0]==y.shape[0], f"Input has {x.shape[0]} rows, output has {y.shape[0]} rows."

        self.x = x.tocsr(copy=False).astype(np.float32)
        self.y = y.tocsr(copy=False).astype(np.float32)
        # scale labels from {-1, -1} to {0, 1}, zeros are stored explicitly
        self.y.data = (self.y.data + 1) / 2.0

    def __len__(self):
        return(self.x.shape[0])

    @property
    def input_size(self):
        return self.x.shape[1]

    @property
    def output_size(self):
        return self.y.shape[1]

    def __getitem__(self, idx):
        x_start = self.x.indptr[idx]
        x_end = self.x.indptr[idx + 1]
        x_indices = self.x.indices[x_start:x_end]
        x_data = self.x.data[x_start:x_end]

        y_start = self.y.indptr[idx]
        y_end = self.y.indptr[idx + 1]
        y_indices = self.y.indices[y_start:y_end]
        y_data = self.y.data[y_start:y_end]

        return {
            "x_ind":  x_indices,
            "x_data": x_data,
            "y_ind":  y_indices,
            "y_data": y_data,
        }

    def batch_to_x(self, batch, dev):
        """Takes 'xind' and 'x_data' from batch and converts them into a sparse tensor.
        Args:
            batch  batch
            dev    device to send the tensor to
        """
        return torch.sparse_coo_tensor(
                batch["x_ind"].to(dev),
                batch["x_data"].to(dev),
                size=[batch["batch_size"], self.x.shape[1]])


class MappingDataset(Dataset):
    def __init__(self, x_ind, x_data, y, mapping=None):
        """
        Dataset that creates a mapping for features of x (0...N_feat-1).
        """
        ## TODO: need to implement Dataset with custom mapping
        pass

def sparse_collate(batch):
    x_ind  = [b["x_ind"]  for b in batch]
    x_data = [b["x_data"] for b in batch]
    y_ind  = [b["y_ind"]  for b in batch]
    y_data = [b["y_data"] for b in batch]

    ## x matrix
    xrow = np.repeat(np.arange(len(x_ind)), [len(i) for i in x_ind])
    xcol = np.concatenate(x_ind)
    xv   = np.concatenate(x_data)

    ## y matrix
    yrow  = np.repeat(np.arange(len(y_ind)), [len(i) for i in y_ind])
    ycol  = np.concatenate(y_ind).astype(np.int64)

    return {
        "x_ind":  torch.LongTensor([xrow, xcol]),
        "x_data": torch.from_numpy(xv),
        "y_ind":  torch.stack([torch.from_numpy(yrow), torch.from_numpy(ycol)], dim=0),
        "y_data": torch.from_numpy(np.concatenate(y_data)),
        "batch_size": len(batch),
    }

