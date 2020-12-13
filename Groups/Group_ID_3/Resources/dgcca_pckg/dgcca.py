# -*- coding: utf-8 -*-
"""DGCCA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15L_7jxf0KH81UjAO6waIbQso1nqML0kD

# Deep Generalized Cannonical Correlation Analysis Implementaion for 3 views

cca-zoo package is used for the implemntaion of gcca (Generalized Cannonical Correlation Analysis)
"""

#install the cca-zoo package
#pip install cca-zoo

#importing required libraries
import torch
import cca_zoo
import torch.nn as nn
import torch.optim as optim 
import GCCA_loss #to be implemented

"""#  Class DNN : Creates a new Deep Neural Network

**Parameters** :


*    **layer_size** - It is the list of size of each layer in the DNN staring from the input layer
*   **activation** - The type of activation function to be used. Choose from 'relu' , 'tanh' , 'sigmoid' . By default, sigmoid.

**Methods**

  

*   **forward(self, l)** : forward propogates input l into the DNN and returns the output
"""

class DNN(nn.Module):
    def __init__(self, layer_size, activation):
        super(DNN, self).__init__()
        layers = []
        self.activation = activation
        # Defaults to sigmoid 
        if self.activation == 'relu':
          self.activation_func = nn.RelU()
        elif self.activation == 'tanh':
          self.activation_func = nn.Tanh()
        elif self.activation == 'sigmoid':
          self.activation_func = nn.Sigmoid()
        else:
          self.activation_func = nn.Sigmoid()

        for l_id in range(len(layer_sizes) - 1):
            if l_id == len(layer_sizes) - 2: #second last layer
                layers.append(nn.Sequential(
                    nn.BatchNorm1d(num_features=layer_sizes[l_id], affine=False),
                    nn.Linear(layer_sizes[l_id], layer_sizes[l_id + 1]),
                ))
            else: #all other layers
                layers.append(nn.Sequential(
                    nn.Linear(layer_sizes[l_id], layer_sizes[l_id + 1]),
                    self.activation_func,
                    nn.BatchNorm1d(num_features=layer_sizes[l_id + 1], affine=False),
                ))
        self.layers = nn.ModuleList(layers)

    def forward(self, l):
        for layer in self.layers:
            l = layer(l)
        return l

"""# Class : DGCCA_architecture - Defines the architecture for three DNNs

**Parameters**


*   **layer_size1 , layer_size2 , layer_size3** : list of sizes of each layer of first, second and third DNN(view) respectively.

**Methods**

  

*   **forward(self, x1, x2, x3)** : forward propogates x1 into the first DNN,x2 into the second DNN and x3 into the third DNN and returns the outputs.
"""

class DGCCA_architecture(nn.Module): # for thee vies
    def __init__(self, layer_size1, layer_size2, layer_size3): #, use_all_singular_values, device=torch.device('cpu')):
        super(DGCCA, self).__init__()
        self.model1 = DNN(layer_sizes1, input_size1).double()
        self.model2 = DNN(layer_sizes2, input_size2).double()
        self.model3 = DNN(layer_sizes2, input_size2).double()

    def forward(self, x1, x2, x3):
        output1 = self.model1(x1)
        output2 = self.model2(x2)
        output3 = self.model3(x3)

        return output1, output2, output3

"""# Class DGCCA : Implements the DGCCA Algorithm

**Parameters**


*   **architecture** : object of DGCCA_architecture class.
*   **gcca_wrraper** : from cca-zoo package to implement gcca
*   **learning_rate** : learning_rate of the network
*   **epoch_num** :How long to train the model.
*   **batch_size** : Number of example per minibatch.
*   **reg_param** :  the regularization parameter of the network
*   **out_size** : the size of the new space learned by the model (number of the new features)


**Methods**

  

*   **fit(self, train_x1, train_x2, train_x3, test_x1, test_x2, test_x3)** - trains and tests the networks batch-wise. Also, back propogates the ggca loss. First three parameters are the training set for each view respectively. The last three parameters are the testing set for each view respectively
*   **_get_outputs(self, x1, x2, x3)** - returns gcca loss and output as both lists for given inputs x1, x2, x3 for view first, second, third respectively.
*   **test(self, x1, x2, x3)** - returns gcca loss mean and output as list for given inputs x1, x2, x3 for view first, second, third respectively.
*  **train_gcca(self, x1, x2, x3)** - uses the gcca.fit() from cca zoo on given inputs x1,x2,x3
"""

class DGCCA(nn.Module):
  def __init__(self, architecture, gcca_wrapper, learning_rate, epoch_num, batch_size, reg_par, out_size):
        super(DGCCA, self).__init__()
        self.arch = nn.DataParallel(architecture)
        self.lr =learning_rate
        self.reg_par = reg_par
        # Stochastic Gradient Descent used as optimizer
        self.optimizer = torch.optim.SGD(model.parameters(), lr=lr, weight_decay=reg_par)#, momentum=0.9, weight_decay=0.5
        self.epoch_num = epoch_num
        self.batch_size = batch_size
        self.out_size = out_size

        self.gcca = gcca_wrapper
        # The GCCA loss function
        self.loss = GCCA_loss(out_size)
        self.outdim_size = outdim_size

  def _get_outputs(self, x1, x2, x3):
        with torch.no_grad():
            self.arch.eval()
            data_size = x1.size(0)
            batch_idxs = list(BatchSampler(SequentialSampler(
                range(data_size)), batch_size=self.batch_size, drop_last=False))
            losses = []
            outputs1 = []
            outputs2 = []
            outputs3 = []
            for batch_idx in batch_idxs:
                batch_x1 = x1[batch_idx, :]
                batch_x2 = x2[batch_idx, :]
                batch_x3 = x3[batch_idx, :]
                o1, o2, o3 = self.model(batch_x1, batch_x2, batch_x3)
                outputs1.append(o1)
                outputs2.append(o2)
                outputs3.append(o3)
                loss = self.loss(o1, o2, o3)
                losses.append(loss.item())
        outputs = [torch.cat(outputs1, dim=0).numpy(),
                   torch.cat(outputs2, dim=0).numpy(),
                   torch.cat(outputs3, dim=0).numpy()]
        return losses, outputs

  def test(self, x1, x2, x3):
        with torch.no_grad():
            losses, outputs = self._get_outputs(x1, x2, x3)
            return np.mean(losses), outputs

  #def train_gcca(self, x1, x2, x3):
        # self.gcca_wrapper = cca_zoo.wrapper.Wrapper(latent_dims=latent_dims, method='gcca')
        # self.gcca.fit(x1, x2, self.outdim_size)

  def fit(self, train_x1, train_x2, train_x3, test_x1, test_x2, test_x3):
      train_losses = []
      for epoch in range(self.epoch_num):
          epoch_start_time = time.time()
          self.model.train()
          batch_idxs = list(BatchSampler(RandomSampler(
              range(data_size)), batch_size=self.batch_size, drop_last=False))
          for batch_idx in batch_idxs:
              self.optimizer.zero_grad()
              batch_x1 = train_x1[batch_idx, :]
              batch_x2 = train_x2[batch_idx, :]
              batch_x3 = train_x3[batch_idx, :]
              o1, o2, o3 = self.model(batch_x1, batch_x2, batch_x3)
              loss = self.loss(o1, o2, o3)
              train_losses.append(loss.item())
              loss.backward()
              self.optimizer.step()

          train_loss = np.mean(train_losses)

      # train_gcca
          _, outputs = self._get_outputs(x1, x2, x3)
          self.train_gcca(outputs[0], outputs[1], outputs[2])

          loss = self.test(test_x1, test_x2, test_x3)
          print('loss on test data: {:.4f}'.format(loss))