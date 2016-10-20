from kostyor.rpc.app import app


@app.task
def noop():
    pass
