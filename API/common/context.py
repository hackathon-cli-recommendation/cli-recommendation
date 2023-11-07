import logging
import os
import traceback
from datetime import datetime
from functools import wraps

import azure.functions as func
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

exporter = AzureExporter(connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"])


class DependencyCall():
    callName = ""
    request = None
    response = None
    startTime = 0
    endTime = 0
    duration = 0
    usage = None
    exception = None
    telemetryClient = None
    tracer = None

    def __init__(self, callName) -> None:
        self.callName = callName

    def start(self):
        self.startTime = datetime.now()
    
    def end(self, exception = None):
        self.endTime = datetime.now()
        self.duration = (self.endTime - self.startTime).total_seconds()
        logging.info(f"{self.callName} operation time: {self.duration} seconds.")
        if exception is not None:
            self.exception = exception
    
    def toDict(self):
        return {
            "callName": self.callName,
            "startTime": self.startTime.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "endTime": self.endTime.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "duration": self.duration,
            "usage": self.usage,
            "exception": self.exception,
        }


class ContextStatistics():
    callGraph = None

    def __init__(self) -> None:
        self.callGraph = []

    def addCall(self, call: DependencyCall):
        self.callGraph.append(call)
    
    def toDict(self):
        return {
            "callGraph": list(map(lambda call: call.toDict(), self.callGraph))
        }


class OpenAIConfig():
    apiUrl: str  # API url for the Azure OpenAI instance
    apiVersion: str  # API version for the Azure OpenAI
    apiKey: str  # API key for the Azure OpenAI
    gptEngine: str  # GPT engine for the Azure OpenAI model
    embeddingUrl: str  # Embedding url for the Azure OpenAI model

    def __init__(self, apiUrl: str = None, apiVersion: str = None, apiKey: str = None, gptEngine: str = None, embeddingUrl: str = None) -> None:
        if (apiUrl is None):
            self.apiUrl = os.environ.get("OPENAI_API_URL")
        else:
            self.apiUrl = apiUrl
        if (apiVersion is None):
            self.apiVersion = os.environ.get("OPENAI_API_VERSION")
        else:
            self.apiVersion = apiVersion
        if (apiKey is None):
            self.apiKey = os.environ.get("OPENAI_API_KEY")
        else:
            self.apiKey = apiKey
        if (gptEngine is None):
            self.gptEngine = os.environ.get("OPENAI_ENGINE")
        else:
            self.gptEngine = gptEngine
        if (embeddingUrl is None):
            self.embeddingUrl = os.environ.get("EMBEDDING_MODEL_URL")
        else:
            self.embeddingUrl = embeddingUrl
        
    def toDict(self):
        return {
            "apiUrl": self.apiUrl,
            "apiVersion": self.apiVersion,
            "gptEngine": self.gptEngine,
            "embeddingUrl": self.embeddingUrl
        }


class Context():
    statistics = None
    originalCall: DependencyCall = DependencyCall("OriginalCall")
    functionOperationId: str
    functionInvocationId: str
    applicationInsightsId: str
    openaiConfig: OpenAIConfig = None
    tracer = None
    method = None
    endpoint = None

    def __init__(self, functionOperationId: str, functionInvocationId: str, openaiConfig: OpenAIConfig) -> None:
        self.functionOperationId = functionOperationId
        self.functionInvocationId = functionInvocationId
        self.statistics = ContextStatistics()
        self.openaiConfig = openaiConfig

    def calculateUsage(self):
        totalUsage = {}
        for call in self.statistics.callGraph:
            usage = call.usage
            if usage is None:
                continue
            model = usage.get('model', None)
            if model is None:
                model = "None"
            if model not in totalUsage:
                totalUsage[model] = {
                    'completion_tokens': 0,
                    'prompt_tokens': 0,
                    'total_tokens': 0,
                }
            modelUsage = totalUsage[model]
            modelUsage['completion_tokens'] += usage.get('completion_tokens', 0)
            modelUsage['prompt_tokens'] += usage.get('prompt_tokens', 0)
            modelUsage['total_tokens'] += usage.get('total_tokens', 0)
        self.originalCall.usage = totalUsage

    def toDict(self):
        return {
            "method": self.method,
            "endpoint": self.endpoint,
            "statistics": self.statistics.toDict(),
            "originalCall": self.originalCall.toDict(),
            "functionOperationId": self.functionOperationId,
            "functionInvocationId": self.functionInvocationId,
            "applicationInsightsId": self.applicationInsightsId
        }

def log_dependency_call(callName):
    def decorate(func):
        @wraps(func)
        def innerFunc(*args, **kwargs):
            context = args[0].custom_context
            dependencyCall = DependencyCall(callName)
            dependencyCall.start()
            try:
                tracer = context.tracer
                with tracer.span(name=callName) as span:
                    span.add_attribute("name", callName)
                    response = func(*args, **kwargs)
                    if 'usage' in response:
                        dependencyCall.usage = response['usage']
                        for key, value in response['usage'].items():
                            span.add_attribute(f"{key}", value)
            except Exception as e:
                logging.error(e)
                tracebackStr = traceback.format_exc()
                dependencyCall.end(exception=tracebackStr)
                if context is not None:
                    context.statistics.addCall(dependencyCall)
                raise e
            dependencyCall.end()
            if context is not None:
                context.statistics.addCall(dependencyCall)
            return response
        return innerFunc
    return decorate

def log_dependency_call_async(callName):
    def decorate(func):
        @wraps(func)
        async def innerFunc(*args, **kwargs):
            context = args[0].custom_context
            dependencyCall = DependencyCall(callName)
            dependencyCall.start()
            try:
                tracer = context.tracer
                with tracer.span(name=callName) as span:
                    span.add_attribute("name", callName)
                    response = await func(*args, **kwargs)
                    if 'usage' in response:
                        dependencyCall.usage = response['usage']
                        for key, value in response['usage'].items():
                            span.add_attribute(f"{key}", value)
            except Exception as e:
                logging.error(e)
                tracebackStr = traceback.format_exc()
                dependencyCall.end(exception=tracebackStr)
                if context is not None:
                    context.statistics.addCall(dependencyCall)
                raise e
            dependencyCall.end()
            if context is not None:
                context.statistics.addCall(dependencyCall)
            return response
        return innerFunc
    return decorate


def init_custom_context(request: func.HttpRequest, functionOperationId: str, functionInvocationId: str):
    openaiConfig = OpenAIConfig()
    context = Context(functionOperationId, functionInvocationId, openaiConfig)
    context.tracer = Tracer(exporter=exporter, sampler=ProbabilitySampler(1.0))
    context.applicationInsightsId = context.tracer.tracer.trace_id
    context.method = request.method
    context.endpoint = request.url
    return context
