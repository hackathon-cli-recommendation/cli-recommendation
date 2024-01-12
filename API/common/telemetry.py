import json
import logging
import os
import traceback
from functools import wraps

import azure.functions as functions
from common.context import init_custom_context

enable_local_log = os.environ.get('ENABLE_LOCAL_LOG_PERFORMANCE', False)


def telemetry(func):
    @wraps(func)
    def innerFunc(*args, **kwargs):
        context = kwargs['context']
        if not hasattr(context, 'custom_context'):
            functionOperationId = context.trace_context.Traceparent.split('-')[1]
            functionInvocationId = context.invocation_id
            context.custom_context = init_custom_context(kwargs['req'], functionOperationId, functionInvocationId)
        context.custom_context.originalCall.start()
        kwargs['context'] = context
        tracer = context.custom_context.tracer
        method = context.custom_context.method
        endpoint = context.custom_context.endpoint
        endpointName = f"{method} {endpoint}"
        try:
            with tracer.span(name=endpointName) as span:
                response = func(*args, **kwargs)
            context.custom_context.originalCall.end()
            if response.status_code == 200:
                context.custom_context.responseEmpty = len(json.loads(response.get_body())['data']) == 0
            context.custom_context.responseStatus = response.status_code
            return response
        except Exception as e:
            context.custom_context.responseEmpty = True
            logging.error(f'Fatal Error: {str(e)}', exc_info=e)
            tracebackStr = traceback.format_exc()
            context.custom_context.originalCall.end(exception=tracebackStr)
            context.custom_context.responseStatus = 500
            return functions.HttpResponse(f'Fatal Error: {str(e)}', status_code=500)
        finally:
            with tracer.span(name=endpointName) as span:
                span.add_attribute("ResponseStatus", context.custom_context.responseStatus)
                span.add_attribute("ResponseEmpty", context.custom_context.responseEmpty)
            context.custom_context.calculateUsage()
            if enable_local_log:
                startTime = context.custom_context.originalCall.startTime.strftime("%Y%m%d-%H%M%S")
                logPath = os.path.join('logs', f"{startTime}-{context.custom_context.applicationInsightsId}.json")
                if not os.path.exists('logs'):
                    os.makedirs('logs')
                with open(logPath, "w") as outfile:
                    json.dump(context.custom_context.toDict(), outfile, indent=2)
            # use application insights id to get detailed records of the request
            # use function id to get more detailed records of the request
            # but if you want to query application insights database then application insights id is the only option
            logging.info(f"functionOperationId={context.custom_context.functionOperationId}, functionInvocationId={context.custom_context.functionInvocationId}, applicationInsightsId={context.custom_context.applicationInsightsId}")

    return innerFunc

