#!/usr/bin/env python

from collections import OrderedDict
import copy
import json
import os
import sys

import differ

def generate(template, options):
    """Transform 'template' into a data structure suitable for consumption by
    jmxtrans.

    This method transforms the 'template' object into the expected output
    format by changing the data structure and substituting 'url', 'source',
    and 'detectInstance' at the appropriate locations.

    The method is parameterized in this way because the program generates
    four different output files, each parameterized in a slightly different way.
    See the doc comments for the 'main' for more information.

    ARGUMENTS:

    template - The input data structure. Its type is described below.

    url - The Gateway string to be embedded in the output (this is either the
          Stackdriver or the Google gateway).

    source - The "source" property of the settingsDict (this is either the
             string "AWS_INSTANCE_ID" or "GCE_INSTANCE_ID". Note that these
             strings are themselves placeholders, as the human being ultimately
             consuming these JSON files is expected to put something there.

    detectInstance - The "detectInstance" property of the settingsDict (this is
        either the string "AWS" or the string "GCE").

    Exactly one of 'source' and 'detectInstance' will be None.

    'template' is expected to have the following dictionary type:
    {
        "serverInfo": ServerInfo,
        "queryInfos": [ QueryInfo, ... ]  # One or more QueryInfos
    }

    The 'ServerInfo' type is defined as the following dictionary type:
    {
        # ServerInfo properties. The contents of serverInfo are opaque to
        # this program and can therefore be arbitrary. However in practice
        # the properties currently used in all of our cases are:
        "port": Number
        "host": String
        "numQueryThreads": Number
    },

    The 'QueryInfo' type is defined as the following dictionary type:
    {
        # Bean name, e.g. "jboss.web:type=ThreadPool,name=*".
        "obj": String

        # Alias used by upstream processing, e.g. "jboss.threads".
        "resultAlias": String

        # Array of JMX attributes, e.g.:
        # [ "currentThreadCount","currentThreadsBusy" ]
        "attr": [Attribute, ...]

        # Optional JMX typeNames array:
        # e.g. "typeNames": [ "name" ]
        "typeNames"?: [String,...]
    },


    RESULT:

    The result produced is a dictionary type in the following format:
    {
        "servers": [Server]  # Always only one Server
    }

    'Server' is a dictionary type in the following format:
    {
        # All properties copied over from template["serverInfo"], defined above.
        # Plus, an additional property called "queries", an array of Query.
        "queries": [ Query, ...]
    }

    'Query' is a dictionary type in the following format:
    {
        # The values for these three properties are copied directly from the
        # corresponding place in the 'template' object.
        "obj": String,  # JMX object
        "resultAlias": String,
        "attr": [String,...],  # attributes

        # There is one more property whose type is defined below.
        "outputWriters": [OutputWriter]  # A single OutputWriter
    }

    'OutputWriter' is a dictionary type in the following format:
    {
        "@class": "com.googlecode.jmxtrans.model.output.StackdriverWriter",
        "settings": Settings
    }

    'Settings' is a dictionary type in the following format
    {
        "token": "STACKDRIVER_API_KEY",

        # The value of "url" comes from the 'url' argument to this method.
        "url": String,

        # The value of the (optional) "detectInstance" property comes from the
        # 'detectInstance' argument to this method.
        "detectInstance"?: String,

        # The value of the (optional) "source" property comes from the 'source'
        # argument to this method.
        "source"?: String,

        # The value of the (optional) "typeNames" property comes from the
        # QueryInfo.typeNames property above.
        "typeNames"?: [String, ...]
    }
"""
    url = options["url"]
    source = options["source"]
    detectInstance = options["detectInstance"]

    assert len(template) == 2, (
        "Dictionary has {0} keys, expected 2.".format(len(template)))
    serverInfo = template["serverInfo"]
    queryInfos = template["queryInfos"]

    queries = []
    for qi in queryInfos:
        # First check for unexpected properties.
        expectedProperties = {"obj", "resultAlias", "attr", "typeNames"}
        for key in qi:
            if key not in expectedProperties:
                raise ValueError(
                    "Unexpected key " + key + " found in queryInfos")

        # There are three required entries and one optional one.
        obj = qi["obj"]
        attr = qi["attr"]
        resultAlias = qi["resultAlias"]
        typeNames = qi["typeNames"] if "typeNames" in qi else None

        # Build the query element that we are outputting, starting with the
        # nested settingsDict.
        settingsDict = OrderedDict()
        settingsDict["token"] = u"STACKDRIVER_API_KEY"
        settingsDict["url"] = url
        if source is not None:
            settingsDict["source"] = source
        if detectInstance is not None:
            settingsDict["detectInstance"] = detectInstance
        if typeNames is not None:
            settingsDict["typeNames"] = typeNames

        # Next, go out one level and build the outputWriters array, which always
        # contains a single outputWriterDict.
        outputWriterDict = OrderedDict()
        outputWriterDict["@class"] = (
            u"com.googlecode.jmxtrans.model.output.StackdriverWriter")
        outputWriterDict["settings"] = settingsDict
        outputWriters = [outputWriterDict]

        # Finally go out one more level and build the query element, which
        # contains (obj, attr, resultAlias, and outputWriters)
        query = OrderedDict()
        query["obj"] = obj
        query["attr"] = [a["name"] for a in attr]
        query["resultAlias"] = resultAlias
        query["outputWriters"] = outputWriters
        queries.append(query)

    # Now build the serverDict which has all the properties of serverInfo, plus
    # the queries array.
    serverDict = copy.deepcopy(serverInfo)
    serverDict["queries"] = queries
    servers = [serverDict]

    # Finally, build the result.
    result = OrderedDict()
    result["servers"] = servers
    return json.dumps(result, indent=2, separators=(',', ': '))

