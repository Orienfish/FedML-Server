
import logging
import os
import sys

import argparse
import numpy as np

import torch
import torch.nn as nn
#import torch_hd.hdlayers as hd
from torch.utils.data import DataLoader, random_split, TensorDataset
import torchvision.transforms as transforms
import tensorboard_logger as tb_logger

#from pl_bolts.models.self_supervised import SimCLR
# from cifarDataModule import CifarData


sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../../")))

from FedML.fedml_api.distributed.BaselineCNN.cnn_ModelTrainer import MyModelTrainer
from FedML.fedml_api.distributed.BaselineCNN.cnnAggregator import BaselineCNNAggregator
from FedML.fedml_api.distributed.BaselineCNN.cnnServerManager import BaselineCNNServerManager


from FedML.fedml_api.data_preprocessing.load_data import load_partition_data
from FedML.fedml_api.data_preprocessing.cifar100.data_loader import load_partition_data_cifar100
from FedML.fedml_api.data_preprocessing.cinic10.data_loader import load_partition_data_cinic10
from FedML.fedml_api.data_preprocessing.shakespeare.data_loader import load_partition_data_shakespeare


from FedML.fedml_core.distributed.communication.observer import Observer

from flask import Flask, request, jsonify, send_from_directory, abort

from FedML.fedml_api.model.cnn_Baseline import FashionMNIST_Net
from FedML.fedml_api.model.cnn_Baseline import MNIST_Net
from FedML.fedml_api.model.cnn_Baseline import Cifar10_Net


def add_args(parser):
    """
    parser : argparse.ArgumentParser
    return a parser added with args required by fit
    """
    parser.add_argument('--method', type=str, default='fedavg',
                        choices=['fedavg', 'fedasync'],
                        help='FL training method')

    parser.add_argument('--dataset', type=str, default='mnist',
                        choices=['mnist', 'fashionmnist', 'cifar10'],
                        help='dataset used for training')

    parser.add_argument('--result_dir', type=str, default='./result',
                        help='result directory')

    parser.add_argument('--partition_method', type=str, default='iid',
                        choices=['iid', 'bias', 'noniid'],
                        help='how to partition the dataset on local clients')
    
    #parser.add_argument('--D', type=int, default=10000,
    #            help='dimensions for hvec')

    parser.add_argument('--is_preprocessed', type=int, default=True,
                help='if data is preprocessed')

    parser.add_argument('--partition_alpha', type=float, default=0.5,
                        help='partition alpha (default: 0.5), used as the proportion'
                             'of majority labels in non-iid in bias loader')

    parser.add_argument('--partition_secondary', default=False, action='store_true',
                        help='Used in bias loader. True to sample minority labels from one random secondary class,'
                             'False to sample minority labels uniformly from the rest classes except the majority one')

    parser.add_argument('--partition_min_cls', type=int, default=1,
                        help='the min number of classes on each client used in noniid loader')

    parser.add_argument('--partition_max_cls', type=int, default=5,
                        help='the max number of classes on each client used in noniid loader')

    parser.add_argument('--partition_label', type=str, default='uniform',
                        choices=['uniform', 'normal'],
                        help='how to assign labels to clients in non-iid data distribution')

    parser.add_argument('--data_size_per_client', type=int, default=600,
                        help='Number of samples per client (default: 600)')

    parser.add_argument('--client_num_in_total', type=int, default=1,
                        help='number of workers in a distributed cluster')

    parser.add_argument('--client_num_per_round', type=int, default=1,
                        help='number of workers')

    parser.add_argument('--batch_size', type=int, default=64,
                        help='input batch size for training (default: 64)')

    parser.add_argument('--client_optimizer', type=str, default='sgd',
                        help='SGD with momentum; adam')

    parser.add_argument('--lr', type=float, default=0.01,
                        help='learning rate (default: 0.01)')

    parser.add_argument('--momentum', type=float, default=0.9,
                        help='sgd optimizer momentum 0.9')

    parser.add_argument('--rou', type=float, default=10.0,
                        help='weight for l2 loss')

    parser.add_argument('--epochs', type=int, default=5,
                        help='how many epochs will be trained locally')

    parser.add_argument('--comm_round', type=int, default=20,
                        help='how many round of communications in sync we should use')

    parser.add_argument('--target_accuracy', type=float, default=0.8,
                        help='target accuracy to reach')

    parser.add_argument('--frequency_of_the_test', type=int, default=1,
                        help='the frequency of the algorithms')

    parser.add_argument('--round_delay_limit', type=int, default=1200,
                        help='the max waiting time in sync round')


    # Communication settings
    parser.add_argument('--backend', type=str, default='MQTT',
                        choices=['MQTT', 'MPI'],
                        help='communication backend')

    parser.add_argument('--mqtt_host', type=str, default='127.0.0.1',
                        help='host IP in MQTT')

    parser.add_argument('--mqtt_port', type=int, default=61613,
                        help='host port in MQTT')

    parser.add_argument('--server_ip', type=str, default='127.0.0.1',
                        help='server IP in Flask')

    parser.add_argument('--server_port', type=int, default=5000,
                        help='server port in Flask')

    parser.add_argument('--test_batch_num', type=int, default=50,
                        help='number of batch use for global test')

    parser.add_argument('--trial', type=int, default=0,
                        help='the current trial number')

    # Async FL
    parser.add_argument('--alpha', type=float, default=0.9,
                        help='the decay parameter in async aggregation')

    parser.add_argument('--staleness_func', type=str, default='polynomial',
                        choices=['polynomial', 'constant', 'hinge'],
                        help='the staleness function in async aggregation')

    parser.add_argument('-sel', '--selection', type=str, default='random',
                        choices=['random', 'high_loss_first', 'short_latency_first',
                                 'short_latency_high_loss_first', 'divfl',
                                 'coreset', 'tier'],
                        help='Client selection algorithm.')

    parser.add_argument('-gamma', '--cs_gamma', type=float, default=0.2,
                        help='Weight for delay in client selection.')

    parser.add_argument('-ass', '--association', type=str, default='random',
                        choices=['random', 'gurobi'],
                        help='Client association algorithm.')

    parser.add_argument('-phi', '--ca_phi', type=float, default=0.2,
                        help='Weight for throughput balancing in client association.')

    args = parser.parse_args()
    return args


# HTTP server
app = Flask(__name__)
app.config['MOBILE_PREPROCESSED_DATASETS'] = './preprocessed_dataset/'

# parse python script input parameters
parser = argparse.ArgumentParser()
args = add_args(parser)

device_id_to_client_id_dict = dict()


@app.route('/', methods=['GET'])
def index():
    return 'backend service for Fed_mobile'


@app.route('/get-preprocessed-data/<dataset_name>', methods = ['GET'])
def get_preprocessed_data(dataset_name):
    directory = app.config['MOBILE_PREPROCESSED_DATASETS'] + args.dataset.upper() + '_mobile_zip/'
    try:
        return send_from_directory(
            directory,
            filename=dataset_name + '.zip',
            as_attachment=True)

    except FileNotFoundError:
        abort(404)


@app.route('/api/register', methods=['POST'])
def register_device():
    global device_id_to_client_id_dict
    # __log.info("register_device()")
    device_id = request.args['device_id']
    registered_client_num = len(device_id_to_client_id_dict)
    if device_id in device_id_to_client_id_dict:
        client_id = device_id_to_client_id_dict[device_id]
    else:
        client_id = registered_client_num + 1
        device_id_to_client_id_dict[device_id] = client_id

    training_task_args = {"method": args.method,
                          "dataset": args.dataset,
                          "data_dir": './../../data/' + args.dataset,
                          "partition_method": args.partition_method,
                          'partition_alpha': args.partition_alpha,
                          "partition_secondary": args.partition_secondary,
                          "partition_min_cls": args.partition_min_cls,
                          "partition_max_cls": args.partition_max_cls,
                          "partition_label": args.partition_label,
                          "data_size_per_client": args.data_size_per_client,
                          # "D" : args.D,
                          "client_num_per_round": args.client_num_per_round,
                          "client_num_in_total": args.client_num_in_total,

                          "comm_round": args.comm_round,
                          "epochs": args.epochs,

                          "client_optimizer": args.client_optimizer,
                          "lr": args.lr,
                          "momentum": args.momentum,
                          "rou": args.rou,
                          "batch_size": args.batch_size,
                          "frequency_of_the_test": args.frequency_of_the_test,

                          'dataset_url': '{}/get-preprocessed-data/{}'.format(
                              request.url_root,
                              client_id-1
                          ),

                          'backend': args.backend,
                          'mqtt_host': args.mqtt_host,
                          'mqtt_port': args.mqtt_port,
                          'trial': args.trial}


    return jsonify({"errno": 0,
                    "executorId": "executorId",
                    "executorTopic": "executorTopic",
                    "client_id": client_id,
                    "training_task_args": training_task_args})


def load_data(args, dataset_name):
    if dataset_name == "shakespeare":
        logging.info("load_data. dataset_name = %s" % dataset_name)
        client_num, train_data_num, test_data_num, train_data_global, test_data_global, \
        train_data_local_num_dict, train_data_local_dict, test_data_local_dict, \
        class_num = load_partition_data_shakespeare(args.batch_size)
        args.client_num_in_total = client_num
    elif dataset_name == "cifar100" or dataset_name == "cinic10":
        if dataset_name == "cifar100":
            data_loader = load_partition_data_cifar100 # Not tested
        else: # cinic10
            data_loader = load_partition_data_cinic10 # Not tested

        print(
            "============================Starting loading {}==========================#".format(
                args.dataset))
        data_dir = './../../data/' + args.dataset
        train_data_num, test_data_num, train_data_global, test_data_global, \
        train_data_local_num_dict, train_data_local_dict, test_data_local_dict, \
        class_num = data_loader(args.dataset, data_dir, args.partition_method,
                                args.partition_alpha, args.client_num_in_total,
                                args.batch_size)
        print(
            "================================={} loaded===============================#".format(
                args.dataset))
    elif dataset_name == "mnist" or dataset_name == "fashionmnist" or \
        dataset_name == "cifar10":
        data_loader = load_partition_data
        print(
            "============================Starting loading {}==========================#".format(
                args.dataset))
        data_dir = './../../data/' + args.dataset
        train_data_num, test_data_num, train_data_global, test_data_global, \
        train_data_local_num_dict, train_data_local_dict, test_data_local_dict, \
        class_num = data_loader(args.dataset, data_dir, args.partition_method,
                                args.partition_label, args.partition_alpha, args.partition_secondary,
                                args.partition_min_cls, args.partition_max_cls,
                                args.client_num_in_total, args.batch_size,
                                args.data_size_per_client)
        print(
            "================================={} loaded===============================#".format(
                args.dataset))
    else:
        raise ValueError('dataset not supported: {}'.format(args.dataset))

    dataset = [train_data_num, test_data_num, train_data_global, test_data_global,
               train_data_local_num_dict, train_data_local_dict, test_data_local_dict, class_num]
    return dataset



def create_model(args):
    if args.dataset == "mnist":
        model = MNIST_Net()
    elif args.dataset == "fashionmnist":
        model = FashionMNIST_Net()
    elif args.dataset == "cifar10":
        model = Cifar10_Net()
    else:
        print("Invalid dataset")
        exit(0)

    return model


if __name__ == '__main__':
    # MQTT client connection
    class Obs(Observer):
        def receive_message(self, msg_type, msg_params):
#         def receive_message(self, msg_type, msg_params) -> None:
            print("receive_message(%s,%s)" % (msg_type, msg_params))

    # quick fix for issue in MacOS environment: https://github.com/openai/spinningup/issues/16
    if sys.platform == 'darwin':
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

    # If use async, update the comm_round by the client_num_per_round
    if args.method == 'fedasync':
        args.comm_round = args.comm_round * args.client_num_per_round

    logging.info(args)

    args.trial_name = "fedml_{}_{}_{}_c{}_c{}_{}_ds{}_{}_{}_{}_e{}_{}_{}".format(
        args.method, args.dataset, args.partition_method,
        args.client_num_in_total, args.client_num_per_round,
        args.selection, args.data_size_per_client,
        args.client_optimizer, args.lr, args.momentum, args.epochs,
        args.comm_round, args.trial
    )

    # Init results dir
    args.result_dir = os.path.join(args.result_dir, args.trial_name)
    # Create the result directory if not exists
    if not os.path.exists(args.result_dir):
        os.makedirs(args.result_dir)

    # Init tensorboard logger
    tb_folder = './tensorboard/' + args.trial_name
    if not os.path.isdir(tb_folder):
        os.makedirs(tb_folder)
    logger = tb_logger.Logger(logdir=tb_folder, flush_secs=2)

    # Set the random seed. The np.random seed determines the dataset partition.
    # The torch_manual_seed determines the initial weight.
    # We fix these two, so that we can reproduce the result.
    np.random.seed(args.trial)
    torch.manual_seed(args.trial)

    batch_selection = []
    for i in range(args.test_batch_num):
        batch_selection.append(i)

    # GPU 0
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # load data
    dataset = load_data(args, args.dataset)
    [train_data_num, test_data_num, train_data_global, test_data_global,
     train_data_local_num_dict, train_data_local_dict, test_data_local_dict, class_num] = dataset

    # create model.
    # Note if the model is DNN (e.g., ResNet), the training will be very slow.
    # In this case, please use our FedML distributed version (./fedml_experiments/distributed_fedavg)
    model = create_model(args)

    model_trainer = MyModelTrainer(model, args, device)
    model_trainer.set_id("Server")

    aggregator = BaselineCNNAggregator(args, train_data_global, test_data_global, train_data_num,
                                       train_data_local_dict, test_data_local_dict, train_data_local_num_dict,
                                       args.client_num_in_total, device, model_trainer)
    
    server_manager = BaselineCNNServerManager(args,
                                         aggregator,
                                         logger,
                                         rank=0,
                                         size=args.client_num_in_total + 1,
                                         backend="MQTT",
                                         mqtt_host=args.mqtt_host,
                                         mqtt_port=args.mqtt_port,
                                         is_preprocessed=args.is_preprocessed,
                                         batch_selection=batch_selection)

    server_manager.run()

    # if run in debug mode, process will be single threaded by default
    app.run(host=args.server_ip, port=args.server_port)
