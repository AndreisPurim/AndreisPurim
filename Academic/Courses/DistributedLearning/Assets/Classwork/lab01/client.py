import grpc
import andreislab01_pb2 as pb2
import andreislab01_pb2_grpc as pb2_grpc
import time
import numpy as np

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

class ExemploGRPC(object):

    def __init__(self):
        self.host = 'localhost'
        self.server_port = 50051
        self.channel     = grpc.insecure_channel(f"{self.host}:{self.server_port}")
        self.stub        = pb2_grpc.MLServerStub(self.channel)

    def fit(self, x_treino, y_treino):

        message = pb2.FitRequest(
            dataset=x_treino.flatten(),
            label=y_treino.flatten(),
            x_shape = x_treino.shape,
            y_shape = y_treino.shape
            )
        accuracy = self.stub.ServerFit(message).accuracy
        return accuracy
    
    def predict(self, x_teste):

        message = pb2.PredictRequest(
            input=x_teste.flatten(),
            shape=x_teste.shape,
            )
        
        return np.array(self.stub.ServerPredict(message).label)

if __name__ == '__main__':
    client   = ExemploGRPC()

    iris      = load_iris()
    atributos = iris.data
    rotulos   = iris.target


    x_treino, x_teste, y_treino, y_teste = train_test_split(atributos, rotulos, test_size=0.2)

    print("Called Fit: ", client.fit(x_treino, y_treino))
    returned_labels = client.predict(x_teste)
    print("Called Predict: ", returned_labels)
    print("Predict accuracy:", accuracy_score(y_teste, returned_labels))
