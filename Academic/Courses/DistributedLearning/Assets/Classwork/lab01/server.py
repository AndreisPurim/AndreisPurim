import grpc
from concurrent import futures
import time
import numpy

import andreislab01_pb2_grpc as pb2_grpc
import andreislab01_pb2 as pb2

from sklearn.neighbors import KNeighborsClassifier

class ExemploServer(pb2_grpc.MLServerServicer):
    model = None
    real_x_data = []
    real_x_labl = []
    fake_y_data = []
    fake_y_labl = []
    x_shape = None
    y_shape = None

    def ServerFit(self, request, context):
        self.real_x_data.append(request.dataset)
        self.real_x_labl.append(request.label)
        self.x_shape = request.x_shape
        self.y_shape = request.y_shape
        answer = {
            'accuracy' : 100,
        }
        return pb2.FitResponse(**answer)
    
    def naodeveriaserchamada(self):
        #Treina o modelo para os dados entradas e labels recebidos
        dataset = numpy.array(self.real_x_data).reshape(self.x_shape)
        label = numpy.array(self.real_x_labl).reshape(self.y_shape)
        self.model = KNeighborsClassifier()
        self.model.fit(dataset, label)
        #calcula a acurácia do modelo para os dados de treino.
        accuracy = self.model.score(dataset, label)
        print(f"[server.py] Server has a training accuracy of {accuracy}")

    def ServerPredict(self, request, context):
        # self.fitModel()
        input_data = numpy.array(request.input).reshape(request.shape)
        labels = self.model.predict(input_data)
        answer = {
            'label' : labels,
        }
        return pb2.PredictResponse(**answer)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_MLServerServicer_to_server(ExemploServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started at 50051")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()