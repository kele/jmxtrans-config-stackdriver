#! /usr/bin/python

MBEAN_TEMPLATE = """
        <MBean "{MBean}">
            ObjectName "{ObjectName}"
            InstancePrefix "{InstancePrefix}"
            <Value>
                Type "{InstancePrefix}"
                Table false
                {ValuesList}
            </Value>

        </MBean>

"""

VALUE_TEMPLATE = """
                Attribute "{Attribute}" """

CONFIG_TEMPLATE = """
# Look for {host} and {port} to adjust your configuration file.
<Plugin "java">
    JVMARG "{JVMARG}"
    LoadPlugin "org.collectd.java.GenericJMX"

    <Plugin "GenericJMX">
{MBeanList}

        <Connection>
            Host "{Host}"
            ServiceURL "{ServiceURL}"
{CollectList}
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
            "Attributes" : q["attr"],
            "InstancePrefix" : alias}


def encode_value(attribute):
    return VALUE_TEMPLATE.format(Attribute=attribute)

def encode_type(name, attributes):
    attr_with_types = [ attr["name"] + ":" + attr["type"] for attr in attributes ]
    return name + "\t" + ', '.join(attr_with_types)

def encode_query(genericjmx_query):
    values_string = ''.join([encode_value(v["name"]) for v in genericjmx_query["Attributes"]])
    value_type = genericjmx_query["InstancePrefix"]

    return { "conf" : MBEAN_TEMPLATE.format(ValuesList=values_string, **genericjmx_query),
             "type" : encode_type(value_type, genericjmx_query["Attributes"]) }


def convert(server, queries, options):
    jmxtrans_queries = queries
    genericjmx_queries = [convert_query(q) for q in jmxtrans_queries]
    encoded_queries = [encode_query(q) for q in genericjmx_queries]

    what_to_collect = ''.join([COLLECT_TEMPLATE.format(MBean=q["MBean"]) for q in genericjmx_queries])
    service_url = SERVICEURL_TEMPLATE.format(**server)
    options["Host"] = server["host"]
    options["host"] = server["host"]
    options["port"] = server["port"]

    conf = CONFIG_TEMPLATE.format(MBeanList=''.join([q["conf"] for q in encoded_queries]),
                                              CollectList=what_to_collect,
                                              ServiceURL=service_url,
                                              **options)
    conf = '\n'.join([line.rstrip() for line in conf.splitlines()])
    return { "conf" : conf,
             "types" : '\n'.join([q["type"] for q in encoded_queries]) }



def generate(template, options):
    return convert(server=template["serverInfo"],
                                   queries=template["queryInfos"],
                                   options=options)



