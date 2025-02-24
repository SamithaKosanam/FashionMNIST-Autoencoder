#!/usr/bin/env python
# coding: utf-8

from utils import mnist_reader
import torch
import torch.nn as nn
import numpy as np

X_train, y_train = mnist_reader.load_mnist('data/fashion', kind='train')
X_test, y_test = mnist_reader.load_mnist('data/fashion', kind='t10k')
print(X_train.shape)
print(y_train.shape)
print(X_test.shape)
print(y_test.shape)
X_train = np.float32(X_train)
x_std = np.std(X_train)
x_mean = np.mean(X_train)

class Autoencoder(nn.Module):
    def __init__(self, input_dim = 784, latent = 8):
        super().__init__()
        
        self.enc1 = nn.Linear(in_features=input_dim, out_features=input_dim//2)
        self.enc2 = nn.Linear(in_features=input_dim//2, out_features=input_dim//4)
        self.enc3 = nn.Linear(in_features=input_dim//4, out_features=latent)
        
        self.dec1 = nn.Linear(in_features=latent, out_features=input_dim//4)
        self.dec2 = nn.Linear(in_features=input_dim//4, out_features=input_dim//2)
        self.dec3 = nn.Linear(in_features=input_dim//2, out_features=input_dim)
    
    def encode(self, x):
        x = self.enc1(x)
        x = nn.LeakyReLU(0.5)(x)
        x = self.enc2(x)
        x = nn.LeakyReLU(0.5)(x)
        x = self.enc3(x)
        x = nn.LeakyReLU(0.5)(x)
        return x
    
    def decode(self, x):        
        x = self.dec1(x)
        x = nn.LeakyReLU(0.5)(x)
        x = self.dec2(x)
        x = nn.LeakyReLU(0.5)(x)
        x = self.dec3(x)
        return x

    def forward(self, x):
        latent = self.encode(x)
        recon = self.decode(latent)
        return recon

def shuffle_data(data):
    size = data.shape[0]
    index = torch.randperm(size)
    new_data = data[index]
    return new_data

def training(model, dataset,optimizer, criterion, latent_dim,  Epochs, batch_size = 1000, device = "cpu"):

    train_loss = []
    best_loss = 1e10
    dataset = shuffle_data(dataset)

    data_size  = dataset.shape[0]
    batches = data_size//batch_size

    for epoch in range(Epochs):
        running_loss = 0.0

        for i in range(batches):
            start = i*batch_size
            end = min(data_size, start+batch_size)

            data = dataset[start:end]   

            optimizer.zero_grad()
            # print(data)
            outputs = model(data)
            loss = criterion(outputs, data)
            # print(loss)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        loss = running_loss / batches

        train_loss.append(loss)

        if epoch % 20 == 0:
            print('Epoch {} of {}, Train Loss: {:.6f}'.format(epoch+1, Epochs, running_loss))

        if (loss < best_loss) and (epoch % 20 == 0):
            torch.save(model.state_dict(), './results/latent_{}_best_parameters.pt'.format(latent_dim))
            #torch.save(model.state_dict(), './results/AE/v2_{}/model/AE_loge_allplanes_latent{}_best_parameters.pt'.format(timestep, latent_dim))
            best_loss = loss
            print('best loss: ', best_loss)
            
    print('final best loss: ', best_loss)

    return train_loss

latent_dim = 8
model = Autoencoder(latent=latent_dim)
model_param = model.parameters()
optimizer = torch.optim.Adam(filter(lambda x: x.requires_grad, model_param), lr=0.0001)
criterion = nn.MSELoss()
dataset = torch.from_numpy(X_train)
dataset_norm = (dataset-torch.mean(dataset))/torch.std(dataset)

training(model, dataset_norm, optimizer, criterion, latent_dim=latent_dim,  Epochs=1000, batch_size = 1024)

with torch.no_grad():
    result = model(dataset)
    result = result.detach().cpu().numpy() * x_std +x_mean

import matplotlib.pyplot as plt
plt.imshow(result[0].reshape([28, 28]))

