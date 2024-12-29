sed -i s/mirror.centos.org/vault.centos.org/g /etc/yum.repos.d/CentOS-*.repo
sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/CentOS-*.repo
sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/CentOS-*.repo





# Upgrade all installed packages to the latest version available.
# 
# This command performs a system-wide upgrade of all installed packages using the DNF package manager.
# It ensures that all packages are updated to their latest versions, which may include security patches,
# bug fixes, and new features.
#
# Parameters:
# - `-y`: Automatically answer "yes" to all prompts and run non-interactively.
#
# Return Value:
# This command does not return a value. It performs an action on the system by upgrading packages.
dnf -y upgrade

# Disable SELinux enforcement.
#
# This command sets SELinux to permissive mode, which effectively disables its enforcement.
# It is often used in environments where SELinux policies interfere with application functionality.
#
# Parameters:
# This command does not take any parameters.
#
# Return Value:
# This command does not return a value. It performs an action on the system by changing the SELinux mode.
setenforce 0

# Modify SELinux configuration file to disable SELinux permanently.
#
# This command updates the SELinux configuration file to ensure that SELinux is disabled
# after a system reboot. It replaces the 'SELINUX=enforcing' line with 'SELINUX=disabled'.
#
# Parameters:
# - `-i --follow-symlinks`: Edit files in place and follow symlinks.
# - `'s/SELINUX=enforcing/SELINUX=disabled/g'`: The sed expression to perform the substitution.
# - `/etc/sysconfig/selinux`: The file to be edited.
#
# Return Value:
# This command does not return a value. It performs an action on the system by modifying a configuration file.
sed -i --follow-symlinks 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/sysconfig/selinux

modprobe br_netfilter

firewall-cmd --add-masquerade --permanent
firewall-cmd --reload

EOF
cat << /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

sysctl --system

swapoff -a

dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo

yum install containerd

dnf install docker-ce --nobest -y

systemctl start docker
systemctl enable docker

echo '{
  "exec-opts": ["native.cgroupdriver=systemd"]
}' > /etc/docker/daemon.json

systemctl restart docker

cat < /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.31/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.31/rpm/repodata/repomd.xml.key

dnf upgrade -y

dnf install -y kubelet kubeadm kubectl --disableexcludes=kubernetes

systemctl enable kubelet
systemctl start kubelet

kubeadm config images pull

firewall-cmd --zone=public --permanent --add-port={6443,2379,2380,10250,10251,10252}/tcp

firewall-cmd --zone=public --permanent --add-rich-rule 'rule family=ipv4 source address=worker-IP-address/32 accept'

firewall-cmd --zone=public --permanent --add-rich-rule 'rule family=ipv4 source address=172.17.0.0/16 accept'

firewall-cmd --reload

https://docs.tigera.io/calico/latest/getting-started/kubernetes/quickstart#overview

kubeadm init --pod-network-cidr 192.168.0.0/16

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join 192.168.16.146:6443 --token i9y52i.qzkqav9wsouv06i2 \
        --discovery-token-ca-cert-hash sha256:9346350519c09f782d1ce8a04f260853b66d78923c16bb44f3a2ba9622d9eeae
[root@kubemaster01 shaahin]#


mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml

kubectl taint nodes --all node-role.kubernetes.io/master-

kubectl get nodes

firewall-cmd --zone=public --permanent --add-port={10250,30000-32767}/tcp

firewall-cmd --reload

kubeadm join 94.237.41.193:6443 --token 4xrp9o.v345aic7zc1bj8ba 
--discovery-token-ca-cert-hash sha256:b2e459930f030787654489ba7ccbc701c29b3b60e0aa4998706fe0052de8794c

kubectl get nodes

