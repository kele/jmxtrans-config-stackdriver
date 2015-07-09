#! /usr/bin/python

MBEAN_TEMPLATE = """
        <MBean "{MBean}">
            ObjectName "{ObjectName}"
            InstancePrefix "{InstancePrefix}"
            {ValuesString}
        </MBean>

"""

VALUE_TEMPLATE = """
            <Value>
                Attribute "{Attribute}"
                InstancePrefix "{Attribute}"
                Type "gauge"
                Table false
            </Value>"""

CONFIG_TEMPLATE = """
<Plugin "java">
    JVMARG "{JVMARG}"
    LoadPlugin "org.collectd.java.GenericJMX"

    <Plugin "GenericJMX">
{MBeans}

        <Connection>
            Host "{Host}"
            ServiceURL "{ServiceURL}"
{WhatToCollect}
        </Connection>
    </Plugin>
</Plugin>
"""

COLLECT_TEMPLATE = """
            Collect "{MBean}" """

SERVICEURL_TEMPLATE = "service:jmx:rmi:///jndi/rmi://{host}:{port}/jmxrmi"

import json

def convert_query(q):
    obj = q["obj"]
    alias = q["resultAlias"].replace(".", "_")

    return {"ObjectName" : obj,
            "MBean" : alias,
            "Values" : q["attr"],
            "InstancePrefix" : alias}


def encode_value(attribute):
    return VALUE_TEMPLATE.format(Attribute=attribute)

def encode_query(genericjmx_query):
    values_string = ''.join([encode_value(v) for v in genericjmx_query["Values"]])
    return MBEAN_TEMPLATE.format(ValuesString=values_string, **genericjmx_query)


def convert(server, queries, options):
    jmxtrans_queries = queries
    genericjmx_queries = [convert_query(q) for q in jmxtrans_queries]
    encoded_queries = [encode_query(q) for q in genericjmx_queries]

    what_to_collect = ''.join([COLLECT_TEMPLATE.format(MBean=q["MBean"]) for q in genericjmx_queries])
    service_url = SERVICEURL_TEMPLATE.format(**server)
    options["Host"] = server["host"]

    return CONFIG_TEMPLATE.format(MBeans=''.join(encoded_queries),
                                  WhatToCollect=what_to_collect,
                                  ServiceURL=service_url,
                                  **options)



def generate(template, options):
    return convert(server=template["serverInfo"],
                   queries=template["queryInfos"],
                   options=options)


