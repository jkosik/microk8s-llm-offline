# LLM in offline mode on MicroK8S

This project addresses offline deployment of LLM (Large Language Model) in Kubernetes using a self-contained Helm Chart.
Project uses Ubuntu,  MicroK8S and LLM with TGI (Text Generation Inference) support. Minimalistic [google/flan-t5-base](https://huggingface.co/google/flan-t5-base) LLM was selected.

Deployment was tested on mid-range laptop without GPU support. Code can be easily adjusted to run on any Kubernetes cluster with GPU support.

## Deployment
1. **Install MicroK8S**
```
sudo snap remove --purge microk8s
sudo snap install microk8s --classic
microk8s enable hostpath-storage dns ingress
microk8s config > ~/.kube/config
```
2. **Deploy Helm Chart**
```
cd /helm
helm upgrade --install microk8s-llm-offline .
```

3. **Query the model**  
TGI API is exposed via K8S Ingress. FQDN is defined in Helm `values.yaml` as `ingress.host` key. Update your `/etc/hosts` to resolve the FQDN to `127.0.0.1`.
```
curl http://llm-api.mydom.com/generate \
-X POST \
-d '{"inputs":"Translate English to German: How old are you?"}' \
-H 'Content-Type: application/json'
```

There are also further endpoints available:
```
curl http://llm-api.mydom.com/info
curl http://llm-api.mydom.com/metrics
```

Alternatively query the model via port-forwarded K8S Service.  
See [google/flan-t5-base](https://huggingface.co/google/flan-t5-base) details to understand the model and type of questions to ask.

## Further considerations
#### Mind various MicroK8S bugs and issues
- If your IP address changes, TLS verification error may appear and MicroK8S may need to re-issue TLS certificates (see below).
- If Helm complains on TLS validation, ensure your kubeconfig `server` address points to your external interface IP address and not `127.0.0.1`.  
Re-created MicroK8S config by `microk8s config view > ~/.kube/config` and omit `-l` flag.
- If pulling `ghcr.io/huggingface/text-generation-inference` image takes a lot of time and Pod is in Pending state for more than 10 minutes, pull image directly on MicroK8S node by: `microk8s ctr images pull ghcr.io/huggingface/text-generation-inference:1.4.0` and restart the pending Pod.

#### Test offline mode. 
Once Deployment finishes and no further in-K8S calls are needed, simply stop egress communication and model should be still responsive.
```
# Disable egress
sudo iptables -A OUTPUT -j DROP -o [YOUR INTERFACE]

# Re-enable egress
sudo iptables -D OUTPUT -j DROP -o [YOUR INTERFACE]
```

#### Model storage
K8S StorageClass defines where K8S Persistent Volume stores LLM data. In our case it is `/opt/microk8s/PVC_NAME/`.  
If StorageClass is not defined, data end up in the default location in `/var/snap/microk8s/common/default-storage/`


#### Pull fresh LLM
1. Delete pull Job
2. Delete TGI Deployment
3. Re-deploy Helm Chart

#### Re-issue MicroK8S TLS certificates
```
sudo microk8s refresh-certs -e ca.crt
sudo microk8s refresh-certs -e server.crt
sudo microk8s refresh-certs -e front-proxy-client.crt
microk8s stop
microk8s start
```

If it does not help, add YOUR_EXTERNAL_IP to `/var/snap/microk8s/current/certs/csr.conf.template`
```
[ req ]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C = GB
ST = Canonical
L = Canonical
O = Canonical
OU = Canonical
CN = 127.0.0.1

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = kubernetes
DNS.2 = kubernetes.default
DNS.3 = kubernetes.default.svc
DNS.4 = kubernetes.default.svc.cluster
DNS.5 = kubernetes.default.svc.cluster.local
IP.1 = 127.0.0.1
IP.2 = 10.152.183.1
#MOREIPS
IP.100 = YOUR_EXTERNAL_IP


[ v3_ext ]
authorityKeyIdentifier=keyid,issuer:always
basicConstraints=CA:FALSE
keyUsage=keyEncipherment,dataEncipherment,digitalSignature
extendedKeyUsage=serverAuth,clientAuth
subjectAltName=@alt_names
```
  
Restart MicroK8S:
```
microk8s stop
microk8s start
```

## Docker and online LLM usage
This section describes simplified use case of using Docker and online TGI LLM usage.  
More info: https://github.com/huggingface/text-generation-inference/blob/main/README.md#get-started

```
model=google/flan-t5-base
volume=$PWD/data

sudo docker run --shm-size 1g -p 8080:80 -v $volume:/data ghcr.io/huggingface/text-generation-inference:latest --model-id $model

curl 127.0.0.1:8080/generate \
-X POST \
-d '{"inputs":"Translate English to German: How old are you?"}' \
-H 'Content-Type: application/json'
```

When using private LLM models from Hugging Face, register, get `read` token and export as `token=YOUR_READ_TOKEN` and extend the `docker` command by `-e HUGGING_FACE_HUB_TOKEN=$token`.