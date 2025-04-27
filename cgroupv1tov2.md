# Migrating from cgroup v1 to cgroup v2 on CentOS Kubernetes Cluster

---

## Step 1: Check Your System Compatibility

Ensure your CentOS version supports cgroup v2 properly:

- **CentOS 7**: Limited support for cgroup v2.
- **CentOS 8/Stream 8/9**: Recommended.

Check CentOS version:
```bash
cat /etc/centos-release
```

---

## Step 2: Check Your Current cgroup Version

```bash
mount | grep cgroup
```
OR
```bash
ls /sys/fs/cgroup
```

- Many separate directories (cpu, memory, etc.) = cgroup v1.
- Unified hierarchy = cgroup v2.

---

## Step 3: Set the System to Boot into cgroup v2

1. Edit GRUB config:
```bash
sudo vi /etc/default/grub
```

2. Modify `GRUB_CMDLINE_LINUX` to add:
```
systemd.unified_cgroup_hierarchy=1
```

Example:
```bash
GRUB_CMDLINE_LINUX="... other options ... systemd.unified_cgroup_hierarchy=1"
```

3. Regenerate GRUB:
- BIOS systems:
  ```bash
  sudo grub2-mkconfig -o /boot/grub2/grub.cfg
  ```
- UEFI systems:
  ```bash
  sudo grub2-mkconfig -o /boot/efi/EFI/centos/grub.cfg
  ```

4. Reboot:
```bash
sudo reboot
```

---

## Step 4: Verify cgroup v2 is Active

Check:
```bash
mount | grep cgroup
```

Or:
```bash
cat /proc/cgroups
```

Or:
```bash
cat /proc/self/mountinfo | grep cgroup
```

You should see:
```
0::/sys/fs/cgroup
```

---

## Step 5: Adjust Kubernetes Components

### Kubelet:
Edit `/var/lib/kubelet/config.yaml` or kubelet startup parameters:
```yaml
cgroupDriver: systemd
```

Or, for systemd service (`/etc/systemd/system/kubelet.service.d/10-kubeadm.conf`):
```bash
--cgroup-driver=systemd
```

Restart kubelet:
```bash
sudo systemctl daemon-reexec
sudo systemctl restart kubelet
```

---

## Step 6: Update Container Runtime

### For containerd:

Edit config:
```bash
sudo vi /etc/containerd/config.toml
```

Set:
```toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true
```

Restart containerd:
```bash
sudo systemctl restart containerd
```

For CRI-O or Docker, similar adjustments needed.

---

## Step 7: Verify Everything is Healthy

- Kubelet logs:
```bash
sudo journalctl -u kubelet
```

- Node status:
```bash
kubectl get nodes
```

- Pods:
```bash
kubectl get pods -A
```

---

## Quick Summary

| Step | Task |
|:----:|:-----|
| 1 | Confirm CentOS version |
| 2 | Modify GRUB for `systemd.unified_cgroup_hierarchy=1` |
| 3 | Regenerate GRUB and reboot |
| 4 | Verify cgroup v2 |
| 5 | Adjust kubelet to `systemd` driver |
| 6 | Adjust container runtime (SystemdCgroup=true) |
| 7 | Restart and verify Kubernetes cluster |

---

Would you like an example full config file too? 🚀

