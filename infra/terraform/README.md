# Terraform LOGISTIA

Ce dossier crée les dix machines Debian 13 du projet LOGISTIA sur Proxmox VE 9.

## Machines créées

| VMID | Nom | IP | VLAN | RAM | Disque |
|------|-----|----|------|-----|--------|
| 101 | router-logistia | 192.168.10.151 | WAN | 2 Go | 20 Go |
| 102 | app-logistia | 10.10.10.10 | VLAN10 | 4 Go | 30 Go |
| 103 | db-logistia | 10.20.20.10 | VLAN20 | 4 Go | 40 Go |
| 104 | devops-logistia | 10.30.30.10 | VLAN30 | 4 Go | 30 Go |
| 105 | soc-logistia | 10.40.40.10 | VLAN40 | 12 Go | 60 Go |
| 106 | ia-logistia | 10.50.50.10 | VLAN50 | 12 Go | 40 Go |
| 107 | backup-logistia | 10.60.60.10 | VLAN60 | 2 Go | 100 Go |
| 108 | misp-logistia | 10.40.40.20 | VLAN40 | 8 Go | 40 Go |
| 109 | cortex-logistia | 10.40.40.30 | VLAN40 | 8 Go | 40 Go |
| 110 | thehive-logistia | 10.40.40.40 | VLAN40 | 12 Go | 50 Go |

## Prérequis Proxmox

Un template Debian 13 cloud-init doit exister avec l'ID 9000. Les bridges vmbr0 à vmbr7 doivent être créés sur Proxmox.

```bash
wget https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2 \
  -O /tmp/debian13.qcow2
virt-customize -a /tmp/debian13.qcow2 --install qemu-guest-agent
qm create 9000 --name debian13-cloudinit --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0 --ostype l26 --scsihw virtio-scsi-pci
qm importdisk 9000 /tmp/debian13.qcow2 local-lvm
qm set 9000 \
  --scsi0 local-lvm:vm-9000-disk-0 \
  --ide2 local-lvm:cloudinit \
  --boot order=scsi0 \
  --serial0 socket --vga serial0 \
  --agent enabled=1
qm template 9000
```

## Variables

```bash
cp terraform.tfvars.example terraform.tfvars
```

Renseigner `terraform.tfvars` avec les valeurs de l'environnement. Ce fichier est ignoré par Git.

## Commandes

```bash
terraform init
terraform plan -out=logistia-plan.tfplan
terraform apply logistia-plan.tfplan
```

## Cloud-init

`cloudinit/logistia-cloudinit.yaml` est uploadé sur Proxmox comme snippet lors du `terraform apply`. Il configure au premier démarrage de chaque machine l'installation des paquets de base, la création de l'utilisateur `logistia` et l'activation de SSH.

Terraform injecte uniquement la clé SSH publique. Aucun mot de passe n'est créé ni stocké.
