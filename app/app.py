from flask import Flask, jsonify, render_template
from kubernetes import client, config

app = Flask(__name__)

config.load_incluster_config()
v1 = client.CoreV1Api()

def get_pods():
    pods = v1.list_pod_for_all_namespaces()
    return [{"name": p.metadata.name, "namespace": p.metadata.namespace, "status": p.status.phase} for p in pods.items]

def get_nodes():
    nodes = v1.list_node()
    return [{"name": n.metadata.name, "status": n.status.conditions[-1].type} for n in nodes.items]

@app.route("/")
def dashboard():
    return render_template("dashboard.html", pods=get_pods(), nodes=get_nodes())

@app.route("/pods")
def list_pods():
    return jsonify(get_pods())

@app.route("/nodes")
def list_nodes():
    return jsonify(get_nodes())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)