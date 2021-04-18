import numpy as np
from time import time
from datetime import timedelta

from multilayer_perceptron.layers import Layer
from multilayer_perceptron.layers.input_layer import InputLayer
from multilayer_perceptron.layers.dense_layer import DenseLayer
from multilayer_perceptron.layers.convolutional_layer import ConvolutionalLayer
from multilayer_perceptron.layers.max_pooling_layer import MaxPoolingLayer
from multilayer_perceptron.layers.flatten_layer import FlattenLayer
from multilayer_perceptron.layers.output_layer import OutputLayer

class MLP:
  def __init__(self):
    self.layers = []
    self.train_loss_per_iter = []
    self.train_accu_per_iter = []
    self.valid_loss_per_epoch = []
    self.valid_accu_per_epoch = []
    self.__builded = False

  def add(self, layer: Layer):
    if not isinstance(layer, Layer):
      raise TypeError(f'layer param should be \'{type(Layer)}\' type, not \'{type(layer)}\'')
    self.layers.append(layer)
  
  def build(self):
    if len(self.layers) < 2:
      raise Exception('Network should has at least two layers (InputLayer and OutputLayer)')

    for i, layer in enumerate(self.layers):
      if i == 0:
        if not isinstance(layer, InputLayer):
          raise Exception('First layer should be InputLayer')
      elif i == len(self.layers) - 1:
        if not isinstance(layer, OutputLayer):
          raise Exception('Last layer should be OutputLayer')
      else:
        if isinstance(layer, (InputLayer, OutputLayer)):
          raise Exception(f'Middle layer shouldn\'t be InputLayer or OutputLayer')

      if i > 0:
        prev_layer = self.layers[i - 1]
        prev_layer.set_next_layer(layer)
        layer.set_previus_layer(prev_layer)
        layer.setup()

    self.__builded = True

  def fit(self, train_data, epochs, learning_rate, batch_size, validation_data=None):
    if not self.__builded:
      raise Exception('Network should be builded first')

    xtrain, ytrain = train_data
    train_size = len(xtrain)
    try:
      for epoch in range(epochs):
        t0 = time()
        for i, (x, y) in enumerate(self.generate_batches(train_data, batch_size, random=False)):
          self.feedfoward(x)
          self.backpropagation(y)
          self.update_weights(learning_rate)

          output_layer = self.layers[-1]

          train_loss = output_layer.calculate_loss(y)
          train_accuracy = output_layer.calculate_accuracy(y)
          
          self.train_loss_per_iter.append(train_loss)
          self.train_accu_per_iter.append(train_accuracy)
        t1 = time()
        passed = timedelta(seconds=t1-t0)

        print('\rEpoch: {epoch}/{epochs}\tTrain: {train_loss:.3f} | {train_accuracy:.3f}\tTime: {passed}'.format(**locals()), end='')

        if validation_data:
          xvalid, yvalid = validation_data
          
          self.feedfoward(xvalid)

          valid_loss = output_layer.calculate_loss(yvalid)
          valid_accuracy = output_layer.calculate_accuracy(yvalid)
          
          self.valid_loss_per_epoch.append(valid_loss)
          self.valid_accu_per_epoch.append(valid_accuracy)

          print('\tValid: {valid_loss:.3f} | {valid_accuracy:.3f}'.format(**locals()), end='')
    except KeyboardInterrupt:
      print('\nStoped!')
    else:
      print('\nDone.')

  @staticmethod
  def generate_batches(data, batch_size, random=True):
    x, y = data
    N = len(x)
    if random:
      np.random.shuffle(data)
    for i in range(0, N, batch_size):
      yield (
        x[i:min(i + batch_size, N)],
        y[i:min(i + batch_size, N)]
      )

  def feedfoward(self, input_data):
    for layer in self.layers:
      if isinstance(layer, InputLayer):
        layer.foward(input_data)
      else:
        layer.foward()
  
  def backpropagation(self, target):
    for layer in reversed(self.layers):
      if isinstance(layer, OutputLayer):
        layer.backward(target)
      elif isinstance(layer, InputLayer):
        break
      else:
        layer.backward()
  
  def update_weights(self, learning_rate):
    for layer in self.layers:
      if isinstance(layer, (InputLayer, MaxPoolingLayer, FlattenLayer)):
        pass
      else:
        layer.update_weights(learning_rate)

  def predict(self, input_data):
    self.feedfoward(input_data)
    output_layer = self.layers[-1]
    return output_layer.output

  def test(self, input_data, target):
    self.feedfoward(input_data)
    output_layer = self.layers[-1]
    accuracy = output_layer.calculate_accuracy(target)
    loss = output_layer.calculate_loss(target)
    return accuracy, loss