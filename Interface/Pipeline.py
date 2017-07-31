from Interface import PipelineComponents, utility
import pickle
import simplejson as json
import jsonpickle
from decimal import Decimal
import numpy
import pandas

srvname = ""
def init(self, srvname):
    self.srvname = srvname
    PipelineComponents.init(PipelineComponents, srvname)

def getPipelineData():
    pipelineFile = PipelineComponents.projectfolder + '/pipeline.json'
    pipelinedata = utility.getFileData(pipelineFile)
    pipelinejson = json.loads(pipelinedata)
    return pipelinejson

def Run():
    pickleFile = PipelineComponents.projectfolder + '/pipeline.out'
    pipelinejson = getPipelineData()
    resultset = {}

    for p in pipelinejson:
        name = p['name']
        module = p['module']
        if module == "return_result":
            continue

        input = {}
        if "input" in p:
            input = p['input']
        func = getattr(PipelineComponents, module)
        args = {}
        for i in input:
            inputValue = input[i]
            if "output->" in inputValue:
                args[i] = resultset[inputValue]
                continue

            args[i] = inputValue

        args['pipeline'] = p
        output = func(**args)

        if type(output) is tuple:
            count = 0
            for t in output:
                resultset["output->" + name + "->" + str(count)] = t
                count = count + 1
        else:
            resultset["output->" + name] = output

    with open(pickleFile, "wb") as f:
        pickle.dump(resultset, f)

def Predict(filename, savePrediction = False):
    PipelineComponents.init(PipelineComponents, srvname)
    pipelinefile = PipelineComponents.projectfolder + '/pipeline.json'
    pipelinedata = utility.getFileData(pipelinefile)
    pipelinejson = json.loads(pipelinedata)
    resultset = {}
    initialX = []

    for p in pipelinejson:
        name = p['name']
        module = p['module']
        input = {}
        if module == "data_loadcsv":
            p["input"]["filename"] = filename

        if module == "data_handlemissing" or module == "data_filtercolumns":
            continue

        if "input" in p:
            input = p['input']

        if module == "data_getxy":
            module = "data_getx"

        if "model_" in module:
            if module != "model_fit" and module != "model_train":
                continue
            else:
                if module == "model_train":
                    input['mlp'] = "true"
                module = "model_predict"
                name = "model_predict"
                del input["model"]
                del input["Y"]

        args = {}
        if module == "data_featureselection" or module == "data_featureselection_withestimator":
            module = "data_getfeatures"
            args['result'] = Output(name, 2)

        func = getattr(PipelineComponents, module)

        for i in input:
            inputValue = input[i]
            if "output->" in inputValue:
                args[i] = resultset[inputValue]
                continue

            args[i] = inputValue

        args['pipeline'] = p
        output = func(**args)
        if type(output) is tuple:
            count = 0
            for t in output:
                resultset["output->" + name + "->" + str(count)] = t
                count = count + 1
        else:
            resultset["output->" + name] = output

        if module == "data_loadcsv":
            initialX = output

    predictions = resultset["output->model_predict"]

    if savePrediction is True:
        initialX['result'] = predictions
        initialX.to_csv(PipelineComponents.projectfolder + "/dataset/predictions.csv")
    return predictions

def ContinueTraining(epoches=25, batch_size=32):
    PipelineComponents.init(PipelineComponents, srvname)
    pipelineFile = PipelineComponents.projectfolder + '/pipeline.json'
    pickleFile = PipelineComponents.projectfolder + '/pipeline.out'
    pipelinedata = utility.getFileData(pipelineFile)
    pipelinejson = json.loads(pipelinedata)
    resultset = {}
    for p in pipelinejson:
        name = p['name']
        module = p['module']
        input = {}

        if "input" in p:
            input = p['input']

        if module == "model_train":
            p['options']['epoches'] = epoches
            p['options']['batch_size'] = batch_size
            input['more'] = "true"
        func = getattr(PipelineComponents, module)
        args = {}
        for i in input:
            inputValue = input[i]
            if "output->" in inputValue:
                args[i] = resultset[inputValue]
                continue

            args[i] = inputValue

        args['pipeline'] = p
        output = func(**args)

        if type(output) is tuple:
            count = 0
            for t in output:
                resultset["output->" + name + "->" + str(count)] = t
                count = count + 1
        else:
            resultset["output->" + name] = output

    with open(pickleFile, "wb") as f:
        pickle.dump(resultset, f)

def Output(name, num = None, to_json=False):
    PipelineComponents.init(PipelineComponents, srvname)
    result = PipelineComponents.return_result(name, num)
    #if to_json is True:
    #    if type(result) is numpy.ndarray:
    #        result = pandas.DataFrame(result).to_json()
    #    elif type(result) is dict:
    #        formatted_result = {}
    #        for r in result:
    #            t = type(result[r])
    #            if t is numpy.ndarray:
    #                formatted_result[r] = pandas.DataFrame(result[r]).to_json()
    #            if t is list:
    #                formatted_result[r] = jsonpickle.encode(result[r], unpicklable=False)
    #            else:
    #                formatted_result[r] = result[r]

    #        result = formatted_result
    return jsonpickle.encode(result, unpicklable=False)