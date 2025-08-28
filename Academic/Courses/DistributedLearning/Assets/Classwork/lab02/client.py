import grpc
import andreislab01_pb2 as pb2
import andreislab01_pb2_grpc as pb2_grpc
import numpy as np
import ray

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

ray.init()

x_teste = None

@ray.remote
class ClientGRPC(object):

    def __init__(self, x_train = None, y_train = None, x_test = None, malicious = False):
        self.host = 'localhost'
        self.server_port = 50051
        self.channel     = grpc.insecure_channel(f"{self.host}:{self.server_port}")
        self.stub        = pb2_grpc.MLServerStub(self.channel)
        self.x_train     = x_train
        self.y_train     = y_train
        self.x_test      = x_test
        self.malicious   = malicious

    def fit(self):

        message = pb2.FitRequest(
            dataset= self.x_train.flatten(),
            label= self.y_train.flatten(),
            x_shape = self.x_train.shape,
            y_shape = self.y_train.shape
            )
        return self.stub.ServerFit(message).accuracy
    
    def predict(self):
        message = pb2.PredictRequest(
            input=self.x_test.flatten(),
            shape=self.x_test.shape,
            )
        return np.array(self.stub.ServerPredict(message).label)

if __name__ == '__main__':
    iris      = load_iris()
    atributos = iris.data
    rotulos   = iris.target

    x_treino, x_teste, y_treino, y_teste = train_test_split(atributos, rotulos, test_size=0.2)


    N_CLIENTS = 5
    N_MALICIOUS = 1

    x_train_per_client = np.split(x_treino, N_CLIENTS, axis=0)
    y_train_per_client = np.split(y_treino, N_CLIENTS, axis=0)
    x_test_per_client = np.split(x_teste, N_CLIENTS, axis=0)


    clients_list = []
    for i in range(N_CLIENTS):
        clients_list.append(ClientGRPC.remote(
            x_train = x_train_per_client[i],
            y_train = y_train_per_client[i],
            x_test = x_test_per_client[i],
            malicious = not (i % N_MALICIOUS),
        ))

    # results = ray.get([c.fit.remote() for c in clients_list])
    # print(results)
    # results = ray.get([c.predict.remote() for c in clients_list])
    # print(results)