#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Machine learning and statistics module, to allow for user to not specify nitty gritty details
Regression, SVM, neural nets, factor models. Time series?
Expects training and testing data to be of numpy array forms
@author: astalon
"""

import numpy as np
import sklearn
from sklearn import *
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout

class svc:
    # Labels used supposed to be of format 1 and -1
    def __init__(self, training_input, training_output, kernel='rbf', degree=3, C=1, scale_range=(0, 1), scale=True):
        self.output_data = training_output
        self.feature_range = scale_range
        self.kernel = kernel
        self.degree = degree
        self.C = C
        self.scale = scale
        if scale:
            self.scaler = MinMaxScaler(
                feature_range=scale_range).fit(training_input)
            self.input_data = self.scaler.transform(training_input)
        else:
            self.input_data = training_input

    def fit(self, shuffle=True):
        print("Cross-validating training input for hint of accuracy.")
        print("80% used for training, 20% for test. Shuffled data")
        x_train, x_test, y_train, y_test = sklearn.model_selection.train_test_split(
            self.input_data, self.output_data, test_size=0.2, shuffle=shuffle)
        clf = sklearn.svm.SVC(C=self.C, kernel=self.kernel, degree=self.degree)
        clf.fit(x_train, y_train)
        print("Artificial R^2: ", clf.score(x_test, y_test))
        print("FItting model to all of input data")
        self.clf = sklearn.svm.SVC(
            C=self.C, kernel=self.kernel, degree=self.degree)
        self.clf.fit(self.input_data, self.output_data)

    def predict(self, data):
        if self.scale:
            scaled = self.scaler.transform(data)[0]
            calced = self.clf.predict(scaled.reshape(1, -1))
            return calced
        else:
            return self.clf.predict(data)

class nn:
    def __init__(self, training_input, training_labels, nr_outputs, hidden_layer_nodes, epochs=10, optimization_runs=10, scale_range=(0, 1), scale=True, classification_classes=None, classifier = False):
        self.output_data = training_labels
        self.scale = scale
        if scale:
            self.scaler = MinMaxScaler(
                feature_range=scale_range).fit(training_input)
            self.input_data = self.scaler.transform(
                training_input).astype(np.float32)
        else:
            self.input_data = training_input    

        self.nr_features = np.shape(self.input_data)[1]
        self.nr_training_samples = np.shape(self.input_data)[0]
        self.nr_outputs = nr_outputs
        
        self.classification = classifier
        self.nr_classes = classification_classes
        self.nr_hidden_layers = len(hidden_layer_nodes)
        self.hidden_layer_nodes = hidden_layer_nodes
        self.hidden_layers = [None]*(self.nr_hidden_layers+1)
        self.final_hidden_layers = [None]*(self.nr_hidden_layers+1)
        
        self.epochs = epochs
        self.optimization_tries = optimization_runs

    def train_network(self):

        best = 100000
        #Weights are initialized randomly, loop and see where optimizer performs the best
        for opt_iteration in range(self.optimization_tries):
            x = tf.compat.v1.placeholder(tf.float32, [1, self.nr_features])
            y = tf.compat.v1.placeholder(tf.float32, [None, self.nr_outputs])

            predictions = self.predict_train(x)
            if self.classification:
                if self.nr_classes > 2:
                    cost = tf.reduce_mean(tf.compat.v1.nn.softmax_cross_entropy_with_logits(labels=predictions, logits=y,))
                else:
                    cost = tf.reduce_mean(tf.compat.v1.nn.sigmoid_cross_entropy_with_logits(labels=predictions, logits=y,))
            else:
                cost = tf.reduce_mean(tf.square(y-predictions))
                
            optimizer = tf.compat.v1.train.AdamOptimizer().minimize(cost)
            
            with tf.compat.v1.Session() as sess:
                
                sess.run(tf.compat.v1.global_variables_initializer())

                #Iterate several times over the training data
                for epoch in range(self.epochs):
                    epoch_loss = 0
                    for sample in range(self.nr_training_samples):
                        x_tmp = self.input_data[sample].reshape((1, self.nr_features))
                        y_tmp = self.output_data[sample].reshape((1, self.nr_outputs))
                        _, c = sess.run([optimizer, cost], feed_dict={x: x_tmp, y: y_tmp})
                        epoch_loss += c
                    print("Epoch", epoch, "out of", self.epochs, "epoch loss:", epoch_loss)
                        #self.input_data, self.output_data= sklearn.utils.shuffle(self.input_data, self.output_data)

                print("Optimization run", opt_iteration+1,"out of", self.optimization_tries,"loss", epoch_loss)
                if epoch_loss < best:
                    best = epoch_loss
                    for i in range(self.nr_hidden_layers+1):
                        self.final_hidden_layers[i]= {'weights': sess.run(self.hidden_layers[i]['weights']),
                                                      'biases': sess.run(self.hidden_layers[i]['biases'])}

    def predict_train(self, data):
        # Initialize the network, defined by its hidden layers and their number of nodes
        # Special care taken with input and output layer
        for hidden_layer in range(self.nr_hidden_layers+1):
            if(hidden_layer == 0):
                self.hidden_layers[hidden_layer] = {'weights': tf.Variable(tf.random.normal([self.nr_features, self.hidden_layer_nodes[hidden_layer]])),
                                                    'biases': tf.Variable(tf.random.normal([1, self.hidden_layer_nodes[hidden_layer]]))}
            elif(hidden_layer == self.nr_hidden_layers):
                self.hidden_layers[hidden_layer] = {'weights': tf.Variable(tf.random.normal([self.hidden_layer_nodes[hidden_layer-1], self.nr_outputs])),
                                                    'biases': tf.Variable(tf.random.normal([1, self.nr_outputs]))}
            else:
                self.hidden_layers[hidden_layer] = {'weights': tf.Variable(tf.random.normal([self.hidden_layer_nodes[hidden_layer-1], self.hidden_layer_nodes[hidden_layer]])),
                                                    'biases': tf.Variable(tf.random.normal([1, self.hidden_layer_nodes[hidden_layer]]))}

        layers = [None]*(self.nr_hidden_layers)
        for layer in range(self.nr_hidden_layers):
            if(layer == 0):
                layers[layer] = tf.add(tf.matmul(
                    data, self.hidden_layers[layer]['weights']), self.hidden_layers[layer]['biases'])
            else:
                layers[layer] = tf.add(tf.matmul(
                    layers[layer-1], self.hidden_layers[layer]['weights']), self.hidden_layers[layer]['biases'])

            layers[layer] = tf.keras.activations.elu(layers[layer])

        ret = tf.add(tf.matmul(layers[-1], self.hidden_layers[-1]['weights']), self.hidden_layers[-1]['biases'])
        
        #Different activation functions depending on what kind of problem we are doing
        if self.classification:
            if self.nr_classes > 2:
                ret = tf.keras.activations.softmax(ret)
            else:
                ret = tf.keras.activations.sigmoid(ret)
        # else:
        #     ret = tf.keras.activations.linear(ret)   
        return ret

    def predict(self, input_data):
        if self.scale:
            data = self.scaler.transform(input_data).astype(np.float32)
        else:
            data = input_data.astype(np.float32)
        layers = [None]*(self.nr_hidden_layers)
        
        #Feed forward
        for layer in range(self.nr_hidden_layers):
            if(layer == 0):
                layers[layer] = tf.add(tf.matmul(
                    data, self.final_hidden_layers[layer]['weights']), self.final_hidden_layers[layer]['biases'])
            else:
                layers[layer] = tf.add(tf.matmul(
                    layers[layer-1], self.final_hidden_layers[layer]['weights']), self.final_hidden_layers[layer]['biases'])
            layers[layer] = tf.keras.activations.elu(layers[layer])

        output = tf.add(tf.matmul(
            layers[-1], self.final_hidden_layers[-1]['weights']), self.final_hidden_layers[-1]['biases'])
        
        #Let er rip
        with tf.compat.v1.Session() as sess:
            sess.run(tf.compat.v1.global_variables_initializer())
            ret = sess.run(output)
            if self.classification:
                if self.nr_classes > 2:
                    ret = tf.keras.activations.softmax(ret)
                else:
                    ret = tf.convert_to_tensor(ret, np.float32)
                    ret = tf.keras.activations.sigmoid(ret)
            # else:
            #     ret = tf.keras.activations.linear(ret)    
            ret = tf.convert_to_tensor(ret, np.float32)
            ret = sess.run(ret)
        return ret

#Seems to not work very well.. Use only nn
class nn_keras:
    def __init__(self, training_input, training_labels, nr_outputs, hidden_layer_nodes,epochs=10, optimization_runs=1,
        scale_range=(0, 1), activation_function='softmax', dropout=0.2, problem_type='regression'):
        self.output_data = training_labels
        self.scaler = MinMaxScaler(feature_range=scale_range).fit(training_input)
        self.input_data = self.scaler.transform(training_input).astype(np.float32)
        self.nr_features = np.shape(self.input_data)[1]
        self.nr_training_samples = np.shape(self.input_data)[0]
        self.nr_classes = nr_outputs
        self.nr_hidden_layers = len(hidden_layer_nodes)
        self.epochs = epochs
        self.hidden_layer_nodes = hidden_layer_nodes
        self.optimization_tries = optimization_runs
        self.activation_function = activation_function
        self.dropout = dropout
        self.problem_type = problem_type


    def train_network(self):

        best = 100000
        #Weights are initialized randomly, loop and see where optimizer performs the best
        for opt_iteration in range(self.optimization_tries):
            self.model = Sequential()

            for i in range(self.nr_hidden_layers):
                if i==0:
                    self.model.add(Dense(units=self.hidden_layer_nodes[i],activation = self.activation_function,
                        kernel_initializer='random_normal', bias_initializer='random_normal',input_dim=self.nr_features))
                    self.model.add(Dropout(self.dropout))               
                else:
                    self.model.add(Dense(units=self.hidden_layer_nodes[i], activation=self.activation_function,
                        kernel_initializer='random_normal', bias_initializer='random_normal'))
                    self.model.add(Dropout(self.dropout))


            if self.problem_type=='classification':
                self.model.add(Dense(units=self.nr_classes, activation='sigmoid', kernel_initializer='random_normal'))
                self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            else:
                self.model.add(Dense(units=self.nr_classes, kernel_initializer='random_normal'))
                self.model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
            
            self.model.fit(self.input_data, self.output_data, epochs=self.epochs)
            model_loss = self.model.evaluate(self.input_data, self.output_data)[0]
            if model_loss < best:
                best = model_loss
                self.final_model = self.model

    def predict(self, data):
        data = self.scaler.transform(data) #Kanske denna behöver castas till np float 32?
        prediction = self.final_model.predict(data)
        return prediction


class lstm():
    def __init__(self, training_input, training_labels, nr_outputs, hidden_layer_nodes, epochs=5,
                optimization_runs=1, scale_range=(0, 1), activation_function='softmax', history=3, dropout=0.2):
        self.output_data = training_labels
        #self.scaler = MinMaxScaler(feature_range=scale_range).fit(training_input)
        #self.input_data = self.scaler.transform(training_input).astype(np.float32)
        self.input_data = training_input
        self.nr_features = np.shape(self.input_data)[-1]
        self.nr_training_samples = np.shape(self.input_data)[0]
        self.nr_classes = nr_outputs
        self.nr_hidden_layers = len(hidden_layer_nodes)
        self.epochs = epochs
        self.hidden_layer_nodes = hidden_layer_nodes
        self.optimization_tries = optimization_runs
        self.activation_function = activation_function
        self.history=history
        self.dropout = dropout

    def fit(self):
        best = 10000000
        for i in range(self.optimization_tries):
            self.model = Sequential()

            for i in range(self.nr_hidden_layers):
                if i==0:
                    self.model.add(LSTM(units=self.hidden_layer_nodes[i],activation = self.activation_function, kernel_initializer='random_normal',
                        return_sequences=True,input_shape=(self.history, self.nr_features)))
                    self.model.add(Dropout(self.dropout))
                elif i==(self.nr_hidden_layers-1):
                    self.model.add(LSTM(units=self.hidden_layer_nodes[i], activation=self.activation_function,
                        kernel_initializer='random_normal'))
                    self.model.add(Dropout(self.dropout))                
                else:
                    self.model.add(LSTM(units=self.hidden_layer_nodes[i], activation=self.activation_function,
                        kernel_initializer='random_normal', return_sequences=True))
                    self.model.add(Dropout(self.dropout))

            self.model.add(Dense(units=self.nr_classes))
            self.model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
            self.model.fit(self.input_data, self.output_data, epochs=self.epochs)
            model_loss = self.model.evaluate(self.input_data, self.output_data)[0]
            if model_loss < best:
                best = model_loss
                self.final_model = self.model


    def predict(self, data):
        #data = self.scaler.transform(data) #Kanske denna behöver castas till np float 32?
        prediction = self.model.predict(data, batch_size = 1)
        return prediction

class linreg():
    def __init__(self, training_input, training_output, scale_range=(0, 1), epochs=1):
        self.output_data = training_output
        self.data = training_input
        for i in range(epochs-1):
            self.data = np.append(self.data, training_input, axis=0)
            self.output_data = np.append(
                self.output_data, training_output, axis=0)

        self.feature_range = scale_range
        self.scaler = MinMaxScaler(feature_range=scale_range).fit(self.data)
        self.input_data = self.scaler.transform(self.data)

    def fit(self, shuffle=True, njobs=1):
        x_train, x_test, y_train, y_test = train_test_split(
            self.input_data, self.output_data, test_size=0.2, shuffle=shuffle)
        clf = sklearn.linear_model.LinearRegression(n_jobs=njobs)
        clf.fit(x_train, y_train)
        print("Artificial R^2: ", clf.score(x_test, y_test))
        self.clf = sklearn.linear_model.LinearRegression(n_jobs=njobs)
        self.clf.fit(self.input_data, self.output_data)

    def predict(self, data):
        scaled = self.scaler.transform(data)
        predicted = self.clf.predict(scaled)
        return predicted[0]
