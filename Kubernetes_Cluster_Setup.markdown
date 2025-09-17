# Setting Up a Kubernetes Cluster with Calico on CentOS 8

This guide provides step-by-step instructions to set up a high-availability Kubernetes cluster with 3 master nodes and 2 worker nodes using Calico as the CNI on CentOS 8.

## Prerequisites

### Hardware/VM Requirements
- **3 Master Nodes (Control-Plane)**: Minimum 2 GB RAM, 2 CPUs, 20 GB disk each.
- **2 Worker Nodes**: Minimum 2 GB RAM, 2 CPUs, 20 GB disk each.
- **Network Setup**:
  - All nodes on the same network (e.g., `192.168.1.0/24`).
  - Example IPs/Hostnames:
    - Master1: `k8s-master-1` (192.168.43.165)
    - Master2: `k8s-master-2` (192.168.43.169)
    - Master3: `k8s-master-3` (192.168.43.170)
    - Worker1: `k8s-worker-1` (192.168.43.171)
    - Worker2: `k8s-worker-2` (192.168.43.172)
    - Load Balancer VIP: `vip-k8s-master` (192.168.1.173)
  - Firewall ports: 6443 (API server), 2379-2380 (etcd), 10250-10252 (Kubelet), 179 (Calico BGP), 4789 (VXLAN, optional), 30000-32767 (NodePorts).
- **Access**: SSH as root or sudo user.
- **System Prep**:
  - Disable SELinux: `setenforce 0` and edit `/etc/selinux/config` to `SELINUX=permissive`.
  - Disable swap: `swapoff -a` and comment out swap in `/etc/fstab`.
  - Install NTP: `dnf install -y chrony` and `systemctl enable --now chronyd`.

### Software Versions
- Kubernetes: v1.30.x
- Container Runtime: containerd 1.7.x
- Calico: v3.27.x

Run all commands as root unless specified.

## Step 1: Prepare All Nodes (Masters and Workers)

Execute these on **all 5 nodes**.

1. **Update the system**:
   ```bash
   dnf update -y
   ```

2. **Install required packages**:
   ```bash
   dnf install -y iproute-tc conntrack-tools iptables curl wget
   ```

3. **Load kernel modules**:
   ```bash
   modprobe overlay
   modprobe br_netfilter
   ```

4. **Configure sysctl**:
   ```bash
   cat <<EOF > /etc/sysctl.d/k8s.conf
   net.bridge.bridge-nf-call-ip6tables = 1
   net.bridge.bridge-nf-call-iptables = 1
   net.ipv4.ip_forward = 1
   EOF
   sysctl --system
   ```

5. **Set hostnames** (adjust per node):
   ```bash
   hostnamectl set-hostname k8s-master-1  # Example for Master1
   ```

6. **Update /etc/hosts** on all nodes:
   ```bash
   cat <<EOF >> /etc/hosts
   192.168.43.165 k8s-master-1
   192.168.43.169 k8s-master-2
   192.168.43.170 k8s-master-3
   192.168.1.171 k8s-worker-1
   192.168.1.172 k8s-worker-2
   192.168.1.173 vip-k8s-master
   EOF
   ```

## Step 2: Set Up Load Balancer for HA

Use a dedicated CentOS 8 VM (IP: 192.168.1.45) for HAProxy + Keepalived.

1. **Install HAProxy and Keepalived**:
   ```bash
   dnf install -y haproxy keepalived
   ```

2. **Configure HAProxy** (`/etc/haproxy/haproxy.cfg`):
   ```bash
   cat <<EOF > /etc/haproxy/haproxy.cfg
   global
       log /dev/log local0
       log /dev/log local1 notice
       chroot /var/lib/haproxy
       stats socket /run/haproxy/admin.sock mode 660 level admin
       stats timeout 30s
       user haproxy
       group haproxy
       daemon

   defaults
       log global
       mode tcp
       option tcplog
       option dontlognull
       timeout connect 5000
       timeout client 50000
       timeout server 50000

   frontend kubernetes
       bind 192.168.43.173:6443
       mode tcp
       default_backend kubernetes-backend

   backend kubernetes-backend
       mode tcp
       balance roundrobin
       option tcp-check
       server master1 192.168.43.165:6443 check fall 3 rise 2
       server master2 192.168.43.169:6443 check fall 3 rise 2
       server master3 192.168.43.170:6443 check fall 3 rise 2
   EOF
   ```

3. **Configure Keepalived** (`/etc/keepalived/keepalived.conf`):
   ```bash
   cat <<EOF > /etc/keepalived/keepalived.conf
   vrrp_instance VI_1 {
       state MASTER
       interface eth0  # Adjust to your interface
       virtual_router_id 51
       priority 100
       advert_int 1
       authentication {
           auth_type PASS
           auth_pass 1111
       }
       virtual_ipaddress {
           192.168.43.173
       }
   }
   EOF
   ```

4. **Enable and start services**:
   ```bash
   systemctl enable --now haproxy keepalived
   ```

*Note*: For multi-LB HA, adjust priorities for backup nodes.

## Step 3: Install Container Runtime (containerd)

On **all nodes**.

1. **Install containerd**:
   ```bash
   dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
   dnf install -y containerd.io
   ```

2. **Generate default config**:
   ```bash
   mkdir -p /etc/containerd
   containerd config default > /etc/containerd/config.toml
   ```

3. **Enable SystemdCgroup**:
   ```bash
   sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
   ```

4. **Restart and enable**:
   ```bash
   systemctl restart containerd
   systemctl enable containerd
   ```

## Step 4: Install Kubernetes Components

On **all nodes**.

1. **Add Kubernetes repo**:
   ```bash
   cat <<EOF > /etc/yum.repos.d/kubernetes.repo
   [kubernetes]
   name=Kubernetes
   baseurl=https://pkgs.k8s.io/core:/stable:/v1.30/rpm/
   enabled=1
   gpgcheck=1
   gpgkey=https://pkgs.k8s.io/core:/stable:/v1.30/rpm/repodata/repomd.xml.key
   EOF
   ```

2. **Install kubeadm, kubelet, kubectl**:
   ```bash
   dnf install -y kubelet kubeadm kubectl --disableexcludes=kubernetes
   systemctl enable --now kubelet
   ```

## Step 5: Initialize the First Master Node

On **Master1 only** (192.168.1.40).

1. **Pull images**:
   ```bash
   kubeadm config images pull --kubernetes-version=v1.30.0
   ```

2. **Initialize cluster**:
   ```bash
   kubeadm init \
     --control-plane-endpoint=vip-k8s-master \
     --upload-certs \
     --pod-network-cidr=192.168.0.0/16 \
     --kubernetes-version=v1.30.0
   ```

   - Save the `kubeadm join` commands for control-plane and worker nodes.
   - Example:
     ```bash
     kubeadm join vip-k8s-master:6443 --token abcdef.1234567890abcdef \
       --discovery-token-ca-cert-hash sha256:xxxxxxxxxx...
     ```
     And for masters:
     ```bash
     kubeadm join vip-k8s-master:6443 --token abcdef.1234567890abcdef \
       --discovery-token-ca-cert-hash sha256:xxxxxxxxxx... \
       --control-plane --certificate-key yyyyyyyyyy...
     ```

3. **Set up kubeconfig**:
   ```bash
   mkdir -p $HOME/.kube
   cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
   chown $(id -u):$(id -g) $HOME/.kube/config
   ```

## Step 6: Install Calico CNI

On **Master1**.

1. **Apply Calico manifest**:
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.3/manifests/calico.yaml
   ```

2. **Verify pods**:
   ```bash
   kubectl get pods -n calico-system
   ```

## Step 7: Join Additional Master Nodes

On **Master2 and Master3**.

1. **Run control-plane join command** (from Step 5):
   ```bash
   kubeadm join vip-k8s-master:6443 --token abcdef.1234567890abcdef \
     --discovery-token-ca-cert-hash sha256:xxxxxxxxxx... \
     --control-plane --certificate-key yyyyyyyyyy...
   ```

2. **Set up kubeconfig** (repeat Step 5.3).

3. **Verify**:
   ```bash
   kubectl get nodes
   ```

## Step 8: Join Worker Nodes

On **Worker1 and Worker2**.

1. **Run worker join command** (from Step 5):
   ```bash
   kubeadm join vip-k8s-master:6443 --token abcdef.1234567890abcdef \
     --discovery-token-ca-cert-hash sha256:xxxxxxxxxx...
   ```

2. **Verify on any master**:
   ```bash
   kubectl get nodes -o wide
   ```

## Step 9: Verification and Post-Setup

1. **Check cluster info**:
   ```bash
   kubectl cluster-info --context default
   ```

2. **Check pods**:
   ```bash
   kubectl get pods --all-namespaces
   ```

3. **Test deployment**:
   ```bash
   kubectl run nginx --image=nginx --replicas=2
   kubectl expose pod/nginx --port=80 --type=NodePort
   kubectl get svc
   ```

4. **Access via NodePort** (e.g., `curl <worker-ip>:<nodeport>`).

## Troubleshooting

- **Pods NotReady**: Check Calico logs (`kubectl logs -n calico-system <pod-name>`).
- **Join fails**: Regenerate token (`kubeadm token create --print-join-command`).
- **Reset node**: `kubeadm reset`.
- **Production**: Use external etcd, cert rotation, RBAC.

This sets up a highly available Kubernetes cluster with stacked etcd, load-balanced API, and Calico networking.
