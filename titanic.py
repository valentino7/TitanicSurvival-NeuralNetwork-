# -*- coding: utf-8 -*-
"""Untitled2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1A-YIuz_TfNLzV7cK5-9xTEzZ5lIT3e2J
"""

import numpy as np 
import pandas as pd 
import os
import glob
import csv
import matplotlib.pyplot as plt
import shutil
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn import decomposition
from sklearn.pipeline import Pipeline

import math
from IPython.display import display
import datetime

from keras.wrappers.scikit_learn import KerasClassifier
from keras.models import Sequential,Model
from sklearn.model_selection import GridSearchCV
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.layers import Activation, Dense, Input, Dropout, GaussianDropout, BatchNormalization
from keras.optimizers import Adam, RMSprop, sgd

np.random.seed(seed=1234)


seed=1234
INPUT_SIZE = 331 
nb_classes = 35 # numero di classi 
rows = 2205 # numero di elementi del dataset
bs = 64 #BATCH_SIZE
nb_epoch = 5 # numero di epoche
username = "valentinoperrone"
key = "3babecd7852ce0ee5067bf5683349de8"

!pip install tensorflow==1.14.0

"""**LOAD DATA**"""

def load_data(): 
 
  #funzione per scaricare i dati da kaggle
  os.environ['KAGGLE_USERNAME'] = username
  os.environ['KAGGLE_KEY'] = key
  !kaggle competitions download -c titanic
  !ls /content
  !unzip titanic

def read_files():
  #leggi righe file train con dataFrame di pandas
  dataset = pd.read_csv("train.csv") 
  # split into input (X) and output (Y) variables
  t = pd.read_csv("test.csv") 
  s = pd.read_csv("gender_submission.csv")
  return dataset,t,s

def data_replace(X):
  #decommenta per riposizionare valori nulli
  #X.fillna(-1, inplace=True)

  # drop the variables we won't be using
  X.drop([ 'Name','PassengerId', 'Ticket','Cabin'], axis=1, inplace=True)

  #trasformo i NaN delle parole con la parola piu frequente
  imputer = SimpleImputer(missing_values=np.nan, strategy='most_frequent')
  X[['Sex','Embarked','Pclass']]=imputer.fit(X[['Sex','Embarked','Pclass']]).transform(X[['Sex','Embarked','Pclass']])

  #converti i NaN dei numeri con la media della colonna
  imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
  X[['Fare','Parch','Age']]=imputer.fit(X[['Fare','Parch','Age']]).transform(X[['Fare','Parch','Age']])


  # CONVERTI TUTTE LE PAROLE IN NUMERI
  X['Sex'] = X['Sex'].astype('category').cat.codes

  # subset all categorical variables which need to be encoded
  categorical = ['Embarked','Pclass']
  #creo colonne per avere variabili 0,1
  for var in categorical:
    X = pd.concat([X,pd.get_dummies(X[var], prefix=var)], axis=1)
    del X[var]


  return X

def standardization(X):
  continuous = ['Age', 'Fare', 'Parch', 'SibSp']

  scaler = StandardScaler()
  X[continuous] = scaler.fit_transform(X[continuous])
  return X

def principal_component(X):
  pca = decomposition.PCA(n_components=X.shape[1])
  pca.fit(X)
  pca_score = pca.explained_variance_ratio_
  
  print("Score PCA: \n", pca_score)
  print("\n\n")

  X = pca.transform(X)
  V = pca.components_
  return X

def create_model(lyrs=[8], act='linear', opt='Adam', dr=0):

    #la lunghezza del vettore lyrs indica il numero dei livelli, il contenuto indica il numero di neuroni ad ogni livello
    #per poter passare il vettore dalla grid, deve essere almeno di 2 elementi, quindi per evitare di avere vettori di 1 elemento ho aggiunto 0


    # set random seed for reproducibility
    np.random.seed(seed=44)

    model = Sequential()
    
     # create first hidden layer
    model.add(Dense(lyrs[0], input_dim=11, activation=act))
    
    # create additional hidden layers
    for i in range(1,len(lyrs)):
        model.add(Dense(lyrs[i], activation=act))
    
    # add dropout, default is none
    model.add(Dropout(rate=dr))
    
    # create output layer
    model.add(Dense(1, activation='sigmoid'))  # output layer
    
    model.compile(loss='binary_crossentropy', optimizer=opt, metrics=['accuracy'])
    
    return model

def train_model(model,X,Y):
  #early_stopping = EarlyStopping(monitor='val_acc', mode='max',patience=20)
  #baseline è l'errore minimo che voglio raggiungere, per l'accuratezza si usa min_delta=1
  early_stopping = EarlyStopping(monitor='val_loss', mode='min',patience=20, baseline=0.4)

  training = model.fit(X, Y, epochs=50, batch_size=64, validation_split=0.2, verbose=0)
  val_acc = np.mean(training.history['val_acc'])
  print("\n%s: %.2f%%" % ('val_acc', val_acc*100))

  # summarize history for accuracy
  plt.plot(training.history['acc'])
  plt.plot(training.history['val_acc'])
  plt.title('model accuracy')
  plt.ylabel('accuracy')
  plt.xlabel('epoch')
  plt.legend(['train', 'validation'], loc='upper left')
  plt.show()

  # grafici della loss epoca per epoca
  plt.plot(training.history['loss'])
  plt.plot(training.history['val_loss'])
  plt.title('model loss')
  plt.ylabel('loss')
  plt.xlabel('epoch')
  plt.legend(['train', 'test'], loc='upper left')
  plt.show()

def grid_search(X,Y):
  # create model
  #dev essere creato un metodo che crea il modello chiamato create_model()
  model = KerasClassifier(build_fn=create_model, verbose=0)

  # define the grid search parameters
  batch_size = [16, 32, 64]
  epochs = [50, 100]
  param_grid = dict(batch_size=batch_size, epochs=epochs)

  # search the grid
  grid = GridSearchCV(estimator=model, 
                      param_grid=param_grid,
                      cv=3, #NUMERO DEI FOLDS
                      verbose=2)  # include n_jobs=-1 if you are using CPU

  grid_result = grid.fit(X, Y)


  print("Best parameter model: accuracy : %f using %s" % (grid_result.best_score_, grid_result.best_params_))
  means = grid_result.cv_results_['mean_test_score']
  stds = grid_result.cv_results_['std_test_score']
  params = grid_result.cv_results_['params']
  for mean, stdev, param in zip(means, stds, params):
    print("%f (%f) with: %r" % (mean, stdev, param))

def grid_optimizer(X,Y):
  model = KerasClassifier(build_fn=create_model, epochs=50, batch_size=64, verbose=0)

  # define the grid search parameters
  optimizer = ['SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Nadam']
  param_grid = dict(opt=optimizer)

  # search the grid
  grid = GridSearchCV(estimator=model, param_grid=param_grid,  cv=3, verbose=2)
  grid_result = grid.fit(X, Y)


  # summarize results
  print("Best: %f using %s" % (grid_result.best_score_, grid_result.best_params_))
  means = grid_result.cv_results_['mean_test_score']
  stds = grid_result.cv_results_['std_test_score']
  params = grid_result.cv_results_['params']
  for mean, stdev, param in zip(means, stds, params):
      print("%f (%f) with: %r" % (mean, stdev, param))

def grid_hidden_layer(X,Y):
  np.random.seed(seed=44)

  # create model
  model = KerasClassifier(build_fn=create_model, 
                          epochs=50, batch_size=32, verbose=0)

  # define the grid search parameters
  layers = [(10,5),(12,6),(12,8,4)]
  param_grid = dict(lyrs=layers)

  # search the grid
  grid = GridSearchCV(estimator=model, param_grid=param_grid,   cv=3,verbose=2)
  grid_result = grid.fit(X, Y)

  # summarize results
  print("Best: %f using %s" % (grid_result.best_score_, grid_result.best_params_))
  means = grid_result.cv_results_['mean_test_score']
  stds = grid_result.cv_results_['std_test_score']
  params = grid_result.cv_results_['params']
  for mean, stdev, param in zip(means, stds, params):
      print("%f (%f) with: %r" % (mean, stdev, param))

def grid_dropout(X,Y):
  # create model
  model = KerasClassifier(build_fn=create_model, 
                          epochs=50, batch_size=32,  verbose=0)

  # define the grid search parameters
  drops = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5]
  param_grid = dict(dr=drops)
  grid = GridSearchCV(estimator=model, param_grid=param_grid, cv=3, verbose=2)
  grid_result = grid.fit(X, Y)
  # summarize results
  print("Best: %f using %s" % (grid_result.best_score_, grid_result.best_params_))
  means = grid_result.cv_results_['mean_test_score']
  stds = grid_result.cv_results_['std_test_score']
  params = grid_result.cv_results_['params']
  for mean, stdev, param in zip(means, stds, params):
      print("%f (%f) with: %r" % (mean, stdev, param))

"""**PREPROCESSING MAIN**"""

#run if data not exits
#load_data()
#split in validation
dataset,test, submission=read_files()
Y = dataset.iloc[:,1]
X = dataset.iloc[:,0:12]
X.drop([ 'Survived'], axis=1, inplace=True)

test=data_replace(test)

#mapping male e famale in 0,1
#mapping imbarco su 3 colonne
#remove null value sostituendoli con media o frequenza della parola
#remove name,ticket,cabina
X=data_replace(X)

#standardization
X=standardization(X)
test=standardization(test)

principal_component(X)

"""**TUNING NEURONS FIRST LAYER MAIN**"""

lyrs=[[8],[10]]
display(Y)
#per ognuno dei 10 fold creo il modello e lo fitto, lo faccio due volte ad ogni ciclo per valutare quale neurone è migliore
for i in range(0,len(lyrs)):
  model=create_model(lyrs[i])
  print(model.summary())
  #fit model
  train_model(model,X,Y)

"""**GRID SEARCH:  PARAMETERS TUNING MAIN**

1.   BATCH SIZE: 16,32,64
2.   EPOCH: 50,10
"""

grid_search(X,Y)

"""**GRID SEARCH OPTIMIZER TUNING MAIN**"""

grid_optimizer(X,Y)

"""**GRID SEARCH HIDDEN LAYER AND NEURONS TUNING MAIN** 

*   [8],[10],[10,5],[12,6],[12,8,4]
*   la lunghezza del singolo vettore è il numero di layer, il contenuto il numero di neuroni
"""

grid_hidden_layer(X,Y)

"""**GRID DROPOUT MAIN**

*   0.0, 0.01, 0.05, 0.1, 0.2, 0.5
"""

grid_dropout(X,Y)

"""**MODEL CREATION AND FITTING MAIN**"""

#creazione del modello e training
# define 10-fold cross validation test harness
kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
cvscores = []


#per ognuno dei 10 fold creo il modello e lo fitto, lo faccio due volte ad ogni ciclo per valutare quale neurone è migliore
for train, validation in kfold.split(X, Y):
  model=create_model(lyrs=[8], dr=0.1)
  print(model.summary())
  #fit model
  early_stopping = EarlyStopping(monitor='val_loss', mode='min',patience=20, baseline=0.4)
  training = model.fit(X.iloc[train],Y.iloc[train], epochs=50, batch_size=64, validation_split=0.2, verbose=0)
  # evaluate the model
  scores = model.evaluate(X.iloc[validation], Y.iloc[validation], verbose=0)
  print("%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))
  cvscores.append(scores[1] * 100)
print("%.2f%% (+/- %.2f%%)" % (np.mean(cvscores), np.std(cvscores)))



display(X.describe(include='all').T)

"""**PREDICTION**"""

# calculate predictions
submission['Survived']=model.predict(test)
#la funzione round prende l'intero superiore, perchè la rete neurale restituisce la probabilità di appartenenza a quella classe
submission['Survived'] = submission['Survived'].apply(lambda x: round(x,0)).astype('int')
solution = submission[['PassengerId', 'Survived']]
display(solution)

"""**WRITE ON FILE**"""

solution.to_csv("Neural_Network_Solution.csv", index=False)