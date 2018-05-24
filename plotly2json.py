

def plotlyfig2json(fig, fpath=None):
    #import numpy as np
    import json
    from plotly.utils import PlotlyJSONEncoder
    from plotly.offline import download_plotlyjs, plot
    import plotly.graph_objs as go
    """
    Serialize a plotly figure object to JSON so it can be persisted to disk.
    Figure's persisted as JSON can be rebuilt using the plotly JSON chart API:

    http://help.plot.ly/json-chart-schema/

    If `fpath` is provided, JSON is written to file.

    Modified from https://github.com/nteract/nteract/issues/1229
    """

    redata = json.loads(json.dumps(fig.data, cls=PlotlyJSONEncoder))
    relayout = json.loads(json.dumps(fig.layout, cls=PlotlyJSONEncoder))

    fig_json=json.dumps({'data': redata,'layout': relayout})

    if fpath:
        with open(fpath, 'w') as f:
            f.write(fig_json)
    else:
        return fig_json

def plotlyfromjson(fpath):
    #import numpy as np
    import json
    from plotly.utils import PlotlyJSONEncoder
    from plotly.offline import download_plotlyjs, plot
    import plotly.graph_objs as go
    """Render a plotly figure from a json file"""
    import os
    with open(fpath, 'r') as f:
        v = json.loads(f.read())
    fig = go.Figure(data=v['data'], layout=v['layout'])
    fpath2=os.path.splitext(fpath)[0]
    htmlname=fpath2+'.html'
    plot(fig, show_link=False,filename=htmlname, auto_open=False)
    return htmlname