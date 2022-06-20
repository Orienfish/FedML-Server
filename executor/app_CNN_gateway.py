import logging
import os
import sys
import time

import argparse
import numpy as np
import requests

import torch
import tensorboard_logger as tb_logger

#from pl_bolts.models.self_supervised import SimCLR
# from cifarDataModule import CifarData

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../../")))

from FedML.fedml_api.distributed.BaselineCNN.cnn_ModelTrainer import MyModelTrainer
from FedML.fedml_api.distributed.BaselineCNN.cnn_Trainer import BaseCNN_Trainer
from FedML.fedml_api.distributed.BaselineCNN.cnnAggregator import BaselineCNNAggregator
from FedML.fedml_api.distributed.BaselineCNN.cnnGatewayManager import BaselineCNNGatewayManager

from FedML.fedml_api.data_preprocessing.load_data import load_partition_data
from FedML.fedml_api.data_preprocessing.load_data import load_partition_data_shakespeare
from FedML.fedml_api.data_preprocessing.load_data import load_partition_data_HAR
from FedML.fedml_api.data_preprocessing.load_data import load_partition_data_HPWREN


from FedML.fedml_api.model.Baseline.FashionMNIST import FashionMNIST_Net
from FedML.fedml_api.model.Baseline.MNIST import MNIST_Net
from FedML.fedml_api.model.Baseline.CIFAR10 import CIFAR10_Net
from FedML.fedml_api.model.Baseline.shakespeare import Shakespeare_Net
from FedML.fedml_api.model.Baseline.HAR import HAR_Net
from FedML.fedml_api.model.Baseline.HPWREN import HPWREN_Net

def add_args(parser):
    parser.add_argument('--server_ip', type=str, default="http://127.0.0.1:5000",
                        help='IP address of the FedML server')
    parser.add_argument('--client_uuid', type=str, default="0",
                        help='the ID of the client/gateway')
    args = parser.parse_args()
    return args

def register(args, uuid):
    str_device_UUID = uuid
    URL = args.server_ip + "/api/register"

    # defining a params dict for the parameters to be sent to the API
    PARAMS = {'device_id': str_device_UUID}

    # sending get request and saving the response as response object
    r = requests.post(url=URL, params=PARAMS)
    print(r)
    result = r.json()
    client_ID = result['client_id']
    # executorId = result['executorId']
    # executorTopic = result['executorTopic']
    training_task_args = result['training_task_args']

    class Args:
        def __init__(self):
            self.method = training_task_args['method']
            self.dataset = training_task_args['dataset']
            self.data_dir = training_task_args['data_dir']
            self.result_dir = training_task_args['result_dir']
            self.partition_method = training_task_args['partition_method']
            self.is_preprocessed = training_task_args['is_preprocessed']
            self.partition_alpha = training_task_args['partition_alpha']
            self.partition_secondary = training_task_args['partition_secondary']
            self.partition_min_cls = training_task_args['partition_min_cls']
            self.partition_max_cls = training_task_args['partition_max_cls']
            self.partition_label = training_task_args['partition_label']
            self.data_size_per_client = training_task_args['data_size_per_client']
            # self.D = training_task_args['D']
            self.client_num_per_gateway = training_task_args['client_num_per_gateway']
            self.client_num_in_total = training_task_args['client_num_in_total']
            self.gateway_num_in_total = training_task_args['gateway_num_in_total']
            self.comm_round = training_task_args['comm_round']
            self.gateway_comm_round = training_task_args['gateway_comm_round']
            self.epochs = training_task_args['epochs']
            self.client_optimizer = training_task_args['client_optimizer']
            self.lr = training_task_args['lr']
            self.momentum = training_task_args['momentum']
            self.rou = training_task_args['rou']
            self.batch_size = training_task_args['batch_size']
            self.frequency_of_the_test = training_task_args['frequency_of_the_test']
            self.round_delay_limit = training_task_args['round_delay_limit']
            self.backend = training_task_args['backend']
            self.mqtt_host = training_task_args['mqtt_host']
            self.mqtt_port = training_task_args['mqtt_port']
            self.test_batch_num = training_task_args['test_batch_num']
            self.trial = training_task_args['trial']
            self.alpha = training_task_args['alpha']
            self.staleness_func = training_task_args['staleness_func']
            self.selection = training_task_args['selection']
            self.cs_gamma = training_task_args['cs_gamma']
            self.association = training_task_args['association']
            self.ca_phi = training_task_args['ca_phi']
            self.adjust_round = training_task_args['adjust_round']


    args = Args()
    return client_ID, args

def init_training_device(process_ID, fl_worker_num, gpu_num_per_machine):
    # initialize the mapping from process ID to GPU ID: <process ID, GPU ID>
    if process_ID == 0:
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        return device
    process_gpu_dict = dict()
    for client_index in range(fl_worker_num):
        gpu_index = client_index % gpu_num_per_machine
        process_gpu_dict[client_index] = gpu_index

    logging.info(process_gpu_dict)
    device = torch.device("cuda:" + str(process_gpu_dict[process_ID - 1]) if torch.cuda.is_available() else "cpu")
    logging.info(device)
    return device


def load_data(args, dataset_name):
    if dataset_name == "shakespeare":
        print(
            "============================Starting loading {}==========================#".format(
                args.dataset))
        logging.info("load_data. dataset_name = %s" % dataset_name)
        train_data_num, test_data_num, train_data_global, test_data_global, \
        train_data_local_num_dict, train_data_local_dict, test_data_local_dict, \
        class_num = load_partition_data_shakespeare(args.batch_size, "../FedML/data/shakespeare")
        # args.client_num_in_total = len(train_data_local_dict)
        print(
            "================================={} loaded===============================#".format(
                args.dataset))

    elif dataset_name == "har":
        print(
            "============================Starting loading {}==========================#".format(
                args.dataset))
        logging.info("load_data. dataset_name = %s" % dataset_name)
        train_data_num, test_data_num, train_data_global, test_data_global, \
        train_data_local_num_dict, train_data_local_dict, test_data_local_dict, \
        class_num = load_partition_data_HAR(args.batch_size, "../FedML/data/HAR")
        # args.client_num_in_total = len(train_data_local_dict)
        print(
            "================================={} loaded===============================#".format(
                args.dataset))


    elif dataset_name == "hpwren":
        print(
            "============================Starting loading {}==========================#".format(
                args.dataset))
        logging.info("load_data. dataset_name = %s" % dataset_name)
        train_data_num, test_data_num, train_data_global, test_data_global, \
        train_data_local_num_dict, train_data_local_dict, test_data_local_dict, \
        class_num = load_partition_data_HPWREN(args.batch_size, "../FedML/data/HPWREN")
        # args.client_num_in_total = len(train_data_local_dict)
        print(
            "================================={} loaded===============================#".format(
                args.dataset))


    elif dataset_name == "mnist" or dataset_name == "fashionmnist" or \
            dataset_name == "cifar10":
        data_loader = load_partition_data
        print(
            "============================Starting loading {}==========================#".format(
                args.dataset))
        data_dir = './../data/' + args.dataset
        train_data_num, test_data_num, train_data_global, test_data_global, \
        train_data_local_num_dict, train_data_local_dict, test_data_local_dict, \
        class_num = data_loader(args.dataset, data_dir, args.partition_method,
                                args.partition_label, args.partition_alpha, args.partition_secondary,
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
        model = CIFAR10_Net()
    elif args.dataset == "shakespeare":
        model = Shakespeare_Net()
    elif args.dataset == "har":
        model = HAR_Net()
    elif args.dataset == "hpwren":
        model = HPWREN_Net()
    else:
        print("Invalid dataset")
        exit(0)

    return model




if __name__ == '__main__':
    # parse python script input parameters
    parser = argparse.ArgumentParser()
    main_args = add_args(parser)
    uuid = main_args.client_uuid

    client_ID, args = register(main_args, uuid)
    logging.info("client_ID = " + str(client_ID))
    logging.info("method = " + str(args.method))
    logging.info("dataset = " + str(args.dataset))
    logging.info("client_num_per_gateway = " + str(args.client_num_per_gateway))
    client_index = client_ID - 1

    args.trial_name = "fedml_{}_{}_{}_c{}_c{}_{}_{}_ds{}_{}_{}_{}_e{}_{}_{}_{}".format(
        args.method, args.dataset, args.partition_method,
        args.client_num_in_total, args.client_num_per_gateway,
        args.selection, args.association, args.data_size_per_client,
        args.client_optimizer, args.lr, args.momentum, args.epochs,
        args.comm_round, args.adjust_round, args.trial
    )

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

    logging.info("client_ID = %d, size = %d" % (client_ID, args.client_num_per_gateway))
    device = init_training_device(client_ID - 1, args.client_num_per_gateway - 1, 4)
    # device = torch.device("cudo:0" if torch.cuda.is_available() else "cpu")

    # load data
    dataset = load_data(args, args.dataset)
    [train_data_num, test_data_num, train_data_global, test_data_global,
     train_data_local_num_dict, train_data_local_dict, test_data_local_dict,
     class_num] = dataset

    model = create_model(args)

    model_trainer = MyModelTrainer(model, args, device)
    model_trainer.set_id(client_index)

    # trash
    device = torch.device('cpu')

    # start training
    trainer = BaseCNN_Trainer(client_index, train_data_local_dict,
                              train_data_local_num_dict, test_data_local_dict,
                              train_data_num, device, args, model_trainer)

    size = args.client_num_per_gateway + 1

    print("mqtt port: ", args.mqtt_port)

    # Init results dir - should have already been initialized by server
    #args.result_dir = os.path.join(args.result_dir, args.trial_name)
    # Create the result directory if not exists
    #if not os.path.exists(args.result_dir):
    #    os.makedirs(args.result_dir)

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
    counter = 0

    if args.dataset == 'har':
        for i in range(30):
            batch_selection.append(i)

    else:
        for batch_idx, (x, y) in enumerate(test_data_global):
            if counter >= args.test_batch_num:
                break
            if len(x) == args.batch_size:
                batch_selection.append(batch_idx)
                counter+=1


    logging.info("TestBatch Selection:")
    logging.info(batch_selection)

    # create model.
    # Note if the model is DNN (e.g., ResNet), the training will be very slow.
    # In this case, please use our FedML distributed version (./fedml_experiments/distributed_fedavg)
    model = create_model(args)

    model_trainer = MyModelTrainer(model, args, device)
    model_trainer.set_id("Server")

    aggregator = BaselineCNNAggregator(args, train_data_global, test_data_global, train_data_num,
                                       train_data_local_dict, test_data_local_dict, train_data_local_num_dict,
                                       args.client_num_in_total, device, model_trainer)

    client_manager = BaselineCNNGatewayManager(args,
                                         aggregator,
                                         logger,
                                         rank=client_ID,
                                         size=args.client_num_in_total + 1,
                                         backend="MQTT",
                                         mqtt_host=args.mqtt_host,
                                         mqtt_port=args.mqtt_port,
                                         is_preprocessed=args.is_preprocessed,
                                         batch_selection=batch_selection)

    client_manager.run()

    time.sleep(100000)

