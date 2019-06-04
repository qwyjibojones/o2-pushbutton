#!/usr/bin/env python3

# https://opendistro.github.io/for-elasticsearch-docs/docs/alerting/api/

import json
import requests
import os

# Env vars Set by the Jenkins pipeline

username = os.environ["ES_USERNAME"]
password = os.environ["ES_PASSWORD"]
deployment_name = os.environ["OMAR_DEPLOYMENT"]

es_host = "http://es-cluster.es-stack.svc.cluster.local:9200"
endpoint = "http://nifi.omar-dev.svc.cluster.local:8081/alert"

destination_id = str()

log_level = 5


def post(body, path):
    global es_host

    if path.startswith("/"):
        path = path[1:]

    if not es_host.endswith("/"):
        es_host = es_host + "/"

    debug("Sending POST to {}{}".format(es_host, path), 1)
    resp = requests.post(url=es_host + path, data=str(body), auth=(username, password))
    debug("-> Response: {} {}".format(resp.status_code, resp.content), 1)

    return json.loads(resp.content)


def create_monitor(name, query):

    body = {
        "name": deployment_name+" "+name,
        "type": "monitor",
        "enabled": True,
        "schedule": {
            "period": {
                "interval": 1,
                "unit": "MINUTES"
            }
        },
        "inputs": [{
            "search": {
                "indices": ["o2-filebeat-{}-*".format(deployment_name)],
                "query": query
            }
        }],
        "triggers": []
    }

    return post(body, "_opendistro/_alerting/monitors")


def add_triggers_to_monitor(monitor_id, triggers_json):

    return post(triggers_json, "_opendistro/_alerting/monitors/" + monitor_id)


def create_destination(name, dest_type):

    body = {
        "name": name,
        "type": dest_type,
        dest_type: {
            endpoint
        }
    }

    return post(body, "_opendistro/_alerting/destinations")


def create_http_monitor(lower, upper):
    """
    :type lower: int
    :type upper: int
    """

    http_monitor_name = "http {}-{} (last 10min)".format(str(lower), str(upper))

    http_monitor_query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "httpStatus": {
                                "from": lower,
                                "to": upper,
                                "include_lower": True,
                                "include_upper": True
                            }
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "from": "now-10m",
                                "to": "now",
                                "include_lower": True,
                                "include_upper": True
                            }
                        }
                    }
                ]
            }
        }
    }

    return create_monitor(http_monitor_name, http_monitor_query)


def create_slowness_monitor(slowness_monitor_name, slowness_threshold):

    slowness_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "response_time": {
                                "gte": slowness_threshold
                            }
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "from": "now-1m",
                                "to": "now",
                                "include_lower": True,
                                "include_upper": True
                            }
                        }
                    }
                ]
            }
        }
    }

    return create_monitor(slowness_monitor_name, slowness_query)


def add_trigger_json(trigger_name, trigger_severity, trigger_predicate, action_jsons):
    """

    :type action_jsons: list
    """
    return {
        "triggers": [{
            "name": trigger_name,
            "severity": trigger_severity,
            "condition": {
                trigger_predicate
            },
            "actions": action_jsons
        }]
    }


def action_json(action_name, action_subject, action_message):

    return {
        "name": action_name,
        "destination_id": destination_id,
        "subject_template": {
            "source": action_subject,
            "lang": "mustache"
        },
        "message_template": {
            "source": action_message,
            "lang": "mustache"
        }
    }


def debug(message, msg_level):
    if msg_level < log_level:
        print(message)


def main():

    # Create Kibana Alert "Destination"

    global destination_id
    resp = create_destination("http webhook", "custom_webhook")
    destination_id = resp["_id"]

    # Install Monitors w/ triggers

    create_4xx_monitor()

    create_5xx_monitor()

    create_lag_monitor()


def create_4xx_monitor():

    response = create_http_monitor(400, 499)
    monitor_id = response["_id"]

    name = "({}) Excessive 4xx errors".format(deployment_name)
    notify_action = action_json(name, name, "msg")
    count_trigger = add_trigger_json(name, 1, "ctx.results[0].hits.total > 20", action_jsons=[notify_action])
    add_triggers_to_monitor(monitor_id, count_trigger)


def create_5xx_monitor():

    response = create_http_monitor(500, 599)
    monitor_id = response["_id"]

    name = "({}) Excessive 5xx errors".format(deployment_name)
    notify_action = action_json(name, name, "msg")
    count_trigger = add_trigger_json(name, 1, "ctx.results[0].hits.total > 5", action_jsons=[notify_action])
    add_triggers_to_monitor(monitor_id, count_trigger)


def create_lag_monitor():

    add_lag_monitor_response = create_slowness_monitor("slow response monitor", 2000)
    monitor_id = add_lag_monitor_response["._id"]

    name = "{} Excessive responsive times".format(deployment_name)
    notify_action = action_json(name, name, "msg")
    count_trigger = add_trigger_json(name, 1, "ctx.results[0].hits.total > 3", action_jsons=[notify_action])
    add_triggers_to_monitor(monitor_id, count_trigger)


if "__main__" == __name__:
    main()
